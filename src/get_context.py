import ast
import os
import pathlib
from typing import Self

from code_representation import Code_obj, Class_obj, Method_obj, CodeRepresenter

code = CodeRepresenter()

class CodeParser():
    def __init__(self, code_representer):
        self.code_representer = code_representer

    def add_file(self, filename="src\experiments\\ast_tests.py"):
        dir = pathlib.Path().resolve()
        self.full_path = os.path.join(dir, filename)
        self.tree = ast.parse(open(self.full_path).read())
        self.get_file_modules_classes_and_methods(tree=self.tree)
        # TODO first read all files, then do the call dependencies
        for code_obj in self.code_representer.objects.values():
            self.get_class_and_method_calls(parent_obj=code_obj)
            self.get_args_and_return_type(parent_obj=code_obj)
            self.get_exceptions(parent_obj=code_obj)
        self.get_file_level_class_and_method_calls(self.tree)

    def get_file_modules_classes_and_methods(self, tree):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                print("Function def:", func_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                print("Async function def:", func_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                print("Class def:", class_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                class_obj = Class_obj(name=class_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(class_obj)
                self.get_class_methods_and_sub_classes(class_tree=node, class_obj_id=class_obj.id)
            if isinstance(node, ast.Module):
                print("Module")

    def get_class_methods_and_sub_classes(self, class_tree, class_obj_id):
        for node in class_tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                print("Function def:", func_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                print("Async function def:", func_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                print("Class def:", class_def_name)
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                inner_class_obj = Class_obj(name=class_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(inner_class_obj)
                self.get_class_methods_and_sub_classes(class_tree=node, class_obj_id=inner_class_obj.id)
    
    def get_class_and_method_calls(self, parent_obj):
        for node in ast.walk(parent_obj.ast_tree):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    called_func_name = node.func.id
                else:
                    called_func_name = node.func.attr
                if self.full_path + "_" + "method" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "method"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    parent_obj.add_called_method(called_func_id)
                elif self.full_path + "_" + "class" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "class"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    parent_obj.add_called_class(called_func_id)
                else:
                    print("Called code not found. (Happens when calling a class or method not defined in the file)")
                    return

                if parent_obj.type == "method":
                    self.code_representer.objects[called_func_id].add_caller_method(parent_obj.id)
                elif parent_obj.type == "class":
                    self.code_representer.objects[called_func_id].add_caller_class(parent_obj.id)
                else:
                    print("Unmatched parent type:", parent_obj.type)

                print()
                print("Call:", called_func_name)
                print("Call type:", called_func_type)
                print("Called by:", parent_obj.id)
                print()
    
    def get_exceptions(self, parent_obj):
        for node in ast.walk(parent_obj.ast_tree):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Raise):
                parent_obj.add_exception(node.exc.id)
        
    def get_args_and_return_type(self, parent_obj):
        node = parent_obj.ast_tree
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            print("Arguments")
            arguments = []
            for i in range(len(node.args.args)):
                arg = node.args.args[i]
                new_arg = {"name": arg.arg}
                if arg.annotation is not None:
                    new_arg["type"] = arg.annotation.id
                else: 
                    if i == 0 and arg.arg == "self":
                        new_arg["type"] = Self # see https://peps.python.org/pep-0673/
                    else:
                        parent_obj.add_missing_arg_type(arg.arg)
                if i < len(node.args.defaults):
                    default = node.args.defaults[i]
                    if isinstance(default, ast.Constant):
                        new_arg["default"] = default.value
                    elif isinstance(default, ast.List):
                        new_arg["default"] = [item.value for item in default.elts]
                arguments.append(new_arg)
            if hasattr(node.returns, "id"):
                print("Returns", node.returns.id)
                return_type = node.returns.id
            elif hasattr(node.returns, "value"):
                print("Returns", node.returns.value)
                return_type = node.returns.value
            else:
                return_type = None
                print("No return")
            if isinstance(return_type, ast.Name):
                return_type = return_type.id
            parent_obj.arguments = arguments
            parent_obj.return_type = return_type

    # TODO deduplicate
    # TODO that's not how modules work
    def get_file_level_class_and_method_calls(self, tree):
        module_name = self.full_path + "_module"
        docstring = ast.get_docstring(node=tree, clean=True)
        source_code = ast.get_source_segment(open(self.full_path).read(), tree, padded=False)
        module_obj = Code_obj(name=module_name, filename=self.full_path, code_type="module", body=tree.body, ast_tree=tree, docstring=docstring, code=source_code)
        code_parser.code_representer.objects[module_name] = module_obj
        for node in tree.body:
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    called_func_name = node.func.id
                else:
                    called_func_name = node.func.attr
                if self.full_path + "_" + "method" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "method"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    module_name.add_called_method(called_func_id)
                elif self.full_path + "_" + "class" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "class"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    module_name.add_called_class(called_func_id)
                else:
                    print("Called code not found. (Happens when calling a class or method not defined in the file)")
                    return

                if module_name.type == "method":
                    self.code_representer.objects[called_func_id].add_caller_method(module_name.id)
                elif module_name.type == "class":
                    self.code_representer.objects[called_func_id].add_caller_class(module_name.id)
                else:
                    print("Unmatched parent type:", module_name.type)
    
code_parser = CodeParser(CodeRepresenter())
code_parser.add_file()
for node in code_parser.code_representer.objects.values():
    docstring = ast.get_docstring(node=node.ast_tree)
    print(docstring)
print("finished")