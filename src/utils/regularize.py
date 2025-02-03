import ast
import re

class Regularize:
    @classmethod
    def __remove_comments_and_docstrings(cls, code):
        # Remove single-line comments and strings that are used as comments
        code = re.sub(r'(?m)^\s*(#.*|\'[^\']*\'|"[^"]*")\s*$', '', code)
        # Remove multi-line comments and docstrings
        code = re.sub(r'(?s)(\'\'\'.*?\'\'\')|(""".*?""")', '', code)
        return code
    
    @classmethod
    def __regular(cls, code):
        return ast.unparse(ast.parse(code))

    @classmethod
    def run(cls, code):
        code = cls.__regular(code)
        code = cls.__remove_comments_and_docstrings(code)
        return cls.__regular(code)
    