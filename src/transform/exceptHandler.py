import ast

class ExceptHandler(ast.NodeTransformer):
    def __init__(self):
        self.new_line_map = dict()
        self.added_lineno = list()

    def visit_Try(self, node):
        if hasattr(node, 'handlers'):
            loc = node.handlers[0].lineno
            handle_lineno = loc + len(self.added_lineno)
            self.added_lineno.extend([handle_lineno, handle_lineno+1])
            node.handlers.insert(0, ast.ExceptHandler(
            type=ast.Name(id='AssertionError', ctx=ast.Load()),
            body=[
                ast.Expr(
                value=ast.Call(
                    func=ast.Name(id='exit', ctx=ast.Load()),
                    args=[],
                    keywords=[]))]))
            
            for line, new_line in self.new_line_map.items():
                if line >= loc:
                    self.new_line_map[line] = new_line + 2
        return self.generic_visit(node)
    
    def run(self, code:str='', tree:ast=''):
        if code: tree = ast.parse(code)
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                self.new_line_map[node.lineno] = node.lineno
        tree = self.visit(tree)
        self.new_line_map = {new_line:line for line, new_line in self.new_line_map.items()}
        return ast.unparse(tree)
    