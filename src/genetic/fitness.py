from functools import cache

from ..transform import NodeMap
from ..utils import divide
from ..execution import Tester

class Fitness:
    @staticmethod
    @cache
    def run(w_code:str, r_code:str) -> dict:
        w_code = w_code
        w_test_hist, _, w_trace_hist = Tester.trace(w_code)
        w_pass, w_fail = Tester.split_test_hist(w_test_hist)
        
        r_test_hist, _, r_trace_hist = Tester.trace(r_code)
        r_pass, r_fail = Tester.split_test_hist(r_test_hist)
        
        # Unit Test Score
        fp = set(w_fail) & set(r_pass)
        pp = set(w_pass) & set(r_pass)
        fp_test = divide(len(fp), len(w_fail))
        pp_test = divide(len(pp), len(w_pass))
        
        # Execution Trace Score
        fp_trace, pp_trace = 0, 0
        nodeMap = NodeMap(w_code, r_code)
        for testcase in Tester.testsuite:
            if testcase.no not in fp and testcase.no not in pp:
                continue
            trace_sim = nodeMap.trace_sim(
                w_trace_hist[testcase.no], 
                r_trace_hist[testcase.no])
            if testcase.no in fp: fp_trace += trace_sim
            elif testcase.no in pp: pp_trace += trace_sim
        fp_trace = divide(fp_trace, len(fp))
        pp_trace = divide(pp_trace, len(pp))

        # Fitness Score
        score = {'fp_test': fp_test, 'pp_test': pp_test, 
                 'fp_trace': fp_trace, 'pp_trace': pp_trace}
        return score
    