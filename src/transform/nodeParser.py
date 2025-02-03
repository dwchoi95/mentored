from ordered_set import OrderedSet
import ast
import keyword
import builtins

RESERVED_WORDS = OrderedSet(keyword.kwlist)
BUILTIN_WORDS = OrderedSet(dir(builtins))
MODULE_WORDS = OrderedSet(globals())

class NodeParser(ast.NodeVisitor):
    def __init__(self):
        self.line_node_map = dict()
        self.line_vars_map = dict()
        self.cfs = {}
        self.var_name_list = OrderedSet()
        self.key_input = False
        self.parent_map = dict()
        self.object_line_node_dict = {}
        self.objectCall_line_dict = {}
    
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
    
    def visit(self, node):
        if isinstance(node, (ast.Module, ast.stmt)):
            self.update_parent_map(node)

            if hasattr(node, 'lineno'):
                self.line_node_map[node.lineno] = node
                if isinstance(node, (
                    ast.FunctionDef, 
                    ast.ClassDef,
                    ast.For,
                    ast.While,
                    ast.Try,
                    ast.If,
                    # ast.Break,
                    # ast.Continue,
                    # ast.Return
                    )):
                    self.cfs[node.lineno] = node.__class__.__name__

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.object_line_node_dict[node.lineno] = node.name
        
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
    
    def visit_Name(self, node):
        if hasattr(node, 'id'):
            if isinstance(node.ctx, ast.Store):
                var_name = str(node.id)
                if var_name not in RESERVED_WORDS and \
                    var_name not in BUILTIN_WORDS and \
                    var_name not in MODULE_WORDS:
                    self.var_name_list.add(var_name)
                    self.line_vars_map.setdefault(node.lineno, []).append(var_name)
        self.generic_visit(node)

    def visit_arg(self, node):
        self.var_name_list.add(str(node.arg))
        self.line_vars_map.setdefault(node.lineno, []).append(str(node.arg))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if hasattr(node, 'attr'):
            if node.attr in ['readline', 'stdin']:
                self.key_input = True
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if hasattr(node, 'func') and hasattr(node.func, 'id'):
            if node.func.id == 'input': self.key_input = True
            if node.func.id in self.object_line_node_dict.values():
                for lineno, func_id in self.object_line_node_dict.items():
                    if func_id == node.func.id and lineno < node.lineno:
                        self.objectCall_line_dict[node.lineno] = lineno
        self.generic_visit(node)
    
    def run(self, code:str='', tree:ast=''):
        if code: tree = ast.parse(code)
        self.visit(tree)
        