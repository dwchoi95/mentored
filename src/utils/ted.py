import ast
import Levenshtein
from zss import simple_distance, Node
from functools import cache

class TED:
    @classmethod
    def init_cache(cls):
        cls._ast_to_tree.cache_clear()
        cls.get_cfs.cache_clear()
        
    @classmethod
    def __ast_to_tree(cls, node):
        """
        Recursively converts an AST node into a tree format suitable for zss library.
        """
        if not isinstance(node, ast.AST):
            return Node(str(node))
        
        tree = Node(type(node).__name__)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    tree.addkid(cls.__ast_to_tree(item))
            elif isinstance(value, ast.AST):
                tree.addkid(cls.__ast_to_tree(value))
            else:
                tree.addkid(Node(str(value)))
        return tree
    
    @classmethod
    @cache
    def _ast_to_tree(cls, code):
        return cls.__ast_to_tree(ast.parse(code))

    @classmethod
    def __compute_ast_size(cls, tree):
        """
        Computes the size of the AST tree.
        """
        if tree is None:
            return 0
        size = 1  # count the current node
        for child in tree.children:
            size += cls.__compute_ast_size(child)
        return size
    
    @classmethod
    def relative_patch_size(cls, buggy, patch):
        buggy_tree = cls._ast_to_tree(buggy)
        patch_tree = cls._ast_to_tree(patch)
        ted = simple_distance(buggy_tree, patch_tree)
        buggy_size = cls.__compute_ast_size(buggy_tree)
        return round(ted / buggy_size, 2)
    
    @classmethod
    def compute_ted(cls, code1, code2):
        """
        Computes the tree edit distance between two pieces of Python code.
        """
        tree1 = cls._ast_to_tree(code1)
        tree2 = cls._ast_to_tree(code2)
        return simple_distance(tree1, tree2)

    @classmethod
    def compute_sim(cls, code1, code2):
        """
        Computes the similarity between two pieces of Python code based on tree edit distance.
        """
        tree1 = cls._ast_to_tree(code1)
        tree2 = cls._ast_to_tree(code2)
        distance = simple_distance(tree1, tree2)
        max_distance = cls.__compute_ast_size(tree1) + cls.__compute_ast_size(tree2)
        similarity = 1 - distance / max_distance
        return similarity
    
    @classmethod
    @cache
    def get_cfs(cls, code):
        """
        Extracts the control flow structure from the code.
        """
        tree = ast.parse(code)
        cfs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, 
                                 ast.While,
                                 ast.If, 
                                 ast.Try, 
                                 ast.With,
                                 ast.FunctionDef,
                                 ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                cfs.append(node.__class__.__name__)
        return cfs
    
    @classmethod
    def compute_cfs(cls, code1, code2):
        """
        Computes the cfs edit distance between two pieces of code.
        """
        cfs1 = cls.get_cfs(code1)
        cfs2 = cls.get_cfs(code2)
        return Levenshtein.distance(cfs1, cfs2)
    
    
    


# Example usage
class TEDTest:
    @staticmethod
    def run(code1, code2):
        distance = TED.compute_ted(code1, code2)
        print(f"Distance: {distance}")
        similarity = TED.compute_sim(code1, code2)
        print(f"Similarity: {similarity}")
        rps = TED.relative_patch_size(code1, code2)
        print(f"RPS: {rps}")
