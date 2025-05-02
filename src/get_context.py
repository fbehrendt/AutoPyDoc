import ast
import os
import pathlib
import sys
from typing import Self

from code_representation import (
    ClassObject,
    CodeObject,
    CodeRepresenter,
    MethodObject,
    ModuleObject,
)
from extract_affected_code_from_change_info import (
    extract_classes_from_change_info,
    extract_methods_from_change_info,
    extract_module_from_change_info,
)
from import_finder import ImportFinder

code = CodeRepresenter()  # TODO what is this for?


class CodeParser:
    """A code parser used to create dependencies between modules, classes and methods"""

    def __init__(
        self,
        code_representer: CodeRepresenter,
        working_dir: str | None,
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
        if self.working_dir is not None:
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
            sys.stderr = open(os.devnull, "w")
            tree = ast.parse(open(filename).read())
            if self.working_dir is not None:
                self.import_finder.add_file(filename)
            self.extract_file_modules_classes_and_methods(
                tree=tree, file_path=os.path.join(dir, filename)
            )
            sys.stderr = sys.__stderr__
        except Exception as e:
            if e.args[0] == "invalid syntax":
                self.logger.info(filename + " has invalid syntax and will be ignored")
                return
        # TODO add to pull request

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
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                docstring = ast.get_docstring(node=node, clean=True)
                source_code = ast.get_source_segment(open(file_path).read(), node, padded=False)
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
                source_code = ast.get_source_segment(open(file_path).read(), node, padded=False)
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
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
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
            # remove code of children
            parent_code_without_children = parent_obj.code
            for child_obj in [
                self.code_representer.get(child_id)
                for child_id in [*parent_obj.class_ids, *parent_obj.method_ids]
            ]:
                parent_code_without_children = parent_code_without_children.replace(
                    child_obj.code, ""
                )
            # remove annotations
            new_parent_code_without_annotations = []
            for line in parent_code_without_children.split("\n"):
                if not line.lstrip().startswith("@"):
                    new_parent_code_without_annotations.append(line)
            parent_code_without_children = "\n".join(new_parent_code_without_annotations)

            try:
                sys.stderr = open(os.devnull, "w")
                parent_ast_without_children = ast.parse(parent_code_without_children)
            except Exception as e:
                if isinstance(e, IndentationError):
                    # empty code object apart from child methods and classes
                    sys.stderr = sys.__stderr__
                    return
            sys.stderr = sys.__stderr__

            for node in ast.walk(parent_ast_without_children):
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
                                    elif hasattr(value.value, "attr"):
                                        variable_to_resolve = (
                                            value.value.attr + "." + variable_to_resolve
                                        )
                                    else:
                                        if not self.debug:
                                            raise NotImplementedError
                                    value = value.value
                    # Do not include recursive calls, to prevent unsolvable dependencies
                    if called_func_name == parent_obj.name:
                        continue
                    if variable_to_resolve is not None:
                        # TODO resolve variable
                        matches = self.resolve_variable(
                            variable_to_resolve=variable_to_resolve,
                            called_func_name=called_func_name,
                            filename=parent_obj.filename,
                        )
                        if matches is None:
                            continue  # call to python internal methods like print() or methods in imported modules that are not part of the source code
                        matches = [match for match in matches if match.name == called_func_name]
                        if len(matches) == 1:
                            called_code_obj = matches[0]
                        else:
                            raise NotImplementedError
                        # matches = [
                        #    code_obj
                        #    for code_obj in self.code_representer.objects.values()
                        #    if code_obj.filename == outer_code_obj.filename
                        #    and code_obj.parent_id == outer_code_obj.id
                        #    and code_obj.name == called_func_name
                        # ]
                        # if len(matches) == 1:
                        #    called_func = matches[0]
                        # else:
                        #    raise NotImplementedError
                    else:
                        # check this file
                        matches = [
                            code_obj
                            for code_obj in self.code_representer.objects.values()
                            if code_obj.name == called_func_name
                            and code_obj.filename == parent_obj.filename
                        ]
                        if len(matches) == 1:
                            called_code_obj = matches[0]
                        elif len(matches) > 1:
                            # if more than one code object in this file maches, check if one of them exists only locally
                            if (
                                len(
                                    [match for match in matches if match.parent_id == parent_obj.id]
                                )
                                > 0
                            ):
                                matches = [
                                    match for match in matches if match.parent_id == parent_obj.id
                                ]
                                if len(matches) == 1:
                                    called_code_obj = matches[0]
                                else:  # still more than one
                                    raise NotImplementedError
                        elif len(matches) == 0:
                            # check imports
                            matches = self.import_finder.resolve_external_call(
                                called_func_name,
                                parent_obj.filename,
                                code_representer=self.code_representer,
                            )
                            if matches is None:
                                continue  # call to python internal methods like print() or methods in imported modules that are not part of the source code
                            matches = [
                                match
                                for match in matches
                                if match.parent_id is None
                                or self.code_representer.get(match.parent_id).code_type == "module"
                            ]
                            if len(matches) == 1:
                                called_code_obj = matches[0]
                            elif len(matches) > 1:
                                raise NotImplementedError
                            elif len(matches) == 0:
                                raise NotImplementedError
                    # add called method/class
                    if called_code_obj.code_type == "class":
                        parent_obj.add_called_class(called_code_obj.id)
                    elif called_code_obj.code_type == "method":
                        parent_obj.add_called_method(called_code_obj.id)
                    else:
                        raise NotImplementedError
                    # add caller module/class/method
                    if isinstance(parent_obj, MethodObject):
                        self.code_representer.objects[called_code_obj.id].add_caller_method(
                            parent_obj.id
                        )
                    elif isinstance(parent_obj, ClassObject):
                        self.code_representer.objects[called_code_obj.id].add_caller_class(
                            parent_obj.id
                        )
                    elif isinstance(parent_obj, ModuleObject):
                        self.code_representer.objects[called_code_obj.id].add_caller_module(
                            parent_obj.id
                        )
                    else:
                        raise NotImplementedError

    def resolve_variable(self, variable_to_resolve, called_func_name, filename):
        # check in this file
        # check in imports
        # if in neither, skip

        # TODO how to handle parameters?
        # def func_a(some_class):
        #   some_class.func_b()
        # => resolve from where func_a is called and what is some_class

        # import import3 as import1
        # var0 = import1.Class1() # get imports of this file, find import1, resolve to import3, get classes and methods in file corresponding to import3, match class1, return code_obj_id , map var0 to code_obj_id
        # var1 = Class2 # resolve to this file Class2, return code_obj_id, map var1 to code_obj_id
        # var1.attr1 = var0.func_a() # resolve var0 by finding its assignment, resolve func_a, return code_obj_id, map var1.attr1 to code_obj_id
        variable_chain = variable_to_resolve.split(".")
        current_var = variable_chain[0]
        # check imports
        matches = self.import_finder.resolve_external_call(
            call=variable_to_resolve + "." + called_func_name,
            filename=filename,
            code_representer=self.code_representer,
        )
        if matches is None:
            result = self.resolve_variable_chain(
                variable_to_resolve=variable_to_resolve, filename=filename
            )
            if isinstance(result, CodeObject):
                candidates = [
                    code_obj
                    for code_obj in self.code_representer.objects.values()
                    if code_obj.parent_id == result.id
                ]
                return candidates
            return None
        elif len(matches) == 1:
            return matches
        elif len(matches) > 1:
            matches = [code_obj for code_obj in matches if code_obj.name == called_func_name]
            if len(matches) == 1:
                return matches
            else:
                raise NotImplementedError

    def resolve_variable_chain(self, variable_to_resolve, filename):
        tree = ast.parse(open(filename).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign):
                if isinstance(node, ast.AnnAssign):
                    targets = [node.target]
                else:  # ast.Assign
                    targets = node.targets
                for target in targets:
                    if not hasattr(target, "id"):
                        if not self.debug:
                            raise NotImplementedError
                        return None
                if variable_to_resolve in [target.id for target in targets]:
                    if isinstance(node.value, ast.Call):
                        if hasattr(node.value.func, "id"):
                            name = node.value.func.id
                        elif hasattr(node.value.func, "attr"):
                            name = node.value.func.attr
                        else:
                            raise NotImplementedError
                        matches = self.code_representer.get_by_filename_and_name(
                            filename=filename, name=name
                        )

                        if len(matches) == 1:
                            return matches[0]
                        elif len(matches) > 1:
                            raise NotImplementedError
                        elif len(matches) == 0:
                            # resolve imports
                            matches = self.import_finder.resolve_external_call(
                                call=name,
                                filename=filename,
                                code_representer=self.code_representer,
                            )
                            if matches is None:
                                return None
                            elif len(matches) > 1:
                                raise NotImplementedError
                            elif len(matches) == 1:
                                return matches[0]
                    else:
                        pass

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
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
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
                        class_obj.add_class_attribute(attribute=attr)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name):
                        annotation_location = node.annotation
                        while True:
                            if hasattr(annotation_location, "id"):
                                attr_type = annotation_location.id
                                break
                            elif hasattr(annotation_location, "value"):
                                annotation_location = annotation_location.value
                            elif hasattr(annotation_location, "left"):
                                annotation_location = annotation_location.left
                            else:
                                raise NotImplementedError
                        attr = {"name": node.target.id, "type": attr_type}
                        class_obj.add_class_attribute(attribute=attr)
                    else:
                        raise NotImplementedError
            for node in ast.walk(class_obj.ast):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if hasattr(target, "id"):
                            attr_name = target.id
                        elif hasattr(target, "attr"):
                            attr_name = target.attr
                        else:
                            continue  # TODO review
                        if not hasattr(target, "value"):
                            continue  # TODO review
                        if hasattr(target.value, "id"):
                            if target.value.id == "self":
                                attr = {"name": attr_name}
                                class_obj.add_instance_attribute(attribute=attr)
                elif isinstance(node, ast.AnnAssign):
                    if hasattr(node.target, "id"):
                        attr_name = node.target.id
                    elif hasattr(node.target, "attr"):
                        attr_name = node.target.attr
                    else:
                        raise NotImplementedError
                    if hasattr(node.target, "value") and hasattr(node.target.value, "id"):
                        if node.target.value.id == "self":
                            if hasattr(node.annotation, "id"):
                                attr_type = node.annotation.id
                            elif hasattr(node.annotation, "value") and hasattr(
                                node.annotation.value, "id"
                            ):
                                attr_type = node.annotation.value.id
                            else:
                                raise NotImplementedError
                            attr = {"name": attr_name, "type": attr_type}
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
            changed_module = extract_module_from_change_info(filename=change["filename"])
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
            module_obj.dev_comments = self.extract_dev_comments(module_obj)

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
