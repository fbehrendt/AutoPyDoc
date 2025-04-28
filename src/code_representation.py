import os
import pathlib
import sys
from ast import AST
from dataclasses import dataclass, field, fields
from typing import List

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)
from gpt_input import (
    GptInputClassObject,
    GptInputCodeObject,
    GptInputMethodObject,
    GptInputModuleObject,
)


def frozen_field_support(cls):
    """
    Class decorator support dataclass field level freezing
    Support for idempotency i.e. if value is unchanged, no exception is raised

    Example:

    @frozen_field_support
    @dataclass
    class X:
        name: str = field(metadata={"frozen": True})

    x = X(name="whatever")
    x.name = "somethingelse" # FrozenField exception raised

    @raises Exception
    """

    def _setattr_(this, name, value):
        _field = cls.__dataclass_fields__.get(name, {})
        _meta = getattr(_field, "metadata", {})
        is_frozen = _meta.get("frozen", False)
        if not is_frozen:
            return super(cls, this).__setattr__(name, value)

        try:
            current_value = getattr(this, name)
            if value != current_value:
                raise Exception(f"Field '{name}' already has value= {current_value}")
        except AttributeError:  # NOQA TODO
            # dataclass not initialized yet...
            pass

        super(cls, this).__setattr__(name, value)

    setattr(cls, "__setattr__", _setattr_)
    return cls


@frozen_field_support
@dataclass(unsafe_hash=True)
class CodeObject:
    """
    Represent a piece of code like a module, class or method

    :param name: Name of the code piece. Usually the method or class name
    :type name: str
    :param filename: File where the code is located
    :type filename: str
    :param ast: Ast representation of the code
    :type ast: ast.AST
    :param docstring: Docstring of the code piece. Optional
    :type docstring: str
    :param code: Code of the code piece
    :type code: str
    """

    name: str = field(compare=True, hash=True, metadata={"frozen": True})
    filename: str = field(compare=True, hash=True, metadata={"frozen": True})
    ast: AST = field(compare=False, hash=False, metadata={"frozen": True})
    docstring: str | None = field(compare=False, hash=False)
    code: str | None = field(compare=True, hash=True, metadata={"frozen": False})
    parent_id: int | None = field(compare=True, hash=True, metadata={"frozen": True})

    def __post_init__(self):
        # self.__set_fields_frozen()
        self.id = hash(self)
        self.code_type = "code"
        self.class_ids = set()
        self.method_ids = set()
        self.called_methods = set()
        self.called_classes = set()
        self.called_by_methods = set()
        self.called_by_classes = set()
        self.called_by_modules = set()
        self.outdated = False
        self.is_updated = False
        self.send_to_gpt = False
        self.old_docstring = self.docstring

    def __set_fields_frozen(self):
        flds = fields(self)
        for fld in flds:
            if fld.metadata.get("frozen"):
                field_name = fld.name
                field_value = getattr(self, fld.name)
                setattr(self, f"_{fld.name}", field_value)

                def local_getter(self):
                    return getattr(self, f"_{field_name}")

                def frozen(name):
                    def local_setter(self, value):
                        raise RuntimeError(f"Field '{name}' is frozen!")

                    return local_setter

                setattr(self, field_name, property(local_getter, frozen(field_name)))

    def add_class_id(self, class_id: int):
        """
        Add a class id

        :param class_id: class id
        :type class_id: int
        """
        self.class_ids.add(class_id)

    def add_method_id(self, method_id: int):
        """
        Add a method id

        :param method_id: method id
        :type method_id: int
        """
        self.method_ids.add(method_id)

    def add_called_method(self, called_method_id: int):
        """
        Add a called method by its id

        :param called_method_id: id of the called method
        :type called_method_id: int
        """
        if called_method_id != self.id:
            self.called_methods.add(called_method_id)

    def add_called_class(self, called_class_id: int):
        """
        Add a called class by its id

        :param called_class_id: id of the called class
        :type called_class_id: int
        """
        if called_class_id != self.id:
            self.called_classes.add(called_class_id)

    def add_caller_method(self, caller_method_id: int):
        """
        Add a method calling this code object by its id

        :param caller_method_id: id of the calling method
        :type caller_method_id: int
        """
        self.called_by_methods.add(caller_method_id)

    def add_caller_class(self, caller_class_id: int):
        """
        Add a class calling this code object by its id

        :param caller_class_id: id of the calling class
        :type caller_class_id: int
        """
        self.called_by_classes.add(caller_class_id)

    def add_caller_module(self, caller_module_id: int):
        """
        Add a module calling this code object by its id

        :param caller_module_id: id of the calling module
        :type caller_module_id: int
        """
        self.called_by_modules.add(caller_module_id)

    def add_docstring(self, docstring: str):
        """
        Add the docstring of a code piece

        :param docstring: docstring
        :type docstring: str
        """
        self.docstring = docstring

    def update_docstring(self, new_docstring: str):
        """
        Update the docstring of a CodeObject

        :param new_docstring: the new docstring
        :type new_docstring: str
        """
        self.old_docstring = self.docstring
        self.docstring = new_docstring
        self.is_updated = True
        self.outdated = False

    def get_context(self) -> dict[str, list[int]]:
        """
        Get the context of a code piece

        :return: A dictionary of types of context, containing lists of code ids
        :return type: dict[str, list[int]]
        """
        return {
            "called_methods": self.called_methods,
            "called_classes": self.called_classes,
            "called_by_methods": self.called_by_methods,
            "called_by_classes": self.called_by_classes,
            "called_by_modules": self.called_by_modules,
        }

    def get_gpt_input(self, code_representer) -> GptInputCodeObject:
        """
        Create a gpt input object

        :return: GptInput object
        :return type: GptInputCodeObject
        """
        return GptInputCodeObject(
            id=self.id,
            code_type=self.code_type,
            name=self.name,
            docstring=self.docstring,
            code=self.code,
            context=self.get_context(),
            context_objects=code_representer.get_context_objects(self.id),
        )

    def get_sent_to_gpt(self) -> bool:
        return self.send_to_gpt

    def get_context_object(self):
        return ContextObject(
            id=self.id,
            name=self.name,
            code_type=self.code_type,
            docstring=self.docstring,
            code=self.code,
        )


