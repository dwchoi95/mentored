import ast
import copy


class Fixer(ast.NodeTransformer):
    def __init__(self, node_map:dict):
        self.node_map = node_map
        self.parent_map = {}
    
    def __get_child_loc(self, parent, child):
        idx = -1
        loc = None
        if hasattr(parent, 'body') and \
            child in parent.body:
            idx = parent.body.index(child)
            loc = "body"
        elif hasattr(parent, 'handlers') and \
            child in parent.handlers:
            idx = parent.handlers.index(child)
            loc = "handlers"
        elif hasattr(parent, 'orelse') and \
            child in parent.orelse:
            idx = parent.orelse.index(child)
            loc = "orelse"
        elif hasattr(parent, 'finalbody') and \
            child in parent.finalbody:
            idx = parent.finalbody.index(child)
            loc = "finalbody"
        return idx, loc
    
    def __get_node_from_parent(self, parent, idx, loc):
        try:
            if loc == "body":
                node = parent.body[idx]
            elif loc == "handlers":
                node = parent.handlers[idx]
            elif loc == "orelse":
                node = parent.orelse[idx]
            elif loc == "finalbody":
                node = parent.finalbody[idx]
        except:
            node = ast.Pass()
        return node
    

    def del_nodes(self, node):
        # delete_node의 parent를 찾음
        parent = self.parent_map[node]
        # parent의 childs 중 delete_node가
        # loc(body, orelse, finalbody) 중 idx(몇번째)에 있는지 확인
        idx, loc = self.__get_child_loc(parent, node)
        # parent에서 delete_node를 삭제
        parent = self._del_node(parent, idx, loc)
        # delete_node의 childs를 찾아서 delete_node의 parent에 붙여줌
        childs = self._get_childs(node)
        for child in reversed(childs):
            parent = self._ins_node(parent, child, idx, loc)
        # delete_node가 있어야 할 위치에 새로 붙여진 child 노드를 가져와 반환함
        node = self.__get_node_from_parent(parent, idx, loc)
        # child 노드를 delete_node 대신 반환할 경우 
        # child 노드에 대한 탐사 없이 다음 노드로 넘어가기 때문에
        # 원래 child 노드에 대한 수정이 안이루어 질 수 있기 때문에 
        # fix_nodes를 통해 child 노드 추가 수정
        node = self.fix_nodes(node)
        return node
    
    def _get_childs(self, node):
        childs = []
        if hasattr(node, 'body'):
            for child in node.body:
                childs.append(child)
        if hasattr(node, 'handlers'):
            for child in node.handlers:
                if hasattr(child, 'body'):
                    for c in child.body:
                        childs.append(c)
        if hasattr(node, 'orelse'):
            for child in node.orelse:
                childs.append(child)
        if hasattr(node, 'finalbody'):
            for child in node.finalbody:
                childs.append(child)
        return childs
    
    def _del_node(self, parent, idx, loc):
        if loc == "body":
            del parent.body[idx]
        elif loc == "handlers":
            del parent.handlers[idx]
        elif loc == "orelse":
            del parent.orelse[idx]
        elif loc == "finalbody":
            del parent.finalbody[idx]
        return parent
    

    def ins_nodes(self, node, patch):
        patch, ins_loc = patch
        if hasattr(patch, 'body'):
            # patch.body = [ast.Pass()]
            patch.body = [ast.Break() if isinstance(patch, (ast.While, ast.For)) else ast.Pass()]
        if hasattr(node, "handlers"):
            node.handlers = [ast.ExceptHandler(body=[ast.Pass()])]
        if hasattr(patch, 'orelse'):
            patch.orelse = []
        if hasattr(patch, 'finalbody'):
            patch.finalbody = []

        if ins_loc == 'sibling':
            parent = self.parent_map[node]
            idx, loc = self.__get_child_loc(parent, node)
            parent = self._ins_node(parent, patch, idx+1, loc)
            node = self.__get_node_from_parent(parent, idx, loc)
        elif ins_loc == 'child':
            node = self._ins_node(node, patch, 0, 'body')
        return node
    
    def _ins_node(self, parent, node, idx, loc):
        if loc == "body":
            parent.body.insert(idx, copy.deepcopy(node))
        elif loc == "handlers":
            parent.handlers.insert(idx, copy.deepcopy(node))
        elif loc == "orelse":
            parent.orelse.insert(idx, copy.deepcopy(node))
        elif loc == "finalbody":
            parent.finalbody.insert(idx, copy.deepcopy(node))
        self.update_parent_map(parent)
        return parent

    def rep_nodes(self, node, patch):
        if hasattr(node, 'body'):
            patch.body = node.body
        if hasattr(node, 'handlers'):
            patch.handlers = node.handlers
        if hasattr(node, 'orelse'):
            patch.orelse = node.orelse
        if hasattr(node, 'finalbody'):
            patch.finalbody = node.finalbody
        node = patch
        return node
    
    def update_parent_map(self, node):
        if hasattr(node, 'body'):
            for child in node.body:
                self.parent_map[child] = node
        if hasattr(node, 'handlers'):
            for child in node.handlers:
                self.update_parent_map(child)
        if hasattr(node, 'orelse'):
            for child in node.orelse:
                self.parent_map[child] = node
        if hasattr(node, 'finalbody'):
            for child in node.finalbody:
                self.parent_map[child] = node

    def fix_nodes(self, node):
        if node in self.node_map.keys():
            mutations = self.node_map[node]
            del self.node_map[node]
            for action, patch in mutations.items():
                patch = copy.deepcopy(patch)
                if action == 'del':
                    node = self.del_nodes(node)
                elif action == 'ins':
                    node = self.ins_nodes(node, patch)
                elif action == 'rep':
                    node = self.rep_nodes(node, patch)
                elif action == 'cut':
                    node = patch
                self.update_parent_map(node)
        return node
    
    def visit(self, node):
        # Parent - Child node mapping
        if isinstance(node, (ast.Module, ast.stmt)):
            self.update_parent_map(node)

        # Fixing nodes
        node = self.fix_nodes(node)
        
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def run(self, code):
        tree = ast.parse(code)
        node_map_keys = {node.lineno:node for node in self.node_map.keys()}
        node_map_values = {node.lineno:mutations for node, mutations in self.node_map.items()}
        for child in ast.walk(tree):
            if isinstance(child, ast.stmt) and \
                hasattr(child, "lineno") and \
                child.lineno in node_map_keys.keys():
                del self.node_map[node_map_keys[child.lineno]]
                self.node_map[child] = node_map_values[child.lineno]
            
        tree = self.visit(tree)
        return ast.unparse(tree)
