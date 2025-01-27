import ast

code = """
if 1 == 1 and 2 == 2 and 3 == 3:
     test = 1
"""
node = ast.parse(code)
print(ast.get_source_segment(code, node))