@dataclass
class ContextObject:
    id: int = field(compare=True, hash=True)
    name: str = field(compare=True, hash=True)
    code_type: str = field(compare=True, hash=True)
    docstring: str = field(compare=True, hash=True)
    code: str = field(compare=True, hash=True)


@dataclass(unsafe_hash=True)
class ModuleObject(CodeObject):
    """
    Represent Module. Extends CodeObject

    :param name: Name of the code piece. Usually the method or class name
    :type name: str
    :param filename: File where the code is located
    :type filename: str
    :param code_type: The kind of code. E.g. method or class
    :type code_type: str
    :param ast: Ast representation of the code
    :type ast: ast.AST
    :param docstring: Docstring of the code piece. Optional
    :type docstring: str
    :param code: Code of the code piece
    :type code: str
    :param exceptions: Exceptions raised by the code piece. Optional
    :type exceptions: list(str)
    """

    exceptions: set[str] | None = field(default_factory=set, compare=False, hash=False)

    def __post_init__(self):
        super().__post_init__()
        self.code_type = "module"

    def add_exception(self, exception: str):
        """
        Add an exception that is raise by this code piece

        :param exception: The exception that is raised
        :type exception: str
        """
        self.exceptions.add(exception)

    def get_context(self) -> dict[str, list[int]]:
        """
        Get the context of a code piece

        :return: A dictionary of types of context, containing lists of code ids
        :return type: dict[str, list[int]]
        """
        return {
            "called_methods": self.called_methods,
            "called_classes": self.called_classes,
            "called_by_methods": self.called_by_methods,
            "called_by_classes": self.called_by_classes,
            "called_by_modules": self.called_by_modules,
            "class_ids": self.class_ids,
            "method_ids": self.method_ids,
        }

    def get_gpt_input(self, code_representer) -> GptInputModuleObject:
        """
        Create a gpt input object

        :return: GptInput object
        :return type: GptInputCodeObject
        """
        return GptInputModuleObject(
            id=self.id,
            code_type=self.code_type,
            name=self.name,
            docstring=self.docstring,
            code=self.code,
            context=self.get_context(),
            context_objects=code_representer.get_context_objects(self.id),
            exceptions=self.exceptions,
        )

    def get_context_object(self):
        return ModuleContextObject(
            id=self.id,
            name=self.name,
            code_type=self.code_type,
            docstring=self.docstring,
            code=self.code,
            exceptions=self.exceptions,
        )


