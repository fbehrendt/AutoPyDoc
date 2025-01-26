import ast
import os
import pathlib

class FunctionDependencies():
    def __init__(self, filename="working_repo\main.py"):
        self.file_to_tree = {}
        self.caller_to_callee = {} #str -> list(str)
        self.callee_to_caller = {} #str -> list(str)
        self.function_calls = [] # if function is called, but has no caller, the function is called when the file itself is executed
        self.called_by_file = []

        if filename:
            self.add_file(filename=filename)

    def add_file(self, filename="working_repo\main.py"):
        dir = pathlib.Path().resolve()
        self.full_path = os.path.join(dir, filename)
        self.tree = ast.parse(open(self.full_path).read())
        self.file_to_tree[self.full_path] = self.tree

        # TODO idk how lambdas are treated at this point
        # TODO add file and class information to function information
        # TODO handle function calls to and from other files
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    func_name = node.func.id
                else:
                    func_name = node.func.attr
                # print("Function call:", func_name)
                self.function_calls.append(func_name)
            elif isinstance(node, ast.FunctionDef):
                # print("Function definition:", node.name)
                if node.name not in self.caller_to_callee.keys():
                    self.caller_to_callee[node.name] = []
                for inner_node in ast.walk(node):
                    if isinstance(inner_node, ast.Call):
                        if hasattr(inner_node.func, "id"):
                            inner_func_name = inner_node.func.id
                        else:
                            inner_func_name = inner_node.func.attr
                        # print("Function call within", node.name, ":", inner_func_name)
                        self.caller_to_callee[node.name].append(inner_func_name)
                        if inner_func_name not in self.callee_to_caller.keys():
                            self.callee_to_caller[inner_func_name] = []
                        self.callee_to_caller[inner_func_name].append(node.name)

        for function_call in self.function_calls:
            if function_call not in self.callee_to_caller.keys():
                self.called_by_file.append(function_call)
        
        # TODO remove calls to functions that are not part of the code

    def get_callers(self, callee):
        if callee in self.callee_to_caller.keys():
            return self.callee_to_caller[callee]
        else:
            return []
    
    def get_callees(self, caller):
        if caller in self.caller_to_callee.keys():
            return self.caller_to_callee[caller]
        else:
            return []

    def get_function_context(self, function_name):
        return {"callers": self.get_callers(function_name),
                "callees": self.get_callees(function_name),
                # class
                # module
                }
