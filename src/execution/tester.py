from functools import cache
import warnings
warnings.filterwarnings("ignore")

from .results import Results
from .testsuite import TestSuite
from .unittests import Running, Tracing, RunUnitTest, UnitTestStatus

from ..transform import NodeParser, ExceptHandler


class Tester:
    testsuite = None
    timeout = 1
    
    @classmethod
    def clear(cls):
        cls.trace.cache_clear()
        cls.validation.cache_clear()
        
    @classmethod
    def init_global_data(cls, testcases:list, timeout:int=1):
        cls.testsuite = TestSuite(testcases)
        cls.timeout = timeout
        cls.clear()
    
    @classmethod
    def split_test_hist(cls, test_hist:dict) -> list:
        passed_tc_list = [tc_id for tc_id, result in test_hist.items() if result == UnitTestStatus.success]
        failed_tc_list = [tc_id for tc_id, result in test_hist.items() if result != UnitTestStatus.success]
        return passed_tc_list, failed_tc_list
    
    @classmethod
    def is_all_error(cls, test_hist:dict) -> bool:
        return all(result == UnitTestStatus.error for result in test_hist.values())
    
    @classmethod
    def is_all_fail(cls, test_hist:dict) -> bool:
        return all(result != UnitTestStatus.success for result in test_hist.values())
    
    @classmethod
    def is_all_pass(cls, test_hist:dict) -> bool:
        return all(result == UnitTestStatus.success for result in test_hist.values())
    
    @classmethod
    def is_pass(cls, status:str) -> bool:
        return status == UnitTestStatus.success
    
    @classmethod
    def pass_cnt(cls, test_hist:dict) -> int:
        return sum(result == UnitTestStatus.success for result in test_hist.values())
    
    @classmethod
    def get_tc_no_list(cls) -> list:
        return cls.testsuite.get_tc_no_list()
    
    @classmethod
    def print_wrong_tc(cls, test_hist:dict):
        prints = []
        for tc_no, result in test_hist.items():
            if result != UnitTestStatus.success:
                prints.append(cls.print_testcase(tc_no))
        return "\n\n".join(prints)
    
    @classmethod
    def print_testcase(cls, idx:int) -> str:
        return cls.testsuite.print_testcase(idx)
    
    @classmethod
    def gen_test_code(cls, code:str, input:str, key_input:bool=False) -> str:
        from ..utils import Regularize
        try:
            test_input = input
            if 'print(' not in input:
                test_input = 'print(' + input + ')'
            Regularize.run(input)
            Regularize.run(test_input)
        except:
            key_input = True

        test_code = code.strip()
        if not key_input:
            if 'print(' not in input:
                input = 'print(' + input + ')'
            test_code = code + '\n\n' + input

        return Regularize.run(test_code)
    
    @classmethod
    def __fix_exec_traces(cls, node_parser:NodeParser, test_code:str):
        # Set execution traces to before error line when it has compile error
        if Results.status == UnitTestStatus.error:
            if Results.exec_traces:
                pass
            else:
                for lineno in node_parser.line_node_map.keys():
                    Results.exec_traces.append(lineno)
                Results.exec_traces.sort()
        else:
            node_parser = NodeParser()
            node_parser.run(test_code)
            new_exec_traces = []
            for lineno in Results.exec_traces:
                if lineno in node_parser.object_line_node_dict.keys(): continue
                if lineno <= Results.end_line:
                    new_exec_traces.append(lineno)
                if lineno in node_parser.objectCall_line_dict.keys():
                    new_exec_traces.append(node_parser.objectCall_line_dict[lineno])
            Results.exec_traces = new_exec_traces
                    
    @classmethod
    def __fix_vari_values(cls):
        for var, vvs_set in Results.vari_traces.items():
            new_vvs = []
            for (value, lineno) in vvs_set:
                try: value = eval(value)
                except: pass
                new_vvs.append((value, lineno))
            Results.vari_traces[var] = new_vvs
    
    @classmethod
    def run(cls, code:str, input:str, output:str, UnitTest=Running) -> tuple[str, str]:
        from ..utils import Regularize
        
        code = Regularize.run(code)
        Results.init_global_vars()
        np = NodeParser()
        np.run(code)
        test_code = cls.gen_test_code(code, input, np.key_input)
        eh = ExceptHandler()
        handle_code = eh.run(test_code)
        Results.changed_line_map = eh.new_line_map
        Results.vari_names = np.var_name_list
        Results.line_vars_map = np.line_vars_map
        Results.timeout = cls.timeout
        Results.input = input
        Results.output = output
        Results.test_code = handle_code
        Results.end_line = len(code.splitlines())

        # Unittest
        rut = RunUnitTest()
        rut.run(UnitTest)
        
        # Only use in Tracing
        if UnitTest == Tracing:
            cls.__fix_exec_traces(np, test_code)
            cls.__fix_vari_values()
                
        return Results.status, Results.stdout


    @classmethod
    @cache
    def validation(cls, code:str) -> dict[int, str]:
        test_hist = {}

        for testcase in cls.testsuite:
            cls.run(code, testcase.input, testcase.output)
            test_hist[testcase.no] = Results.status
        
        return test_hist

    @classmethod
    @cache
    def trace(cls, code:str) -> tuple[dict[int, str], dict[int, dict], dict[int, list]]:
        test_hist = {}
        vari_hist = {}
        trace_hist = {}

        for testcase in cls.testsuite:
            cls.run(code, testcase.input, testcase.output, Tracing)
            test_hist[testcase.no] = Results.status
            vari_hist[testcase.no] = Results.vari_traces
            trace_hist[testcase.no] = Results.exec_traces
        
        return test_hist, vari_hist, trace_hist
    
