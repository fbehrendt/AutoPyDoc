import typing
from code_representation import (
    CodeObject,
    MethodObject,
    ClassObject,
    ModuleObject,
    CodeRepresenter,
)
from docstring_input_selector import DocstringInput

from repo_controller import UnknownCodeObjectError


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

    def enforce_indentation(self, string: str):
        string = string.split("\n")
        string = [" " * self.indentation_level + substring.lstrip() for substring in string]
        return "\n".join(string)

    def add_parantheses(self, string: str):
        # make sure, the docstring does not contain """
        string = string.replace('"""', "```")
        if "\n" in string:
            docstring = '"""\n' + string + '\n"""'
        else:
            docstring = '"""' + string + '"""'
        return docstring

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

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = self.description
        docstring = self.add_parantheses(docstring)
        return self.enforce_indentation(docstring)


class DocstringBuilderMethod(DocstringBuilder):
    """Docstring Builder for methods"""

    def __init__(self, indentation_level: int):
        """
        Helper class to create method docstrings using the builder pattern

        :param indentation_level: Indentation level of the docstring
        :type indentation_level: int

        :return: self
        :return type: DocstringBuilder
        """
        super().__init__(indentation_level=indentation_level)
        self.params = []
        self.exceptions = []

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

    def add_exception(self, exception_name: str, exception_description: str) -> typing.Self:
        """
        Add an exception

        :param exception_name: Exception name
        :type exception_name: str
        :param exception_description: description of the exception
        :type exception_description: str

        :return: self
        :return type: DocstringBuilder
        """
        self.exceptions.append({"name": exception_name, "description": exception_description})
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
        docstring = self.description
        if (
            len(self.params) > 0
            or not hasattr(self, "return_description")
            or len(self.exceptions) == 0
        ):
            docstring += "\n\n"
        for param in self.params:
            docstring += (
                " " * self.indentation_level + f":param {param['name']}: {param['description']}\n"
            )
            if "default" in param.keys():
                docstring += " " + f" Default is {param['default']}\n"
            docstring += " " * self.indentation_level + f":type {param['name']}: {param['type']}\n"
        if len(self.params) > 0 and hasattr(self, "return_type"):
            docstring += "\n"
        if hasattr(self, "return_type") and hasattr(self, "return_description"):
            docstring += " " * self.indentation_level + f":return: {self.return_description}\n"
            docstring += " " * self.indentation_level + f":rtype: {self.return_type}\n"

        if (len(self.params) > 0 or hasattr(self, "return_type")) and len(self.exceptions) > 0:
            docstring += "\n"
        for exception in self.exceptions:
            docstring += (
                " " * self.indentation_level
                + f":raises {exception['name']}: {exception['description']}\n"  # according to restructuredtext_lint, the extra \n is necessary
            )
        docstring = self.add_parantheses(docstring)
        docstring = self.enforce_indentation(docstring)
        return docstring


class DocstringBuilderClass(DocstringBuilder):
    """Docstring Builder for classes"""

    def __init__(self, indentation_level: int):
        """
        Helper class to create classes docstrings using the builder pattern

        :param indentation_level: Indentation level of the docstring
        :type indentation_level: int

        :return: self
        :return type: DocstringBuilder
        """
        super().__init__(indentation_level=indentation_level)
        self.class_attributes = []
        self.instance_attributes = []

    def add_class_attribute(
        self,
        class_attribute_name: str,
        class_attribute_description: str,
        class_attribute_type: str,
    ) -> typing.Self:
        """
        Add class attribute

        :param class_attribute_name: class attribute name
        :type class_attribute_name: str
        :param class_attribute_description: class attribute description
        :type class_attribute_description: str
        :param class_attribute_type: class attribute type
        :type class_attribute_type: str

        :return: self
        :return type: DocstringBuilder
        """
        class_attribute = {
            "name": class_attribute_name,
            "description": class_attribute_description,
            "type": class_attribute_type,
        }
        self.class_attributes.append(class_attribute)
        return self

    def add_instance_attribute(
        self,
        instance_attribute_name: str,
        instance_attribute_description: str,
        instance_attribute_type: str,
    ) -> typing.Self:
        """
        Add instance attribute

        :param instance_attribute_name: instance attribute name
        :type instance_attribute_name: str
        :param instance_attribute_description: instance attribute description
        :type instance_attribute_description: str
        :param instance_attribute_type: instance attribute type
        :type instance_attribute_type: str

        :return: self
        :return type: DocstringBuilder
        """
        instance_attribute = {
            "name": instance_attribute_name,
            "description": instance_attribute_description,
            "type": instance_attribute_type,
        }
        self.instance_attributes.append(instance_attribute)
        return self

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = self.description
        if len(self.class_attributes) > 0 or len(self.instance_attributes) > 0:
            docstring += "\n\n"

        for class_attribute in self.class_attributes:
            docstring += (
                " " * self.indentation_level
                + f":class attribute {class_attribute['name']}: {class_attribute['description']}\n"
            )
            docstring += (
                " " * self.indentation_level
                + f":type {class_attribute['name']}: {class_attribute['type']}\n"
            )
        if len(self.class_attributes) > 0 and len(self.instance_attributes) > 0:
            docstring += "\n"

        for instance_attribute in self.instance_attributes:
            docstring += (
                " " * self.indentation_level
                + f":instance attribute {instance_attribute['name']}: {instance_attribute['description']}\n"
            )
            docstring += (
                " " * self.indentation_level
                + f":type {instance_attribute['name']}: {instance_attribute['type']}\n"  # according to restructuredtext_lint, the extra \n is necessary
            )

        docstring = self.add_parantheses(docstring)
        return self.enforce_indentation(docstring)


