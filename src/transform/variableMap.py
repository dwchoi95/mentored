from collections import Counter

from .nodeParser import NodeParser
from ..utils import Randoms

class VariableMap:
    def __init__(self, tc_id_list:list=[]):
        self.var_map = {}
        self.tc_id_list = tc_id_list
        self.non_used_a_var_list = []

    def __check_mapped(self, b_var, a_var):
        if b_var not in self.var_map.keys() and a_var not in self.var_map.values():
            return True
        return False
    
    def update(self, a_tree, a_var_hist:dict, b_tree, b_var_hist:dict):
        np_a = NodeParser()
        np_a.run(tree=a_tree)
        self.a_var_name_list = np_a.var_name_list
        np_b = NodeParser()
        np_b.run(tree=b_tree)
        self.b_var_name_list = np_b.var_name_list

        self.a_var_hist = a_var_hist
        self.b_var_hist = b_var_hist
    
    def get_var_value_sequence(self, vvs:list):
        return [v[0] for v in vvs]

    def get_most_matched_var_map(self, var_map_list):
        # Count the occurrences of each a_vars for each b_var
        a_var_counter = {}
        for var_map in var_map_list:
            for b_var, a_var in var_map.items():
                if b_var not in a_var_counter:
                    a_var_counter[b_var] = Counter()
                a_var_counter[b_var][a_var] += 1

        # Create a new dictionary with the most common a_vars for each b_var
        for b_var, counter in a_var_counter.items():
            most_common_a_vars = counter.most_common()
            max_count = most_common_a_vars[0][1]
            most_common_a_vars = [val for val, count in most_common_a_vars if count == max_count]
            chosen_a_var = Randoms.choice(most_common_a_vars)
            if self.__check_mapped(b_var, chosen_a_var):
                self.var_map[b_var] = chosen_a_var

    def dea_var_map(self):
        # Map variables based on dynamic equivalence analysis
        var_map_list = []
        for b_var in self.b_var_name_list:
            for a_var in self.a_var_name_list:
                is_matched = False
                for tc_id in self.tc_id_list:
                    if b_var not in self.b_var_hist[tc_id] or a_var not in self.a_var_hist[tc_id]:
                        continue
                    b_var_values = self.get_var_value_sequence(self.b_var_hist[tc_id][b_var])
                    a_var_values = self.get_var_value_sequence(self.a_var_hist[tc_id][a_var])
                    if self.__is_hist_equal(b_var_values, a_var_values):
                        is_matched = True
                        break
                if is_matched:
                    var_map_list.append({b_var:a_var})
        self.get_most_matched_var_map(var_map_list)
        return self.var_map
    
    def __is_hist_equal(self, hist_a, hist_b):
        if len(hist_a) != len(hist_b):
            return False
        for i in range(len(hist_a)):
            if not self.__is_equal(hist_a[i], hist_b[i]):
                return False
        return True

    def __is_equal(self, object_a, object_b):
        if str(type(object_a)) == str(type(object_b)):
            if object_a == object_b:
                return True
            else:
                return False
        else:
            close_type_list = ["<class 'list'>", "<class 'tuple'>"]
            if str(type(object_a)) in close_type_list and \
                    str(type(object_b)) in close_type_list:
                if list(object_a) == list(object_b):
                    return True
                else:
                    return False
            else:
                return False
            

    def lcs_var_map(self) -> dict:
        # Map variables based on longest common subsequence
        for tc_id in self.tc_id_list:
            a_var_values_dict = self.a_var_hist[tc_id]
            b_var_values_dict = self.b_var_hist[tc_id]

            for b_var, b_data in b_var_values_dict.items():
                b_values = self.get_var_value_sequence(b_data)
                cand_var = {}
                for a_var, a_data in a_var_values_dict.items():
                    a_values = self.get_var_value_sequence(a_data)
                    lcs = self.lcs(b_values, a_values)
                    cand_var.setdefault(lcs, []).append(a_var)

                if cand_var:
                    max_lcs = max(list(cand_var.keys()))
                    a_var = Randoms.choice(cand_var[max_lcs])
                    if self.__check_mapped(b_var, a_var):
                        self.var_map[b_var] = a_var

        return self.var_map
    
    def lcs(self, lst1, lst2):
        # Get the lengths of both input lists
        m, n = len(lst1), len(lst2)
        # Initialize a 2D table 'jh' to store the lengths of common subsequences
        jh = [[0 for j in range(n+1)] for i in range(m+1)]

        # Fill in the 'jh' table using dynamic programming
        for i in range(1, m+1):
            for j in range(1, n+1):
                if lst1[i-1] == lst2[j-1]:
                    jh[i][j] = 1 + jh[i-1][j-1]
                else:
                    jh[i][j] = max(jh[i-1][j], jh[i][j-1])

        # Initialize a result list to store the common subsequence
        result = []
        i, j = m, n

        # Reconstruct the longest common subsequence
        while i > 0 and j > 0:
            if lst1[i-1] == lst2[j-1]:
                result.append(lst1[i-1])
                i -= 1
                j -= 1
            elif jh[i-1][j] > jh[i][j-1]:
                i -= 1
            else:
                j -= 1

        # Return the result list in reverse order to get the correct sequence
        return len(result[::-1])
    

    def type_var_map(self):
        # Map variables with same type
        a_var_type_dict = self.__get_var_type_dict(self.a_var_hist)
        b_var_type_dict = self.__get_var_type_dict(self.b_var_hist)

        for b_var, b_type in b_var_type_dict.items():
            for a_var, a_type in a_var_type_dict.items():
                if self.__check_mapped(b_var, a_var) and b_type == a_type:
                    self.var_map[b_var] = a_var
        return self.var_map
    
    def __get_var_type_dict(self, vari_hist:dict) -> dict:
        var_type_dict = {}
        for var_dict in vari_hist.values():
            for var, data in var_dict.items():
                values = self.get_var_value_sequence(data)
                if var in var_type_dict.keys(): continue
                for v in values:
                    try: v = eval(v)
                    except: pass
                    var_type_dict.setdefault(var, set()).add(type(v).__name__)
                    break
        return var_type_dict
    

    def residue_var_map(self):
        # Using same name str to map variables
        for b_var in self.b_var_name_list:
            for a_var in self.a_var_name_list:
                if self.__check_mapped(b_var, a_var) and b_var == a_var:
                    self.var_map[b_var] = a_var

        # New variables
        for a_var in self.a_var_name_list:
            if self.__check_mapped(a_var, a_var):
                self.var_map[a_var] = a_var
            elif a_var in self.var_map.keys():
                value = self.var_map[a_var]
                key = value
                for k,v in self.var_map.items():
                    if v==a_var:
                        key = k
                        break
                self.var_map[a_var], self.var_map[key] = a_var, value

        for b_var in self.b_var_name_list:
            if self.__check_mapped(b_var, b_var):
                self.var_map[b_var] = b_var
            elif b_var in self.var_map.values():
                key = [k for k,v in self.var_map.items() if v==b_var][0]
                self.var_map[b_var], self.var_map[key] = b_var, key

    def run(self, a_tree, a_vvs:dict, b_tree, b_vvs:dict) -> dict:
        self.update(a_tree, a_vvs, b_tree, b_vvs)

        self.dea_var_map()
        self.lcs_var_map()
        self.type_var_map()
        self.residue_var_map()
        return self.var_map
    