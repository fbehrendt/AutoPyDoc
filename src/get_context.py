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
from extract_affected_code_from_change_info import (
    extract_classes_from_change_info,
    extract_methods_from_change_info,
    extract_module_from_change_info,
)
from import_finder import ImportFinder

code = CodeRepresenter()


class CodeParser:
    """A code parser used to create dependencies between modules, classes and methods"""

    def __init__(
        self,
        code_representer: CodeRepresenter,
        working_dir: str,
        logger,
        debug: bool = False,
        files: list = [],
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
        self.debug = debug
        self.logger = logger
        self.import_finder = ImportFinder(working_dir=working_dir, debug=self.debug)
        for file in files:
            self.add_file(file)

    def add_file(self, filename: str):
        """
        Add a file to the CodeParser

        :param filename: file to add
        :type filename: str
        """
        dir = pathlib.Path().resolve()
        try:
            tree = ast.parse(open(filename).read())
        except Exception as e:
            if e.args[0] == "invalid syntax":
                self.logger.info(filename + " has invalid syntax and will be ignored")
                return
        # TODO add to pull request
        self.import_finder.add_file(filename)
        self.extract_file_modules_classes_and_methods(
            tree=tree, file_path=os.path.join(dir, filename)
        )

    def extract_file_modules_classes_and_methods(self, tree: ast.AST, file_path: str):
        """
        Extract file level modules, classes and methods

        :param tree: abstract syntax tree of the file
        :type tree: ast.AST
        """
        module_id = None
        if isinstance(tree, ast.Module):
            module_name = ""  # TODO get module name
            docstring = ast.get_docstring(node=tree, clean=True)
            source_code = open(file_path).read()
            module_obj = ModuleObject(
                name=module_name,
                filename=file_path,
                ast=tree,
                docstring=docstring,
                code=source_code,
                parent_id=None,
            )
            # module_obj.name = "test" # test frozen variable
            module_id = hash(module_obj)
            self.code_representer.objects[module_obj.id] = module_obj
            self.extract_sub_classes_and_methods(code_obj_id=module_id)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(file_path).read(), node, padded=False
                )
                method_obj = MethodObject(
                    name=func_def_name,
                    filename=file_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    parent_id=module_id,
                    module_id=module_id,
                    outer_class_id=None,
                )
                self.code_representer.add_code_obj(method_obj)
                if module_id is not None:
                    module_obj.add_method_id(method_obj.id)
                self.extract_sub_classes_and_methods(code_obj_id=method_obj.id)
            elif isinstance(node, ast.Lambda):
                self.logger.info("Skipping lambda")
            elif isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(file_path).read(), node, padded=False
                )
                class_obj = ClassObject(
                    name=class_def_name,
                    filename=file_path,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    parent_id=module_id,
                    module_id=module_id,
                    outer_class_id=None,
                )
                self.code_representer.add_code_obj(class_obj)
                if module_id is not None:
                    module_obj.add_class_id(class_obj.id)
                self.extract_sub_classes_and_methods(code_obj_id=class_obj.id)

    def extract_sub_classes_and_methods(
        self,
        code_obj_id: str,
    ):
        """
        Extract methods and sub classes of the given code object

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
        if isinstance(outer_code_obj, MethodObject):
            method_id = outer_code_obj.id
        else:
            method_id = None
        for node in outer_code_obj.ast.body:
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(outer_code_obj.filename).read(), node, padded=False
                )
                method_obj = MethodObject(
                    name=func_def_name,
                    filename=outer_code_obj.filename,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    parent_id=outer_code_obj.id,
                    module_id=module_id,
                    outer_class_id=class_id,
                    outer_method_id=method_id,
                )
                self.code_representer.add_code_obj(method_obj)
                outer_code_obj.add_method_id(method_obj.id)
                self.extract_sub_classes_and_methods(code_obj_id=method_obj.id)
            elif isinstance(node, ast.Lambda):
                self.logger.info("Skipping lambda")
            elif isinstance(node, ast.ClassDef):
                class_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(
                    open(outer_code_obj.filename).read(), node, padded=False
                )
                inner_class_obj = ClassObject(
                    name=class_def_name,
                    filename=outer_code_obj.filename,
                    ast=node,
                    docstring=docstring,
                    code=source_code,
                    parent_id=outer_code_obj.id,
                    module_id=module_id,
                    outer_class_id=class_id,
                    outer_method_id=method_id,
                )
                self.code_representer.add_code_obj(inner_class_obj)
                outer_code_obj.add_class_id(inner_class_obj.id)
                self.extract_sub_classes_and_methods(code_obj_id=inner_class_obj.id)

    def extract_class_and_method_calls(self):
        """
        Extract classes and methods called by the CodeObject
        """
        for parent_obj in self.code_representer.get_code_objects():
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

                    try:
                        code_obj = self.code_representer.get_by_filename_and_name(
                            filename=parent_obj.filename, name=called_func_name
                        )  # TODO could be ambiguous
                        if isinstance(code_obj, MethodObject):
                            parent_obj.add_called_method(code_obj.id)
                        elif isinstance(code_obj, ClassObject):
                            parent_obj.add_called_class(code_obj.id)
                        else:
                            raise NotImplementedError
                        if isinstance(parent_obj, MethodObject):
                            self.code_representer.objects[
                                code_obj.id
                            ].add_caller_method(parent_obj.id)
                        elif isinstance(parent_obj, ClassObject):
                            self.code_representer.objects[code_obj.id].add_caller_class(
                                parent_obj.id
                            )
                        elif isinstance(parent_obj, ModuleObject):
                            self.code_representer.objects[
                                code_obj.id
                            ].add_caller_module(parent_obj.id)
                        else:
                            raise NotImplementedError
                    except Exception as e:
                        if hasattr(e, "args"):
                            if e.args[0] == "No matches":
                                # print("Call from external file. Trying to resolve")
                                matching_imports = (
                                    self.import_finder.resolve_external_call(
                                        call=called_func_name,
                                        filename=parent_obj.filename,
                                        code_representer=self.code_representer,
                                    )
                                )
                                if matching_imports is None or matching_imports == []:
                                    # print("Called code not found. (Happens when calling a class or method not defined in the file)")
                                    continue
                                else:
                                    if len(matching_imports) == 1:
                                        called_func_id = matching_imports[0].id
                                        if matching_imports[0].code_type == "class":
                                            parent_obj.add_called_class(called_func_id)
                                        elif matching_imports[0].code_type == "method":
                                            parent_obj.add_called_method(called_func_id)
                                        else:
                                            raise NotImplementedError
                                    else:
                                        raise NotImplementedError
                                    if isinstance(parent_obj, MethodObject):
                                        self.code_representer.objects[
                                            called_func_id
                                        ].add_caller_method(parent_obj.id)
                                    elif isinstance(parent_obj, ClassObject):
                                        self.code_representer.objects[
                                            called_func_id
                                        ].add_caller_class(parent_obj.id)
                                    elif isinstance(parent_obj, ModuleObject):
                                        self.code_representer.objects[
                                            called_func_id
                                        ].add_caller_module(parent_obj.id)
                                    else:
                                        raise NotImplementedError
                            elif e.args[0] == "More than one match":
                                raise NotImplementedError

    def extract_exceptions(self):
        """
        Extract exceptions raised by the CodeObject
        """
        classes_and_modules = self.code_representer.get_modules()
        classes_and_modules.extend(self.code_representer.get_methods())
        for code_obj in classes_and_modules:
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

    def extract_args_and_return_type(self):
        """
        Extract arguments and return type of methods
        """
        for method_obj in self.code_representer.get_methods():
            node = method_obj.ast
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
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
                            new_arg["type"] = (
                                Self  # see https://peps.python.org/pep-0673/
                            )
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

    def check_return_type(self):
        """
        Check if the return type of a method is missing
        """
        for method_obj in self.code_representer.get_methods():
            if not isinstance(method_obj.ast, ast.FunctionDef) and not isinstance(
                method_obj.ast, ast.AsyncFunctionDef
            ):
                return
            if method_obj.return_type is None:
                # print("check if method returns something")
                for line in method_obj.code.split("\n"):
                    if line.lstrip().startswith("return"):
                        method_obj.missing_return_type = True

    def extract_attributes(self):
        for class_obj in self.code_representer.get_classes():
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
                elif isinstance(node, ast.AnnAssign):
                    if hasattr(node.target, "value") and hasattr(
                        node.target.value, "id"
                    ):
                        if node.target.value.id == "self":
                            if hasattr(node.annotation, "id"):
                                attr_type = node.annotation.id
                            elif hasattr(node.annotation, "value") and hasattr(
                                node.annotation.value, "id"
                            ):
                                attr_type = node.annotation.value.id
                            else:
                                raise NotImplementedError
                            attr = {"name": node.target.id, "type": attr_type}
                            class_obj.add_instance_attribute(attribute=attr)

    def set_code_affected_by_changes_to_outdated(self, changes: list):
        for change in changes:
            changed_methods = extract_methods_from_change_info(
                filename=change["filename"],
                change_start=change["start"],
                change_length=change["lines_changed"],
            )
            changed_classes = extract_classes_from_change_info(
                filename=change["filename"],
                change_start=change["start"],
                change_length=change["lines_changed"],
            )
            if not self.debug:
                raise NotImplementedError
            changed_module = extract_module_from_change_info(
                filename=change["filename"]
            )
            for changed_method in changed_methods:
                method_obj = self.code_representer.get_by_type_filename_and_code(
                    code_type="method",
                    filename=changed_method["filename"],
                    code=changed_method["content"],
                )
                self.code_representer.set_outdated(method_obj.id)
                method_obj.dev_comments = self.extract_dev_comments(method_obj)

            for changed_class in changed_classes:
                class_obj = self.code_representer.get_by_type_filename_and_code(
                    code_type="class",
                    filename=changed_class["filename"],
                    code=changed_class["content"],
                )
                self.code_representer.set_outdated(class_obj.id)
                class_obj.dev_comments = self.extract_dev_comments(class_obj)

            module_obj = self.code_representer.get_by_type_filename_and_code(
                code_type="module",
                filename=changed_module["filename"],
                code=changed_module["content"],
            )
            self.code_representer.set_outdated(module_obj.id)
            module_obj.dev_comments = self.extract_dev_comments(class_obj)

    def extract_dev_comments(self, code_obj: CodeObject) -> list[str]:
        """
        Extract developer comments. NOT IMPLEMENTED

        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: CodeObject

        :return: dev comments
        :return type: list[str]

        :raises NotImplementedError: raised when not in debug mode, because this is not yet implemented
        """
        self.logger.info("###MOCK### Extracting developer comments")
        if not self.debug:
            raise NotImplementedError
        else:
            return ["A developer comment"]


if __name__ == "__main__":
    code_parser = CodeParser(CodeRepresenter())
    code_parser.add_file()
    code_parser.create_dependencies()
    for node in code_parser.code_representer.objects.values():
        docstring = ast.get_docstring(node=node.ast)
        print(docstring)
    print("finished")
