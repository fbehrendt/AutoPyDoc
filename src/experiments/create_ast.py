import ast
import os

tree = ast.parse(open(os.path.abspath("C:/Users/Fabian/Projekte/AutoPyDoc/working_Repo/src/main.py")).read())
print(ast.dump(tree))  # dumps the whole tree

# get the function from the tree body (i.e. from the file's content)
func = tree.body[0]

# get the function argument names
arguments = [a.arg for a in func.args.args]
print('the functions is: %s(%s)' % (func.name, ', '.join(arguments)))