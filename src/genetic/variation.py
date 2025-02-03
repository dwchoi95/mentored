import ast

from .fixHistory import FixHistory

from ..transform import VariableMap, SWTVariables, NodeMap, Fixer
from ..utils import Regularize, Log


class Variation:
    def __init__(self, log:Log, fixHistory:FixHistory=FixHistory()):
        self.log = log
        self.fixHistory = fixHistory
        
        
    def _swt_variables(self, 
                       testcases:list, 
                       w_vari_hist:dict, 
                       r_vari_hist:dict) -> dict:
        # Variables variants
        var_map = VariableMap(testcases).run(self.wrong_tree, 
                                         w_vari_hist, 
                                         self.refer_tree, 
                                         r_vari_hist)
        self.refer_tree = SWTVariables(var_map).visit(self.refer_tree)
        self.log.update({'varmap':var_map})
        return var_map
    
    
    def _fault_localization(self, 
                            w_test_hist:dict, 
                            w_vari_hist:dict, 
                            w_trace_hist:dict, 
                            r_test_hist:dict, 
                            r_vari_hist:dict, 
                            r_trace_hist:dict,
                            var_map:dict) -> dict:
        # FaultLocalization
        from ..execution import FaultLocalization
        fl = FaultLocalization()
        suspiciousness = fl.vsusfl(w_test_hist, 
                                   w_vari_hist, 
                                   w_trace_hist, 
                                   r_test_hist, 
                                   r_vari_hist, 
                                   r_trace_hist, 
                                   var_map)
        self.log.update({'suspiciousness':str(suspiciousness)})
        return suspiciousness
    
    
    def _patch_generation(self, 
                          w_trace_hist:dict, 
                          r_trace_hist:dict, 
                          suspiciousness:dict) -> str:
        # Patch Generation
        child = self.wrong_code
        
        ## Execution Trace Mapping with AST Node
        nodeMap = NodeMap(self.wrong_tree, self.refer_tree)
        rep_node_map, ins_node_map, del_node_map = \
            nodeMap.run(w_trace_hist, r_trace_hist)
        
        ## Find a new repair pattern which not used in previous
        while rep_node_map or ins_node_map or del_node_map:
            cut_node_map = nodeMap.cut_node_map(rep_node_map)
            mut_node_map = nodeMap.mut_node_map(rep_node_map, 
                                                ins_node_map, 
                                                del_node_map,
                                                suspiciousness)
            
            self.log.update({'crossover':self.__node_map_2_str(cut_node_map)})
            self.log.update({'mutation':self.__node_map_2_str(mut_node_map)})
            
            ## Fix
            fix_node_map = cut_node_map | mut_node_map
            if not fix_node_map: break
            child = Fixer(fix_node_map).run(self.wrong_code)

            if self.fixHistory.is_fixed(self.wrong_code, child):
                fix_node_map = cut_node_map | mut_node_map
                for a_node, actions in fix_node_map.items():
                    if a_node.lineno in suspiciousness.keys():
                        del suspiciousness[a_node.lineno]
                    for action in actions.keys():
                        if action == 'del':
                            if a_node in del_node_map.keys():
                                del del_node_map[a_node]
                        elif action == 'ins':
                            if a_node in ins_node_map.keys():
                                del ins_node_map[a_node]
                        else:
                            if a_node in rep_node_map.keys():
                                del rep_node_map[a_node]
            else:
                self.fixHistory.add_fixed_location(self.wrong_code, child)
                break
        
        return Regularize.run(child)
    
    
    def __node_map_2_str(self, node_map:dict) -> str:
        return str([(act, n1.lineno,(n2[0].lineno,n2[1]) 
                     if act=='ins' else n2.lineno if n2 else None) 
            for n1, actions in node_map.items()
            for act, n2 in actions.items()])
        

    def run(self, wrong_code:str, refer_code:str) -> str:
        from ..execution import Tester
        
        self.wrong_code, self.refer_code = wrong_code, refer_code
        self.wrong_tree, self.refer_tree = ast.parse(wrong_code), ast.parse(refer_code)
        w_test_hist, w_vari_hist, w_trace_hist = Tester.trace(wrong_code)
        r_test_hist, r_vari_hist, r_trace_hist = Tester.trace(refer_code)
        self.log.update({
            'w_test_hist':str(w_test_hist),
            'r_test_hist':str(r_test_hist)
        })
        self.log.update({
            'w_vari_hist':str(w_vari_hist),
            'r_vari_hist':str(r_vari_hist)
        })
        self.log.update({
            'w_trace_hist':str(w_trace_hist),
            'r_trace_hist':str(r_trace_hist)
        })
        
        # Use only information of failed testcases for Repair
        passed, failed = Tester.split_test_hist(w_test_hist)
        w_test_hist = w_test_hist.copy()
        w_vari_hist = w_vari_hist.copy()
        w_trace_hist = w_trace_hist.copy()
        r_test_hist = r_test_hist.copy()
        r_vari_hist = r_vari_hist.copy()
        r_trace_hist = r_trace_hist.copy()
        for tc in passed:
            del w_test_hist[tc]
            del w_vari_hist[tc]
            del w_trace_hist[tc]
            del r_test_hist[tc]
            del r_vari_hist[tc]
            del r_trace_hist[tc]
        
        # Variables variants
        var_map = self._swt_variables(failed, 
                                      w_vari_hist, 
                                      r_vari_hist)
        
        # FaultLocalization
        suspiciousness = self._fault_localization(w_test_hist, 
                                                w_vari_hist, 
                                                w_trace_hist, 
                                                r_test_hist, 
                                                r_vari_hist, 
                                                r_trace_hist,
                                                var_map)

        # Patch Generation
        child = self._patch_generation(w_trace_hist, 
                                       r_trace_hist,
                                       suspiciousness)

        return child