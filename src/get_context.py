import ast
import os
import pathlib
from typing import Self

from code_representation import (
    CodeObject,
    ModuleObject,
    ClassObject,
    MethodObject,
    CodeRepresenter,
)
from import_finder import ImportFinder

code = CodeRepresenter()


class CodeParser:
    """A code parser used to create dependencies between modules, classes and methods"""

    def __init__(
        self, code_representer: CodeRepresenter, working_dir: str, debug: bool = False
    ):
        """
        A code parser used to create dependencies between modules, classes and methods

        :param code_representer: CodeRepresenter Object
        :type code_representer: CodeRepresenter
        :param working_dir: path to target code
        :type working_dir: str
        :param debug: toggle debug mode
        :type debug: bool"""
        self.code_representer = code_representer
        self.working_dir = working_dir
        self.ducttape = False  # TODO create a proper solution. For now only allow dependency creation once
        self.debug = debug
        self.import_finder = ImportFinder(working_dir=working_dir, debug=self.debug)

    def add_file(self, filename: str):
        """
        Add a file to the CodeParser

        :param filename: file to add
        :type filename: str
        """
        dir = pathlib.Path().resolve()
        self.full_path = os.path.join(dir, filename)
        self.tree = ast.parse(open(self.full_path).read())
        self.import_finder.add_file(self.full_path)
        self.extract_file_modules_classes_and_methods(tree=self.tree)

    def create_dependencies(self):
        """Create dependencies between modules, classes and methods"""
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
            self.extract_class_and_method_calls(parent_obj=code_obj)
            self.extract_args_and_return_type(method_obj=code_obj)
            self.extract_exceptions(code_obj=code_obj)
            if isinstance(code_obj, MethodObject):
                self.check_return_type(method_obj=code_obj)
            elif isinstance(code_obj, ClassObject):
                self.extract_attributes(class_obj=code_obj)

    def extract_file_modules_classes_and_methods(self, tree: ast.AST):
        """
        Extract file level modules, classes and methods

        :param tree: abstract syntax tree of the file
        :type tree: ast.AST
        """
        module_id = None
        if isinstance(tree, ast.Module):
            module_name = ""  # TODO get module name
            docstring = ast.get_docstring(node=tree, clean=True)
            source_code = open(self.full_path).read()
            module_obj = ModuleObject(
                name=module_name,
                filename=self.full_path,
                ast=tree,
                docstring=docstring,
                code=source_code,
            )
            # module_obj.name = "test" # test frozen variable
            module_id = hash(module_obj)
            self.code_representer.objects[module_obj.id] = module_obj
            self.extract_class_or_module_methods_and_sub_classes(code_obj_id=module_id)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(self.full_path).read(), node, padded=False
                )
                method_obj = MethodObject(
                    name=func_def_name,
                    filename=self.full_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    module_id=module_id,
                    outer_class_id=None,
                )
                self.code_representer.add_code_obj(method_obj)
                if module_id is not None:
                    module_obj.add_method_id(method_obj.id)
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(self.full_path).read(), node, padded=False
                )
                method_obj = MethodObject(
                    name=func_def_name,
                    filename=self.full_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    module_id=module_id,
                    outer_class_id=None,
                )
                self.code_representer.add_code_obj(method_obj)
                if module_id is not None:
                    module_obj.add_method_id(method_obj.id)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(self.full_path).read(), node, padded=False
                )
                class_obj = ClassObject(
                    name=class_def_name,
                    filename=self.full_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    module_id=module_id,
                    outer_class_id=None,
                )
                self.code_representer.add_code_obj(class_obj)
                if module_id is not None:
                    module_obj.add_class_id(class_obj.id)
                self.extract_class_or_module_methods_and_sub_classes(
                    code_obj_id=class_obj.id
                )

    def extract_class_or_module_methods_and_sub_classes(
        self,
        code_obj_id: str,
    ):
        """
        Extract methods and sub classes of the given class

        :param class_tree: abstract syntax tree of the class
        :type class_tree: ast.AST
        :param class_obj_id: ClassObject id
        :type class_obj_id: str
        """
        outer_code_obj = self.code_representer.get(code_obj_id)
        if isinstance(outer_code_obj, ModuleObject):
            module_id = outer_code_obj.id
        else:
            module_id = outer_code_obj.module_id
        if isinstance(outer_code_obj, ClassObject):
            class_id = outer_code_obj.id
        else:
            class_id = None
        for node in outer_code_obj.ast.body:
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(self.full_path).read(), node, padded=False
                )
                method_obj = MethodObject(
                    name=func_def_name,
                    filename=self.full_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    module_id=module_id,
                    outer_class_id=class_id,
                )
                self.code_representer.add_code_obj(method_obj)
                outer_code_obj.add_method_id(method_obj.id)
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(self.full_path).read(), node, padded=False
                )
                inner_class_obj = ClassObject(
                    name=class_def_name,
                    filename=self.full_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    module_id=module_id,
                    outer_class_id=class_id,
                )
                self.code_representer.add_code_obj(inner_class_obj)
                outer_code_obj.add_class_id(inner_class_obj.id)
                self.extract_class_or_module_methods_and_sub_classes(
                    code_obj_id=inner_class_obj.id
                )

    def extract_class_and_method_calls(self, parent_obj: CodeObject):
        """
        Extract classes and methods called by the CodeObject

        :param parent_obj: CodeObject
        :type parent_obj: CodeObject
        """
        for node in ast.walk(parent_obj.ast):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Call):
                variable_to_resolve = None  # TODO resolve variable(?)
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
                                    variable_to_resolve = (
                                        value.value.id + "." + variable_to_resolve
                                    )
                                else:
                                    variable_to_resolve = (
                                        value.value.attr + "." + variable_to_resolve
                                    )
                                value = value.value
                if variable_to_resolve is not None:
                    # TODO resolve variable
                    if not self.debug:
                        raise NotImplementedError

                if (
                    self.full_path + "_" + "method" + "_" + called_func_name
                    in self.code_representer.objects.keys()
                ):
                    called_func_type = "method"
                    called_func_id = (
                        self.full_path + "_" + called_func_type + "_" + called_func_name
                    )
                    parent_obj.add_called_method(called_func_id)
                elif (
                    self.full_path + "_" + "class" + "_" + called_func_name
                    in self.code_representer.objects.keys()
                ):
                    called_func_type = "class"
                    called_func_id = (
                        self.full_path + "_" + called_func_type + "_" + called_func_name
                    )
                    parent_obj.add_called_class(called_func_id)
                else:
                    # print("Call from external file. Trying to resolve")
                    matching_imports = self.import_finder.resolve_external_call(
                        call=called_func_name,
                        filename=parent_obj.filename,
                        code_representer=self.code_representer,
                    )
                    if matching_imports is None or matching_imports == []:
                        # print("Called code not found. (Happens when calling a class or method not defined in the file)")
                        continue
                    else:
                        if len(matching_imports) == 1:
                            called_func_id = matching_imports[0].id
                            if matching_imports[0].code_type == "class":
                                parent_obj.add_called_class(matching_imports[0].id)
                            elif matching_imports[0].code_type == "method":
                                parent_obj.add_called_method(matching_imports[0].id)
                            else:
                                raise NotImplementedError
                        for item in matching_imports:
                            if item.name == called_func_name:
                                called_func_id = item.id
                                if item.code_type == "class":
                                    parent_obj.add_called_class(item.id)
                                elif item.code_type == "method":
                                    parent_obj.add_called_method(item.id)
                                else:
                                    raise NotImplementedError
                        if not self.debug:
                            raise NotImplementedError

                if isinstance(parent_obj, MethodObject):
                    self.code_representer.objects[called_func_id].add_caller_method(
                        parent_obj.id
                    )
                elif isinstance(parent_obj, ClassObject):
                    self.code_representer.objects[called_func_id].add_caller_class(
                        parent_obj.id
                    )
                else:
                    print("Unmatched parent type:", parent_obj.code_type)

    def extract_exceptions(self, code_obj: CodeObject):
        """
        Extract exceptions raised by the CodeObject

        :param code_obj: CodeObject
        :type code_obj: CodeObject
        """
        for node in ast.walk(code_obj.ast):
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Raise):
                if hasattr(node.exc, "id"):
                    code_obj.add_exception(node.exc.id)
                elif hasattr(node.exc, "func"):
                    code_obj.add_exception(node.exc.func.id)
                else:
                    if not self.debug:
                        raise NotImplementedError

    def extract_args_and_return_type(self, method_obj: MethodObject):
        """
        Extract arguments and return type of methods

        :param method_obj: MethodObject
        :type method_obj: MethodObject
        """
        node = method_obj.ast
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            arguments = []
            for i in range(len(node.args.args)):
                arg = node.args.args[i]
                new_arg = {"name": arg.arg}
                if arg.annotation is not None:
                    if hasattr(arg.annotation, "id"):
                        new_arg["type"] = arg.annotation.id
                    elif hasattr(arg.annotation, "value") and hasattr(
                        arg.annotation.value, "id"
                    ):
                        new_arg["type"] = arg.annotation.value.id
                    elif hasattr(arg, "type_comment"):
                        new_arg["type"] = arg.type_comment
                else:
                    if i == 0 and arg.arg == "self":
                        new_arg["type"] = Self  # see https://peps.python.org/pep-0673/
                    else:
                        method_obj.add_missing_arg_type(arg.arg)
                if i < len(node.args.defaults):
                    default = node.args.defaults[i]
                    if isinstance(default, ast.Constant):
                        new_arg["default"] = default.value
                    elif isinstance(default, ast.List):
                        new_arg["default"] = [item.value for item in default.elts]
                method_obj.add_argument(new_arg)
            if hasattr(node.returns, "id"):
                return_type = node.returns.id
            elif hasattr(node.returns, "value"):
                return_type = node.returns.value
            else:
                return_type = None
            if isinstance(return_type, ast.Name):
                return_type = return_type.id
            method_obj.return_type = return_type

    def check_return_type(self, method_obj: MethodObject):
        """
        Check if the return type of a method is missing

        :param method_obj: MethodObject
        :type method_obj: MethodObject
        """
        if not isinstance(method_obj.ast, ast.FunctionDef) and not isinstance(
            method_obj.ast, ast.AsyncFunctionDef
        ):
            return
        if method_obj.return_type is None:
            # print("check if method returns something")
            for line in method_obj.code.split("\n"):
                if line.lstrip().startswith("return"):
                    method_obj.missing_return_type = True

    def extract_attributes(self, class_obj: ClassObject):
        for node in class_obj.ast.body:
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    attr = {"name": node.targets[0].id}
                    class_obj.add_class_attribute(attribute_name=attr)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    if hasattr(node.annotation, "id"):
                        attr_type = node.annotation.id
                    elif hasattr(node.annotation, "value") and hasattr(
                        node.annotation.value, "id"
                    ):
                        attr_type = node.annotation.value.id
                    else:
                        raise NotImplementedError
                    attr = {"name": node.target.id, "type": attr_type}
                    class_obj.add_class_attribute(attribute=attr)
        for node in ast.walk(class_obj.ast):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if hasattr(target, "attr"):
                        if hasattr(target.value, "id"):
                            if target.value.id == "self":
                                attr = {"name": target.attr}
                                class_obj.add_instance_attribute(attribute=attr)


if __name__ == "__main__":
    code_parser = CodeParser(CodeRepresenter())
    code_parser.add_file()
    code_parser.create_dependencies()
    for node in code_parser.code_representer.objects.values():
        docstring = ast.get_docstring(node=node.ast)
        print(docstring)
    print("finished")
