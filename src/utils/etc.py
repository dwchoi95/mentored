import re

def get_stmt_list(code:str) -> list:
    return code.split('\n')

def divide(a, b):
    try: res = a/b
    except ZeroDivisionError:
        res = 0
    return res

def extract_number(filename):
    return int(re.search(r'problem_(\d+)/', filename).group(1))