class DocstringBuilderModule(DocstringBuilder):
    """Docstring Builder for modules"""

    def __init__(self, indentation_level: int):
        """
        Helper class to create module docstrings using the builder pattern

        :param indentation_level: Indentation level of the docstring
        :type indentation_level: int

        :return: self
        :return type: DocstringBuilder
        """
        super().__init__(indentation_level=indentation_level)
        self.exceptions = []

    def add_exception(self, exception_name: str, exception_description: str) -> typing.Self:
        """
        Add an exception

        :param exception_name: Exception name
        :type exception_name: str
        :param exception_description: description of the exception
        :type exception_description: str

        :return: self
        :return type: DocstringBuilder
        """
        self.exceptions.append({"name": exception_name, "description": exception_description})
        return self

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = self.description
        if len(self.exceptions) > 0:
            docstring += "\n\n"

        for exception in self.exceptions:
            docstring += (
                " " * self.indentation_level
                + f":raises {exception['name']}: {exception['description']}\n"
            )
        docstring = self.add_parantheses(docstring)
        return self.enforce_indentation(docstring)


def create_docstring(
    code_obj: CodeObject,
    docstring_input: DocstringInput,
    indentation_level: int,
    code_representer: CodeRepresenter,
    debug: bool = False,
) -> str:
    """
    Create a docstring for a CodeObject, using the GPT results

    :param code_obj: CodeObject in question
    :type code_obj: CodeObject
    :param docstring_input: docstring input dataclass
    :type docstring_input: DocstringInput
    :param indentation_level: indentation level the docstring should have
    :type indentation_level: int
    :param debug: toggle debug mode. Default False
    :type debug: bool

    :return: docstring for the CodeObject
    :return type: str

    """

    if isinstance(code_obj, MethodObject):
        docstring_builder = DocstringBuilderMethod(indentation_level=indentation_level)
        # description
        docstring_builder.add_description(docstring_input.description)
        # arguments
        for param in docstring_input.arguments.keys():
            if param == "self":  # skip self
                continue
            docstring_builder.add_param(
                param_name=param,
                param_type=docstring_input.argument_types[param],
                param_description=docstring_input.arguments[param],
            )
        # exceptions
        for exception in docstring_input.exceptions.keys():
            docstring_builder.add_exception(
                exception_name=exception,
                exception_description=docstring_input.exceptions[exception],
            )
        # return
        if code_obj.return_type is not None:
            docstring_builder.add_return(
                return_type=docstring_input.return_type,
                return_description=docstring_input.return_description,
            )
    elif isinstance(code_obj, ClassObject):
        docstring_builder = DocstringBuilderClass(indentation_level=indentation_level)
        # description
        docstring_builder.add_description(docstring_input.description)
        # class attributes
        for class_attribute_name in docstring_input.class_attributes.keys():
            docstring_builder.add_class_attribute(
                class_attribute_name=class_attribute_name,
                class_attribute_type=docstring_input.class_attribute_types[class_attribute_name],
                class_attribute_description=docstring_input.class_attributes[class_attribute_name],
            )
        # instance attributes
        for instance_attribute_name in docstring_input.instance_attributes.keys():
            docstring_builder.add_instance_attribute(
                instance_attribute_name=instance_attribute_name,
                instance_attribute_type=docstring_input.instance_attribute_types[
                    instance_attribute_name
                ],
                instance_attribute_description=docstring_input.instance_attributes[
                    instance_attribute_name
                ],
            )

    elif isinstance(code_obj, ModuleObject):
        docstring_builder = DocstringBuilderModule(indentation_level=indentation_level)
        # description
        docstring_builder.add_description(docstring_input.description)
        # exceptions
        for exception in docstring_input.exceptions.keys():
            docstring_builder.add_exception(
                exception_name=exception,
                exception_description=docstring_input.exceptions[exception],
            )
    else:
        raise UnknownCodeObjectError("Unknown code object")
    new_docstring = docstring_builder.build()
    return new_docstring
