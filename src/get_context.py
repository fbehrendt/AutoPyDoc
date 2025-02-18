import ast
import os
import pathlib
from typing import Self

from code_representation import Code_obj, Class_obj, Method_obj, CodeRepresenter
from import_finder import ImportFinder

code = CodeRepresenter()

class CodeParser():
    def __init__(self, code_representer, working_dir, debug=False):
        self.code_representer = code_representer
        self.working_dir = working_dir
        self.ducttape = False # TODO create a proper solution. For now only allow dependency creation once
        self.debug = debug
        self.import_finder = ImportFinder(working_dir=working_dir)

    def add_file(self, filename="src\experiments\\ast_tests.py"):
        dir = pathlib.Path().resolve()
        self.full_path = os.path.join(dir, filename)
        self.tree = ast.parse(open(self.full_path).read())
        self.import_finder.add_file(self.full_path)
        self.get_file_modules_classes_and_methods(tree=self.tree)
        
    def create_dependencies(self):
        # TODO id collisions possible with subclasses/class methods (only within the same file)
        # example
        # class A():
        #   def func_a():
        #       pass
        # class B():
        #   class A(): # class name collision
        # def func_a(): # method name collision
        #   pass
        # or
        # class
        if self.ducttape:
            return
        self.ducttape = True
        for code_obj in self.code_representer.objects.values():
            if code_obj.type == "module":
                pass # TODO remove
            self.get_class_and_method_calls(parent_obj=code_obj)
            self.get_args_and_return_type(parent_obj=code_obj)
            self.get_exceptions(parent_obj=code_obj)
            self.check_return_type(method_obj=code_obj)

    def get_file_modules_classes_and_methods(self, tree):
        if isinstance(tree, ast.Module):
            module_name = "" # TODO get module name
            docstring = ast.get_docstring(node=tree, clean=True)
            source_code = open(self.full_path).read()
            module_obj = Code_obj(name=module_name, filename=self.full_path, code_type="module", body=tree.body, ast_tree=tree, docstring=docstring, code=source_code)
            self.code_representer.objects[module_obj.id] = module_obj
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                class_obj = Class_obj(name=class_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(class_obj)
                self.get_class_methods_and_sub_classes(class_tree=node, class_obj_id=class_obj.id)

    def get_class_methods_and_sub_classes(self, class_tree, class_obj_id):
        for node in class_tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(method_obj)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(self.full_path).read(), node, padded=False)
                inner_class_obj = Class_obj(name=class_def_name, filename=self.full_path, signature="signature mock", body=node.body, ast_tree=node, class_obj_id=class_obj_id, docstring=docstring, code=source_code)
                self.code_representer.add_code_obj(inner_class_obj)
                self.get_class_methods_and_sub_classes(class_tree=node, class_obj_id=inner_class_obj.id)
    
    def get_class_and_method_calls(self, parent_obj):
        for node in ast.walk(parent_obj.ast_tree):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Call):
                variable_to_resolve = None # TODO resolve variable(?)
                if hasattr(node.func, "id"):
                    called_func_name = node.func.id
                else:
                    called_func_name = node.func.attr
                    if hasattr(node.func, "value"):
                        skip = False
                        if hasattr(node.func.value, "id"):
                            variable_to_resolve = node.func.value.id
                        elif isinstance(node.func.value, ast.Attribute):
                            variable_to_resolve = node.func.value.attr
                        else:
                            skip = True
                        if not skip:
                            value = node.func.value
                            while hasattr(value, "value"):
                                if hasattr(value.value, "id"):
                                    variable_to_resolve = value.value.id + '.' + variable_to_resolve 
                                else:
                                    variable_to_resolve = value.value.attr + '.' + variable_to_resolve 
                                value = value.value
                if variable_to_resolve is not None:
                    # TODO resolve variable
                    if not self.debug:
                        raise NotImplementedError
                        
                if self.full_path + "_" + "method" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "method"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    parent_obj.add_called_method(called_func_id)
                elif self.full_path + "_" + "class" + "_" + called_func_name in self.code_representer.objects.keys():
                    called_func_type = "class"
                    called_func_id = self.full_path + "_" + called_func_type + "_" + called_func_name
                    parent_obj.add_called_class(called_func_id)
                else:
                    print("Call from external file. Trying to resolve")
                    matching_imports = self.import_finder.resolve_external_call(call=called_func_name, filename=parent_obj.filename, code_representer=self.code_representer)
                    if matching_imports is None or matching_imports == []:
                        print("Called code not found. (Happens when calling a class or method not defined in the file)")
                        continue
                    else:
                        if len(matching_imports) == 1:
                            called_func_id = matching_imports[0].id
                            if matching_imports[0].type == "class":
                                parent_obj.add_called_class(matching_imports[0].id)
                            elif matching_imports[0].type == "method":
                                parent_obj.add_called_method(matching_imports[0].id)
                            else:
                                raise NotImplementedError
                        for item in matching_imports:
                            if item.name == called_func_name:
                                called_func_id = item.id
                                if item.type == "class":
                                    parent_obj.add_called_class(item.id)
                                elif item.type == "method":
                                    parent_obj.add_called_method(item.id)
                                else:
                                    raise NotImplementedError
                        print()
                        if not self.debug:
                            raise NotImplementedError

                if parent_obj.type == "method":
                    self.code_representer.objects[called_func_id].add_caller_method(parent_obj.id)
                elif parent_obj.type == "class":
                    self.code_representer.objects[called_func_id].add_caller_class(parent_obj.id)
                else:
                    print("Unmatched parent type:", parent_obj.type)
    
    def get_exceptions(self, parent_obj):
        for node in ast.walk(parent_obj.ast_tree):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Raise):
                parent_obj.add_exception(node.exc.id)
        
    def get_args_and_return_type(self, parent_obj):
        node = parent_obj.ast_tree
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
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
                return_type = node.returns.id
            elif hasattr(node.returns, "value"):
                return_type = node.returns.value
            else:
                return_type = None
            if isinstance(return_type, ast.Name):
                return_type = return_type.id
            parent_obj.arguments = arguments
            parent_obj.return_type = return_type
    
    def check_return_type(self, method_obj):
        if not isinstance(method_obj.ast_tree, ast.FunctionDef) and not isinstance(method_obj.ast_tree, ast.AsyncFunctionDef):
            return
        if method_obj.return_type == None:
            print("check if method returns something")
            for line in method_obj.code.split("\n"):
                if line.lstrip().startswith("return"):
                   method_obj.missing_return_type = True 

if __name__ == "__main__":
    code_parser = CodeParser(CodeRepresenter())
    code_parser.add_file()
    code_parser.create_dependencies()
    for node in code_parser.code_representer.objects.values():
        docstring = ast.get_docstring(node=node.ast_tree)
        print(docstring)
    print("finished")