@dataclass
class ModuleContextObject(ContextObject):
    exceptions: list[str] = field(compare=True, hash=True)


@dataclass(unsafe_hash=True)
class MethodObject(CodeObject):
    """
    Represent a method. Extends CodeObject

    :param name: Name of the code piece. Usually the method or class name
    :type name: str
    :param filename: File where the code is located
    :type filename: str
    :param ast: Ast representation of the code
    :type ast: ast.AST
    :param outer_method_id: id of the outer method, if exists. Optional
    :type outer_method_id: int|None
    :param outer_class_id: id of the outer class, if exists. Optional
    :type outer_class_id: int|None
    :param module_id: id of the module which this class is part of, if exists. Optional
    :type module_id: int|None
    :param docstring: Docstring of the code piece. Optional
    :type docstring: str
    :param code: Code of the code piece
    :type code: str
    :param arguments: Arguments of the code obj. Optional
    :type arguments: list
    :param return_type: Return type of the code piece. Optional
    :type return_type: str
    :param exceptions: Exceptions raised by the code piece. Optional
    :type exceptions: list[str]
    """

    arguments: list | None = field(default_factory=list, compare=False, hash=False)
    return_type: str | None = field(default=None, compare=False, hash=False)
    exceptions: set[str] | None = field(default_factory=set, compare=False, hash=False)
    outer_method_id: int | None = field(default=None, compare=True, hash=True)
    outer_class_id: int | None = field(default=None, compare=True, hash=True)
    module_id: int | None = field(default=None, compare=True, hash=True)

    def __post_init__(self):
        super().__post_init__()
        if self.arguments is None:
            self.arguments = []
        if self.exceptions is None:
            self.exceptions = set()
        self.missing_arg_types = set()
        self.missing_return_type = False
        self.code_type = "method"
        self.class_ids = set()
        self.method_ids = set()

    def add_argument(self, argument: dict[str, str]):
        """
        Add an argument

        :param argument: The argument to be added
        :type argument: dict[str, str]
        """
        self.arguments.append(argument)

    def add_missing_arg_type(self, arg_name: str):
        """
        Add an argument for which the return type is missing

        :param arg_name: Name of the argument for which type information is missing
        :type arg_name: str
        """
        self.missing_arg_types.add(arg_name)

    def add_exception(self, exception: str):
        """
        Add an exception that is raise by this code piece

        :param exception: The exception that is raised
        :type exception: str
        """
        self.exceptions.add(exception)

    def add_class_id(self, class_id: int):
        """
        Add a class id

        :param class_id: class id
        :type class_id: int
        """
        self.class_ids.add(class_id)

    def add_method_id(self, method_id: int):
        """
        Add a method id

        :param method_id: method id
        :type method_id: int
        """
        if method_id != self.id:
            self.method_ids.add(method_id)

    def get_missing_arg_types(self) -> set[str]:
        """
        Get a set of arguments, for which the return type is missing

        :return: set of arguments, for which the return type is missing
        :return type: set[str]
        """
        return self.missing_arg_types

    def get_arguments(self) -> list[dict] | None:
        if hasattr(self, "arguments"):
            return [
                argument for argument in self.arguments if argument["name"] != "self"
            ]  # ignore self
        return None

    def get_context(self) -> dict[str, list[int] | int]:
        """
        Get the ids of context code pieces

        :return: A dictionary of types of context, containing lists of code ids or a code id
        :return type: dict[str, list[int]|int]
        """
        result = super().get_context()
        result["outer_class_id"] = self.outer_class_id
        result["outer_method_id"] = self.outer_method_id
        result["module_id"] = self.module_id
        result["class_ids"] = self.class_ids
        result["method_ids"] = self.method_ids
        return result

    def get_gpt_input(self, code_representer) -> GptInputMethodObject:
        return GptInputMethodObject(
            id=self.id,
            code_type=self.code_type,
            name=self.name,
            docstring=self.docstring,
            code=self.code,
            context=self.get_context(),
            context_objects=code_representer.get_context_objects(self.id),
            exceptions=self.exceptions,
            parent_method_id=self.outer_method_id,
            parent_class_id=self.outer_class_id,
            parent_module_id=self.module_id,
            parameters=[param["name"] for param in code_representer.get_arguments(self.id)],
            missing_parameters=self.get_missing_arg_types(),
            return_missing=self.missing_return_type,
        )

    def get_context_object(self):
        return MethodContextObject(
            id=self.id,
            name=self.name,
            code_type=self.code_type,
            docstring=self.docstring,
            code=self.code,
            exceptions=self.exceptions,
            arguments=self.arguments,
        )


