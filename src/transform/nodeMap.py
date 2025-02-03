import ast
from collections import Counter

from .nodeParser import NodeParser
from ..utils import Randoms, TED, divide

class NodeMap:

    def __init__(self, a_tree:ast, b_tree:ast):
        a_tree = ast.parse(a_tree) if type(a_tree) == str else a_tree
        b_tree = ast.parse(b_tree) if type(b_tree) == str else b_tree
        self.a_np:NodeParser = self.__make_node_parser(a_tree)
        self.b_np:NodeParser = self.__make_node_parser(b_tree)


    def __make_node_parser(self, tree:ast) -> NodeParser:
        np = NodeParser()
        np.run(tree=tree)
        return np
    
    def __get_trace_node_map(self, node_parser:NodeParser, traces:list) -> dict:
        line_node_map = node_parser.line_node_map
        trace_node_map = {line_node_map[lineno]:line_node_map[lineno].__class__.__name__ 
                            for lineno in traces
                            if lineno in line_node_map.keys()}
        return trace_node_map

    def merge_node_map(self, node_map_list):
        # Count the occurrences of each b_nodes for each a_node
        b_node_counter = {}
        for node_map in node_map_list:
            for a_node, b_node in node_map.items():
                if a_node not in b_node_counter:
                    b_node_counter[a_node] = Counter()
                b_node_counter[a_node][b_node] += 1

        # Create a new dictionary with the most common b_nodes for each a_node
        mearge_node_map = {}
        for a_node, counter in b_node_counter.items():
            most_common_b_nodes = counter.most_common()
            max_count = most_common_b_nodes[0][1]
            most_common_b_nodes = [val for val, count in most_common_b_nodes if count == max_count]
            chosen_b_node = Randoms.choice(most_common_b_nodes)
            mearge_node_map[a_node] = chosen_b_node

        return mearge_node_map

    def rep_node_map(self, a_trace_node_map:dict, b_trace_node_map:dict) -> dict:
        rep_node_map = {}
        a_nodes = []
        a_node_names = []
        for k, v in reversed(list(a_trace_node_map.items())):
            a_nodes.append(k)
            a_node_names.append(v)
        
        b_nodes = []
        b_node_names = []
        for k, v in reversed(list(b_trace_node_map.items())):
            b_nodes.append(k)
            b_node_names.append(v)
        
        # Initialize a 2D array to store the lengths of LCS
        dp = [[0] * (len(b_node_names) + 1) for _ in range(len(a_node_names) + 1)]

        # Calculate the dp array
        for i in range(1, len(a_node_names) + 1):
            for j in range(1, len(b_node_names) + 1):
                if a_node_names[i - 1] == b_node_names[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # Node mapping with LCS
        # Crossover: rep Node Mapping
        i, j = len(a_node_names), len(b_node_names)
        while i > 0 and j > 0:
            if a_node_names[i - 1] == b_node_names[j - 1]:
                a_node = a_nodes[i - 1]
                b_node = b_nodes[j - 1]
                rep_node_map[a_node] = b_node
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
    
        return rep_node_map
    
    def ins_node_map(self, node_map:dict, b_trace_node_map:dict) -> dict:
        ins_node_map = {}
        b_node_list = list(b_trace_node_map.keys())
        b_traces = []
        for i, b_node in enumerate(b_node_list):
            b_traces.append(b_node.lineno)
            ### Skip if it already mapped
            if b_node in node_map.values(): continue
            for _ in range(i, 0, -1):
                before_b_node = b_node_list[i-1]
                ### Find before_b_node's mapped a_node
                a_node, loc = self.__find_ins_loc(b_node, before_b_node, node_map)
                if a_node is not None:
                    ### Inserts b_node before a_node 
                    ### in the next sequence of mapped before_a_node
                    ins_node_map.setdefault(a_node, []).append((b_node, loc))
                    # if a_node not in ins_node_map.keys():
                    #     ins_node_map[a_node] = (b_node, loc)
        ins_node_map = {a_node:Randoms.choice(candidates) for a_node, candidates in ins_node_map.items()}
        return ins_node_map
    
    def __find_ins_loc(self, b_node, before_b_node, node_map):
        loc = None
        for mapped_a_node, mapped_b_node in node_map.items():
            if before_b_node == mapped_b_node:
                loc = 'sibling'
                for child in ast.walk(before_b_node):
                    if child == b_node:
                        loc = 'child'
                        break
                return mapped_a_node, loc
        return None, loc
    
    def del_node_map(self, a_trace_node_map:dict) -> dict:
        del_node_map = {}
        a_node_list = list(a_trace_node_map.keys())
        for a_node in a_node_list:
            if not isinstance(a_node, ast.FunctionDef):
                del_node_map[a_node] = None
        return del_node_map
    

    def rolette_wheel(self, suspiciousness:dict) -> int:
        total_suspiciousness = sum(suspiciousness.values())
        pick = Randoms.uniform(0, total_suspiciousness)
        
        current = 0
        for lineno, suspiciousness in suspiciousness.items():
            current += suspiciousness
            if current > pick:
                break
        return lineno
    

    def cut_node_map(self, node_map:dict) -> dict:
        cut_node_map = {}
        # node_map = {k:v for k, v in node_map.items() if not isinstance(k, ast.FunctionDef)}
        if node_map:
            a_node, b_node = Randoms.choice(list(node_map.items()))
            cut_node_map[a_node] = {'cut':b_node}
        return cut_node_map
    
    def mut_node_map(self, rep_node_map:dict, ins_node_map:dict, del_node_map:dict, suspiciousness:dict) -> dict:
        mut_node_map = {}
        while suspiciousness:
            candidate = []
            lineno = self.rolette_wheel(suspiciousness)
            if lineno in self.a_np.line_node_map.keys():
                a_node = self.a_np.line_node_map[lineno]
                if a_node in rep_node_map.keys():
                    candidate.append({'rep':rep_node_map[a_node]})
                if a_node in ins_node_map.keys():
                    candidate.append({'ins':ins_node_map[a_node]})
                if a_node in del_node_map.keys():
                    candidate.append({'del':del_node_map[a_node]})
                if candidate:
                    mut_node_map[a_node] = Randoms.choice(candidate)
                    break
            del suspiciousness[lineno]
        return mut_node_map
    
    def run(self, a_trace_hist:dict, b_trace_hist:dict) -> dict:
        rep_node_map_list = []
        ins_node_map_list = []
        del_node_map_list = []
        for tc_no in a_trace_hist.keys():
            a_trace_node_map = self.__get_trace_node_map(self.a_np, a_trace_hist[tc_no])
            b_trace_node_map = self.__get_trace_node_map(self.b_np, b_trace_hist[tc_no])
            rep_node_map = self.rep_node_map(a_trace_node_map, b_trace_node_map)
            rep_node_map_list.append(rep_node_map)
            ins_node_map_list.append(self.ins_node_map(rep_node_map, b_trace_node_map))
            del_node_map_list.append(self.del_node_map(a_trace_node_map))
        
        rep_node_map = self.merge_node_map(rep_node_map_list)
        ins_node_map = self.merge_node_map(ins_node_map_list)
        del_node_map = self.merge_node_map(del_node_map_list)
        
        return rep_node_map, ins_node_map, del_node_map
    

    def trace_sim(self, a_trace:list, b_trace:list):
        rep_node_map = self.rep_node_map(
            self.__get_trace_node_map(self.a_np, a_trace), 
            self.__get_trace_node_map(self.b_np, b_trace))
        return divide(len(rep_node_map), max(len(a_trace), len(b_trace)))
        trace_sim = 0
        for a_node, b_node in rep_node_map.items():
            if isinstance(a_node, (ast.Try, ast.TryStar)):
                trace_sim += 1
                continue
            a_stmt = ast.unparse(a_node).split('\n')[0].strip()
            if a_stmt.endswith(":"): a_stmt += "\n    pass"
            b_stmt = ast.unparse(b_node).split('\n')[0].strip()
            if b_stmt.endswith(":"): b_stmt += "\n    pass"
            trace_sim += TED.compute_sim(a_stmt, b_stmt)
        trace_sim = divide(trace_sim, max(len(a_trace), len(b_trace)))
        return trace_sim
