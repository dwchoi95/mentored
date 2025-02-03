import ast


class SWTVariables(ast.NodeTransformer):
    def __init__(self, var_map:dict):
        self.var_map = var_map

    def visit_FunctionDef(self, node):
        if node.name in self.var_map.keys():
            node.name = self.var_map[node.name]
        return self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if node.name in self.var_map.keys():
            node.name = self.var_map[node.name]
        return self.generic_visit(node)
    
    def visit_Name(self, node):
        if node.id in self.var_map.keys():
            node.id = self.var_map[node.id]
        return self.generic_visit(node)

    def visit_arg(self, node):
        if node.arg in self.var_map.keys():
            node.arg = self.var_map[node.arg]
        return self.generic_visit(node)
    
    def visit_Constant(self, node):
        if node.value in self.var_map.keys():
            node.value = self.var_map[node.value]
        return self.generic_visit(node)
