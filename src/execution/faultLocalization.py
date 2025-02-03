from sklearn.preprocessing import MinMaxScaler

from .tester import Tester

class FaultLocalization:
    def get_nth_fl(self, suspiciousness:dict, n:int=1):
        rankings = dict(sorted(suspiciousness.items(), key=lambda x:x[1], reverse=True))
        return list(rankings.keys())[n-1]
    
    def get_fl_over_nscore(self, suspiciousness:dict, n:int=0):
        fl_list = [lineno for lineno, score in suspiciousness.items() if score > n]
        return fl_list
    
    def get_fl_below_nscore(self, suspiciousness:dict, n:int=0):
        fl_list = [lineno for lineno, score in suspiciousness.items() if score <= n]
        return fl_list

    def trantula(self, test_hist:dict, trace_hist:dict) -> dict:
        total_pass = 0
        total_fail = 0
        pass_cnt_dict = {}
        fail_cnt_dict = {}
        lines = set()

        for no, status in test_hist.items():
            for lineno in set(trace_hist[no]):
                lines.add(lineno)
                if not Tester.is_pass(status):
                    total_fail += 1
                    fail_cnt_dict.setdefault(lineno, 0)
                    fail_cnt_dict[lineno] += 1
                else:
                    total_pass += 1
                    pass_cnt_dict.setdefault(lineno, 0)
                    pass_cnt_dict[lineno] += 1
        
        suspiciousness = {}
        for lineno in lines:
            pass_cnt = pass_cnt_dict[lineno] if lineno in pass_cnt_dict.keys() else 0
            fail_cnt = fail_cnt_dict[lineno] if lineno in fail_cnt_dict.keys() else 0
            score = 0
            try: score = round((fail_cnt / total_fail) / ((fail_cnt / total_fail) + (pass_cnt / total_pass)), 1)
            except ZeroDivisionError:
                if fail_cnt > 0 and pass_cnt == 0:
                    score = 1
            suspiciousness[lineno] = score
        
        return suspiciousness
    
    def jaccard(self, test_hist:dict, trace_hist:dict) -> dict:
        total_fail = 0
        exec_cnt_dict = {}
        fail_cnt_dict = {}
        lines = set()

        for no, status in test_hist.items():
            if not Tester.is_pass(status):
                total_fail += 1
            for lineno in set(trace_hist[no]):
                lines.add(lineno)
                exec_cnt_dict.setdefault(lineno, 0)
                exec_cnt_dict[lineno] += 1
                if not Tester.is_pass(status):
                    fail_cnt_dict.setdefault(lineno, 0)
                    fail_cnt_dict[lineno] += 1
        
        suspiciousness = {}
        for lineno in lines:
            exec_cnt = exec_cnt_dict[lineno] if lineno in exec_cnt_dict.keys() else 0
            fail_cnt = fail_cnt_dict[lineno] if lineno in fail_cnt_dict.keys() else 0
            score = 0
            try: score = round((fail_cnt / (exec_cnt + (total_fail - fail_cnt))), 1)
            except ZeroDivisionError:
                if fail_cnt > 0 and exec_cnt == 0:
                    score = 1
            suspiciousness[lineno] = score
        
        return suspiciousness
    
    
    def vsusfl(self, test_hist1:dict, vari_hist1:dict, trace_hist1:dict, 
               test_hist2:dict, vari_hist2:dict, trace_hist2:dict, var_map:dict) -> dict:
        
        suspiciousness = {}
        var_map = {v:k for k, v in var_map.items()}
        for tc_id, status1 in test_hist1.items():
            
            status2 = test_hist2[tc_id]
            traces1 = trace_hist1[tc_id]

            vvs1 = vari_hist1[tc_id]
            vvs1_line_var_map = {}
            for var, values in vvs1.items():
                for data in values:
                    lineno = data[1]
                    vvs1_line_var_map.setdefault(lineno, set())
                    vvs1_line_var_map[lineno].add(var)

            vvs2 = vari_hist2[tc_id]
            vvs2_line_var_map = {}
            for var2, values in vvs2.items():
                for data in values:
                    lineno2 = data[1]
                    vvs2_line_var_map.setdefault(lineno2, {})
                    vvs2_line_var_map[lineno2].setdefault(var2, []).append(data[0])
            
            for lineno in traces1:
                suspiciousness.setdefault(lineno, 0)
                if lineno not in vvs1_line_var_map.keys(): continue
                for var1 in vvs1_line_var_map[lineno]:
                    if var1 not in var_map.keys() or var1 not in vvs1.keys():
                        if not Tester.is_pass(status1):
                            suspiciousness[lineno] += 9
                        continue
                    
                    found = False
                    var2 = var_map[var1]
                    if var2 not in vvs2.keys(): continue
                    values1 = [item[0] for item in vvs1[var1] if item[1] == lineno]
                    for lineno2, var_value_dict2 in vvs2_line_var_map.items():
                        if var2 not in var_value_dict2.keys(): continue
                        values2 = var_value_dict2[var2]
                        if values1 == values2:
                            del vvs2_line_var_map[lineno2][var2]
                            found = True
                            break
                    
                    if found:
                        if Tester.is_pass(status1) and Tester.is_pass(status2):
                            suspiciousness[lineno] += 1
                    else:
                        if not Tester.is_pass(status1) and Tester.is_pass(status2):
                            suspiciousness[lineno] += 9
        
        # suspiciousness = {lineno:susp for lineno, susp in suspiciousness.items() if susp >= 0}
        # print(suspiciousness)

        if suspiciousness:
            scaler = MinMaxScaler((0.3, 1.0))
            scaler.fit([[value] for value in suspiciousness.values()])
            suspiciousness = {key: float(scaled_value[0]) 
                              for key, scaled_value in 
                              zip(suspiciousness.keys(), 
                                  scaler.transform([[value] 
                                    for value in suspiciousness.values()]))}
        return suspiciousness


    def run_core(self, test_hist:dict, trace_hist:dict, formula:str="jaccard") -> dict:
        if formula == "trantula":
            suspiciousness = self.trantula(test_hist, trace_hist)
        elif formula == "jaccard":
            suspiciousness = self.jaccard(test_hist, trace_hist)
        return suspiciousness
    
    def run(self, code:str, formula:str="jaccard") -> dict:
        test_hist, _, trace_hist = Tester.trace(code)
        suspiciousness = self.run_core(test_hist, trace_hist, formula)
        return suspiciousness