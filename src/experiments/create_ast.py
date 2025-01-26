import ast
import os

tree = ast.parse(open(os.path.abspath("C:/Users/Fabian/Github/AutoPyDoc/working_repo/main.py")).read()) # TODO get abs path relative to this file
# print(ast.dump(tree))  # dumps the whole tree

caller_to_callee = {} #str -> list(str)
callee_to_caller = {} #str -> list(str)
function_calls = [] # if function is called, but has no caller, the function is called when the file itself is executed

# TODO idk how lambdas are treated at this point
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        print("Function call:", node.func.id)
        function_calls.append(node.func.id)
    elif isinstance(node, ast.FunctionDef):
        print("Function definition:", node.name)
        caller_to_callee[node.name] = []
        for inner_node in ast.walk(node):
            if isinstance(inner_node, ast.Call):
                print("Function call within", node.name, ":", inner_node.func.id)
                caller_to_callee[node.name].append(inner_node.func.id)
                if inner_node.func.id not in callee_to_caller.keys():
                    callee_to_caller[inner_node.func.id] = []
                callee_to_caller[inner_node.func.id].append(node.name)

print("###Function calls###")
for function_call in function_calls:
    print(function_call)
print()

print("###Caller to callee###")
for caller, callees in caller_to_callee.items():
    print("Caller:", caller, "calls:")
    for callee in callees:
        print(callee)
    print()

print("###Callee to caller###")
for callee, callers in callee_to_caller.items():
    print("Callee:", callee, "is called by:")
    for caller in callers:
        print(caller)
    print()



# get the function from the tree body (i.e. from the file's content)
#func = tree.body[0]

# get the function argument names
#arguments = [a.arg for a in func.args.args]
#print('the functions is: %s(%s)' % (func.name, ', '.join(arguments)))