@dataclass
class MethodContextObject(ContextObject):
    exceptions: list[str] = field(compare=True, hash=True)
    arguments: list | None = field(compare=True, hash=True)


@dataclass(unsafe_hash=True)
class ClassObject(CodeObject):
    """
    Represent a class. Extends CodeObject

    :param name: Name of the code piece. Usually the method or class name
    :type name: str
    :param filename: File where the code is located
    :type filename: str
    :param ast: Ast representation of the code
    :type ast: ast.AST
    :param outer_method_id: id of the outer method, if exists. Optional
    :type outer_method_id: int|None
    :param outer_class_id: id of the outer class, if exists. Optional
    :type outer_class_id: int|None
    :param module_id: id of the module which this class is part of, if exists. Optional
    :type module_id: int|None
    :param inherited_from: id of the class this class inherits from. Optional
    :type inherited_from: int|None
    :param docstring: Docstring of the code piece. Optional
    :type docstring: str
    :param code: Code of the code piece
    :type code: str
    """

    outer_method_id: int | None = field(default=None, compare=True, hash=True)
    outer_class_id: int = field(default=None, compare=True, hash=True)
    module_id: int = field(default=None, compare=True, hash=True)
    inherited_from: int = field(default=None, compare=True, hash=True)
    exceptions: set[str] | None = field(default_factory=set, compare=False, hash=False)

    def __post_init__(self):
        super().__post_init__()
        self.code_type = "class"
        self.class_attributes = list()
        self.instance_attributes = list()

    def add_exception(self, exception: str):
        """
        Add an exception that is raise by this code piece

        :param exception: The exception that is raised
        :type exception: str
        """
        self.exceptions.add(exception)

    def add_class_attribute(self, attribute: dict[str, str]):
        """
        Add a class attribute

        :param attribute_name: attribute name
        :type attribute_name: str
        """
        if attribute["name"] not in [
            attr["name"] for attr in [*self.class_attributes, *self.instance_attributes]
        ]:
            self.class_attributes.append(attribute)

    def add_instance_attribute(self, attribute: dict[str, str]):
        """
        Add an instance attribute

        :param attribute_name: attribute name
        :type attribute_name: str
        """
        if attribute["name"] not in [
            attr["name"] for attr in [*self.class_attributes, *self.instance_attributes]
        ]:
            self.instance_attributes.append(attribute)

    def get_context(self) -> dict[str, list[int] | int]:
        """
        Get the ids of context code pieces

        :return: A dictionary of types of context, containing lists of code ids or a code id
        :return type: dict[str, list[int]|int]
        """
        result = super().get_context()
        result["outer_class_id"] = self.outer_class_id
        result["outer_method_id"] = self.outer_method_id
        result["module_id"] = self.module_id
        result["inherited_from"] = self.inherited_from
        result["class_ids"] = self.class_ids
        result["method_ids"] = self.method_ids
        return result

    def get_gpt_input(self, code_representer) -> GptInputClassObject:
        """
        Create a gpt input object

        :return: GptInput object
        :return type: GptInputClassObject
        """
        return GptInputClassObject(
            id=self.id,
            code_type=self.code_type,
            name=self.name,
            docstring=self.docstring,
            code=self.code,
            context=self.get_context(),
            context_objects=code_representer.get_context_objects(self.id),
            parent_method_id=self.outer_method_id,
            parent_class_id=self.outer_class_id,
            parent_module_id=self.module_id,
            inherited_from=self.inherited_from,
            class_ids=self.class_ids,
            method_ids=self.method_ids,
            class_attributes=self.class_attributes,
            instance_attributes=self.instance_attributes,
            missing_class_attribute_types=[
                attr["name"] for attr in self.class_attributes if "type" not in attr.keys()
            ],
            missing_instance_attributes_types=[
                attr["name"] for attr in self.instance_attributes if "type" not in attr.keys()
            ],
        )

    def get_context_object(self):
        return ClassContextObject(
            id=self.id,
            name=self.name,
            code_type=self.code_type,
            docstring=self.docstring,
            code=self.code,
            exceptions=self.exceptions,
            class_attributes=self.class_attributes,
            instance_attributes=self.instance_attributes,
        )


