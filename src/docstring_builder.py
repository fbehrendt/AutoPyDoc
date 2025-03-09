import typing
from code_representation import CodeObject, MethodObject, ClassObject, ModuleObject


class DocstringBuilder:
    """Docstring Builder"""

    def __init__(self, indentation_level: int):
        """
        Helper class to create docstrings using the builder pattern

        :param indentation_level: Indentation level of the docstring
        :type indentation_level: int

        :return: self
        :return type: DocstringBuilder
        """
        self.indentation_level = indentation_level
        self.params = []
        self.exceptions = []

    def add_description(self, description: str) -> typing.Self:
        """
        Add description section

        :param description: description without indentation
        :type description: str

        :return: self
        :return type: DocstringBuilder
        """
        self.description = description
        return self

    def add_param(
        self,
        param_name: str,
        param_description: str,
        param_type: str,
        param_default: str | None = None,
    ) -> typing.Self:
        """
        Add a parameter, including name, description, type and optionally its default value

        :param param_name: parameter name
        :type param_name: str
        :param param_description: description of the parameter
        :type param_description: str
        :param param_type: type of the parameter
        :type param_type: str
        :param param_default: default of the parameter if exists. Optional
        :type param_default: str|None

        :return: self
        :return type: DocstringBuilder
        """
        param = {
            "name": param_name,
            "description": param_description,
            "type": param_type,
        }
        if param_default is not None:
            param["default"] = param_default
        self.params.append(param)
        return self

    def add_exception(
        self, exception_name: str, exception_description: str
    ) -> typing.Self:
        """
        Add an exception

        :param exception_name: Exception name
        :type exception_name: str
        :param exception_description: description of the exception
        :type exception_description: str

        :return: self
        :return type: DocstringBuilder
        """
        self.exceptions.append(
            {"name": exception_name, "description": exception_description}
        )
        return self

    def add_return(self, return_description: str, return_type: str) -> typing.Self:
        """
        Add return information

        :param return_description: return description
        :type return_description: str
        :param return_type: return type
        :type return_type: str

        :return: self
        :return type: DocstringBuilder
        """
        self.return_description = return_description
        self.return_type = return_type
        return self

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = " " * self.indentation_level + '"""'
        docstring += self.description + "\n"
        if len(self.params) > 0:
            docstring += "\n"
        for param in self.params:
            docstring += (
                " " * self.indentation_level
                + f":param {param['name']}: {param['description']}\n"
            )
            if "default" in param.keys():
                docstring += " " + f" Default is {param['default']}\n"
            docstring += (
                " " * self.indentation_level
                + f":type {param['name']}: {param['type']}\n"
            )
        if len(self.params) > 0:
            docstring += "\n"
        if hasattr(self, "return_type") and hasattr(self, "return_description"):
            docstring += (
                " " * self.indentation_level + f":return: {self.return_description}\n"
            )
            docstring += (
                " " * self.indentation_level + f":rtype: {self.return_type}\n\n"
            )
        for exception in self.exceptions:
            docstring += (
                " " * self.indentation_level
                + f":raises {exception['name']}: {exception['description']}\n"
            )
        if len(self.exceptions) > 0:
            docstring += "\n"
        docstring += " " * self.indentation_level + '"""'
        return docstring


def create_docstring(
    code_obj: CodeObject, result: dict, indentation_level: int, debug: bool = False
) -> str:
    """
    Create a docstring for a CodeObject, using the GPT results

    :param code_obj: CodeObject in question
    :type code_obj: CodeObject
    :param result: the GPT results
    :type result: dict
    :param indentation_level: indentation level the docstring should have
    :type indentation_level: int
    :param debug: toggle debug mode. Default False
    :type debug: bool

    :return: docstring for the CodeObject
    :return type: str

    :raises NotImplementedError: raised when trying to access functionality that is not yet implemented
    """
    docstring_builder = DocstringBuilder(indentation_level=indentation_level)
    if not debug:
        raise NotImplementedError
    docstring_builder.add_description(result.description)  # TODO
    if isinstance(code_obj, MethodObject):
        for param in code_obj.arguments:
            if param["name"] == "self":  # skip self
                continue
            if param["name"] in result.parameter_types.keys():
                param_type = result.parameter_types[param["name"]]
            else:
                param_type = param["type"]
            if "default" in param.keys():
                docstring_builder.add_param(
                    param_name=param["name"],
                    param_type=param_type,
                    param_default=param["default"],
                    param_description=result.parameter_descriptions[param["name"]],
                )  # TODO
            else:
                docstring_builder.add_param(
                    param_name=param["name"],
                    param_type=param_type,
                    param_description=result.parameter_descriptions[param["name"]],
                )  # TODO
        for exception, exception_description in result.exception_descriptions.items():
            docstring_builder.add_exception(
                exception_name=exception, exception_description=exception_description
            )  # TODO
        if not code_obj.missing_return_type and code_obj.return_type is not None:
            if result.return_missing:
                return_type = result.return_type
            else:
                return_type = code_obj.return_type
            docstring_builder.add_return(
                return_type=return_type, return_description=result.return_description
            )  # TODO
    elif isinstance(code_obj, ClassObject):
        if not debug:
            raise NotImplementedError  # TODO class and instance attributes, methods, sub classes
        pass
    elif isinstance(code_obj, ModuleObject):
        if not debug:
            raise NotImplementedError  # TODO classes and methods, exceptions when run as script
        pass
    else:
        raise NotImplementedError  # TODO
    return docstring_builder.build()