@dataclass
class ClassContextObject(ContextObject):
    exceptions: list[str] = field(compare=True, hash=True)
    class_attributes: list[str] = field(compare=True, hash=True)
    instance_attributes: list[str] = field(compare=True, hash=True)


class CodeRepresenter:
    """Represent all code pieces like modules, classes and methods"""

    def __init__(self):
        """Represent all code pieces like modules, classes and methods"""
        self.objects = {}

    def get(self, id: int) -> CodeObject:
        """
        Get a CodeObject by id

        :param id: id of the targeted CodeObject
        :type id: int

        :returns: CodeObject with the passed id
        :return type: CodeObject
        """
        if id in self.objects.keys():
            return self.objects[id]
        raise KeyError

    def add_code_obj(self, code_obj: CodeObject):
        """
        Add a CodeObject

        :param code_obj: CodeObject to be added
        :type code_object: CodeObject
        """
        if code_obj.id not in self.objects.keys():
            self.objects[code_obj.id] = code_obj

    def get_docstring(self, code_obj_id: int) -> str | None:
        """
        Get the docstring of a CodeObject, if exists

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: docstring of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "docstring"):
            return self.objects[code_obj_id].docstring
        return None

    def get_code(self, code_obj_id: int) -> str | None:
        """
        Get the code of a CodeObject, if exists

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: code of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "code"):
            return self.objects[code_obj_id].code
        return None

    def get_arguments(self, code_obj_id: int) -> list[dict[str, str]] | None:
        """
        Get the arguments of a CodeObject, if exists. Do not return self as an argument

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: arguments of the CodeObject or None
        :return type: list[dict[str, str]] | None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "arguments"):
            return [
                argument
                for argument in self.objects[code_obj_id].arguments
                if argument["name"] != "self"
            ]  # ignore self
        return None

    def get_return_type(self, code_obj_id: int) -> str | None:
        """
        Get the return type of a CodeObject, if exists

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: return type of the CodeObject or None
        :return type: str|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "return_type"):
            return self.objects[code_obj_id].return_type
        return None

    def get_exceptions(self, code_obj_id: int) -> list[str] | None:
        """
        Get the exceptions of a CodeObject, if exists

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: exceptions raised by the CodeObject or None
        :return type: list[str]|None
        """
        if code_obj_id in self.objects.keys() and hasattr(self.objects[code_obj_id], "exceptions"):
            return self.objects[code_obj_id].exceptions
        return None

    def get_missing_arg_types(self, code_obj_id: int) -> list[str] | bool:
        """
        Get the names of arguments where type information is missing of a CodeObject, if exists

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: names of arguments where type information is missing or False
        :return type: list[str]|bool
        """
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.get_missing_arg_types()

    def return_type_missing(self, code_obj_id: int) -> bool:
        """
        Return if the return type of the CodeObject is missing

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: True if return type is missing, else False
        :return type: bool
        """
        code_obj = self.objects[code_obj_id]
        if not isinstance(code_obj, MethodObject):
            return False
        return code_obj.missing_return_type

    def get_args_types_exceptions(self, code_obj_id: int) -> dict[str, list[str] | str | bool]:
        """
        Get information about arguments, return and exceptions of a CodeObject

        :param code_obj_id: id of the CodeObject
        :type code_obj_id: int

        :return: information about arguments, return and exceptions
        :return type: dict[str, list[str]|str|bool]
        """
        return {
            "arguments": self.get_arguments(code_obj_id=code_obj_id),
            "return_type": self.get_return_type(code_obj_id=code_obj_id),
            "exceptions": self.get_exceptions(code_obj_id=code_obj_id),
            "missing_arg_types": self.get_missing_arg_types(code_obj_id=code_obj_id),
            "return_type_missing": self.return_type_missing(code_obj_id=code_obj_id),
        }

    def get_by_filename(self, filename: str) -> list[CodeObject]:
        """
        Get CodeObjects by filename

        :param filename: filename for which CodeObjects should be returned
        :type filename: str

        :return: list of matching CodeObjecs
        :return type: list[CodeObject]
        """
        if not filename.endswith(".py"):
            filename += ".py"
        matches = []
        for object in self.objects.values():
            if object.filename == filename:
                matches.append(object)
            else:
                # TODO case different separators
                from pathlib import Path

                if str(os.path.join(*Path(object.filename).parts)) == str(
                    os.path.join(*Path(filename).parts)
                ):
                    matches.append(object)
        return matches

    def get_by_type_filename_and_code(self, code_type: str, filename: str, code: str) -> CodeObject:
        """
        Get CodeObjects by filename

        :param code_type: type of the CodeObject (module, class, method)
        :type code_type: str
        :param filename: filename for which CodeObjects should be returned
        :type filename: str
        :param code: Code of the code object that should be returned
        :type code: str

        :return: list of matching CodeObjecs
        :return type: list[CodeObject]
        """
        candidates = self.get_by_filename(filename=filename)
        matches = []
        for candidate in candidates:
            if (
                candidate.code_type == code_type
                and candidate.code.strip()
                in code.strip()  # in instead of == because the extracted code might include additional comments
            ):
                matches.append(candidate)
        if len(matches) > 1:
            raise Exception("More than one match")
        if len(matches) == 0:
            raise Exception("No matches")
        return matches[0]

    def get_by_filename_and_name(self, filename: str, name: str) -> CodeObject:
        """
        Get CodeObjects by filename

        :param filename: filename for which CodeObjects should be returned
        :type filename: str
        :param name: name of the class, module, or method
        :type name: str

        :return: list of matching CodeObjecs
        :return type: list[CodeObject]
        """
        candidates = self.get_by_filename(filename=filename)
        matches = []
        for candidate in candidates:
            if (
                candidate.name == name  # TODO ambiguous
            ):
                matches.append(candidate)
        # if len(matches) > 1:
        #    raise Exception("More than one match")
        # if len(matches) == 0:
        #    raise Exception("No matches")
        # return matches[0]
        return matches

    def get_context_docstrings(self, code_obj_id: int) -> dict[int, str]:
        """
        Get the docstrings of context CodeObjects as a dict of CodeObject id to docstring

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: dictionary of CodeObject ids to docstrings
        :return type: dict[int, str]
        """
        code_obj = self.get(code_obj_id)
        code_obj_context = code_obj.get_context()
        keys = set()
        for sub_list in code_obj_context.values():
            if isinstance(sub_list, set):
                keys.update(sub_list)
        if isinstance(code_obj, MethodObject) or isinstance(code_obj, ClassObject):
            keys.add(code_obj.outer_class_id)
            keys.add(code_obj.module_id)
        if isinstance(code_obj, ClassObject):
            keys.add(code_obj.inherited_from)
        result = {}
        for key in keys:
            if key is None:
                continue
            code_obj_2 = self.get(key)
            if hasattr(code_obj_2, "docstring"):
                result[key] = code_obj_2.docstring
            else:
                result[key] = code_obj_2.code
        return result

    def get_context_objects(self, code_obj_id: int) -> ContextObject:
        """
        Get ContextObjects as a dict of CodeObject id to ContextObject

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: dictionary of CodeObject ids to ContextObject
        :return type: dict[int, ContextObject]
        """
        code_obj = self.get(code_obj_id)
        code_obj_context = code_obj.get_context()
        keys = set()
        for sub_list in code_obj_context.values():
            if isinstance(sub_list, set):
                keys.update(sub_list)
        if isinstance(code_obj, MethodObject) or isinstance(code_obj, ClassObject):
            keys.add(code_obj.outer_class_id)
            keys.add(code_obj.module_id)
        if isinstance(code_obj, ClassObject):
            keys.add(code_obj.inherited_from)
        result = {}
        for key in keys:
            if key is None:
                continue
            code_obj_2 = self.get(key)
            result[key] = code_obj_2.get_context_object()
        return result

    def depends_on_outdated_code(self, code_obj_id: int) -> bool:
        """
        Return if the CodeObject depends on other CodeObjects. Relevant for the order of docstring generation

        :param code_obj_id: CodeObject id
        :type code_obj_id: int

        :return: True if the CodeObject depends on other CodeObjects
        :return type: bool
        """
        code_obj = self.get(code_obj_id)
        for code_id in code_obj.called_classes:
            if self.get(code_id).outdated:
                return True
        for code_id in code_obj.called_methods:
            if self.get(code_id).outdated:
                return True
        if isinstance(code_obj, ClassObject) or isinstance(code_obj, ModuleObject):
            for class_id in code_obj.class_ids:
                if self.get(class_id).outdated:
                    return True
        if isinstance(code_obj, ClassObject):
            for method_id in code_obj.method_ids:
                if self.get(method_id).outdated:
                    return True
        return False

    def update_docstring(self, code_obj_id: int, new_docstring: str):
        """
        Update the docstring of a CodeObject

        :param code_obj_id: CodeObject id
        :type code_obj_id: int
        :param new_docstring: the new docstring
        :type new_docstring: str
        """
        code_obj = self.get(code_obj_id)
        code_obj.old_docstring = code_obj.docstring
        code_obj.docstring = new_docstring
        code_obj.is_updated = True
        code_obj.outdated = False

    def get_outdated_ids(self) -> list[int]:
        return [code_obj.id for code_obj in self.objects.values() if self.is_outdated(code_obj.id)]

    def get_sent_to_gpt_ids(self) -> list[int]:
        return [code_obj.id for code_obj in self.objects.values() if code_obj.get_sent_to_gpt()]

    def generate_next_batch(self, ignore_dependencies=False) -> list[GptInputCodeObject]:
        ids = [
            id
            for id in self.get_outdated_ids()
            if (ignore_dependencies)
            or not self.depends_on_outdated_code(id)
            and not self.get(id).send_to_gpt
        ]
        batch: List[GptInputCodeObject] = []
        for id in ids:
            code_obj = self.get(id)
            code_obj.send_to_gpt = True
            batch.append(code_obj.get_gpt_input(code_representer=self))
        return batch

    def get_code_objects(self) -> list[CodeObject]:
        return list(self.objects.values())

    def get_modules(self) -> list[ModuleObject]:
        return [
            code_obj
            for code_obj in list(self.objects.values())
            if isinstance(code_obj, ModuleObject)
        ]

    def get_classes(self) -> list[ClassObject]:
        return [
            code_obj
            for code_obj in list(self.objects.values())
            if isinstance(code_obj, ClassObject)
        ]

    def get_methods(self) -> list[MethodObject]:
        return [
            code_obj
            for code_obj in list(self.objects.values())
            if isinstance(code_obj, MethodObject)
        ]

    def get_changed_files(self) -> list[str]:
        changed_files = set()
        for filename in [
            code_obj.filename for code_obj in self.objects.values() if code_obj.is_updated
        ]:
            changed_files.add(filename)
        return list(changed_files)

    def set_outdated(self, code_obj_id: int):
        code_obj = self.get(code_obj_id)
        code_obj.outdated = True
        if isinstance(code_obj, MethodObject) or isinstance(code_obj, ClassObject):
            if code_obj.outer_class_id is not None:
                self.set_outdated(code_obj.outer_class_id)
            if code_obj.module_id is not None:
                module_obj = self.get(code_obj.module_id)
                module_obj.outdated = True

    def is_outdated(self, code_obj_id):
        code_obj = self.get(code_obj_id)
        if code_obj.outdated:
            return True
        for dependency_id in [*code_obj.called_methods, *code_obj.called_classes]:
            dependency_obj = self.get(dependency_id)
            if self.is_outdated(dependency_obj.id) and not dependency_obj.is_updated:
                return True
        if isinstance(code_obj, ClassObject):
            for dependency_id in [
                *code_obj.class_ids,
                *code_obj.method_ids,
                code_obj.inherited_from,
            ]:
                if dependency_id is None:
                    continue

                dependency_obj = self.get(dependency_id)
                if self.is_outdated(dependency_obj.id) and not dependency_obj.is_updated:
                    return True
        if isinstance(code_obj, ModuleObject):
            for dependency_id in [*code_obj.class_ids, *code_obj.method_ids]:
                dependency_obj = self.get(dependency_id)
                if self.is_outdated(dependency_obj.id) and not dependency_obj.is_updated:
                    return True
