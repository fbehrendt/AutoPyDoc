import typing
from code_representation import (
    CodeObject,
    MethodObject,
    ClassObject,
    ModuleObject,
    CodeRepresenter,
)


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
        docstring = " " * self.indentation_level + '"""\n'
        docstring += " " * self.indentation_level + self.description + "\n"
        docstring += " " * self.indentation_level + '"""'
        return docstring


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
        docstring = " " * self.indentation_level + '"""\n'
        docstring += " " * self.indentation_level + self.description
        if (
            len(self.params) == 0
            and not hasattr(self, "return_description")
            and len(self.exceptions) == 0
        ):
            if "\n" in self.description:
                docstring += "\n"
            docstring += '"""'
            return docstring
        docstring += "\n\n"
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
            docstring += "\n"

        for exception in self.exceptions:
            docstring += (
                " " * self.indentation_level
                + f":raises {exception['name']}: {exception['description']}\n"
            )
        if len(self.exceptions) == 0:
            docstring = docstring[:-1]
        docstring += " " * self.indentation_level + '"""'
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
        class_attribute = {
            "name": instance_attribute_name,
            "description": instance_attribute_description,
            "type": instance_attribute_type,
        }
        self.instance_attributes.append(class_attribute)
        return self

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = " " * self.indentation_level + '"""\n'
        docstring += " " * self.indentation_level + self.description
        if len(self.class_attributes) == 0 and len(self.instance_attributes) == 0:
            if "\n" in self.description:
                docstring += "\n"
            docstring += '"""'
            return docstring
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
                + f":type {instance_attribute['name']}: {instance_attribute['type']}\n"
            )

        docstring += " " * self.indentation_level + '"""'
        return docstring


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

    def build(self) -> str:
        """
        Build the docstring and return it

        :return: docstring
        :return type: str
        """
        docstring = " " * self.indentation_level + '"""\n'
        docstring += " " * self.indentation_level + self.description
        if len(self.exceptions) == 0:
            if "\n" in self.description:
                docstring += "\n"
            docstring += '"""'
            return docstring
        docstring += "\n\n"

        for exception in self.exceptions:
            docstring += (
                " " * self.indentation_level
                + f":raises {exception['name']}: {exception['description']}\n"
            )
        docstring += " " * self.indentation_level + '"""'
        return docstring


def create_docstring(
    code_obj: CodeObject,
    result: dict,
    indentation_level: int,
    code_representer: CodeRepresenter,
    debug: bool = False,
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

    def generate_parent_chain(code_obj, code_representer):
        parent_chain = code_obj.name
        code_obj_2 = code_obj
        while code_obj_2.parent_id is not None:
            code_obj_2 = code_representer.get(code_obj_2.parent_id)
            parent_chain = code_obj_2.name + "->" + parent_chain
        return parent_chain

    pr_notes = []
    if isinstance(code_obj, MethodObject):
        docstring_builder = DocstringBuilderMethod(indentation_level=indentation_level)
        if isinstance(result.description, bool) and not result.description:
            pr_notes.append(
                f"Please manully add a description for method {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
            )
            description = "<failed to generate>"
        else:
            description = result.description
        docstring_builder.add_description(description)
        for param in code_obj.arguments:
            if param["name"] == "self":  # skip self
                continue
            if (
                isinstance(result.parameter_descriptions[param["name"]], bool)
                and not result.parameter_descriptions[param["name"]]
            ):
                pr_notes.append(
                    f"Please manully add a description for parameter {param['name']} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                param_description = "<failed to generate>"
            else:
                param_description = result.parameter_descriptions[param["name"]]
            if hasattr(param, "type"):
                param_type = param["type"]
            else:
                if (
                    isinstance(result.parameter_types[param["name"]], bool)
                    and not result.parameter_types[param["name"]]
                ):
                    pr_notes.append(
                        f"Unknown type for param {param['name']} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                    )
                    param_type = "<unknown>"
                else:
                    param_type = result.parameter_types[param["name"]]
            if "default" in param.keys():
                docstring_builder.add_param(
                    param_name=param["name"],
                    param_type=param_type,
                    param_default=param["default"],
                    param_description=param_description,
                )
            else:
                docstring_builder.add_param(
                    param_name=param["name"],
                    param_type=param_type,
                    param_description=param_description,
                )
        for exception, exception_description in result.exception_descriptions.items():
            if isinstance(exception_description, bool) and not exception_description:
                pr_notes.append(
                    f"Please manully add a description for exception {exception} in method {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                exception_description = "<failed to generate>"
            docstring_builder.add_exception(
                exception_name=exception, exception_description=exception_description
            )
        if code_obj.return_type is not None:
            if (
                isinstance(result.return_description, bool)
                and not result.return_description
            ):
                pr_notes.append(
                    f"Please manully add a return description in method {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                return_description = "<failed to generate>"
            else:
                return_description = result.return_type
            if not code_obj.missing_return_type:
                return_type = code_obj.return_type
            else:
                if isinstance(result.return_type, bool) and not result.return_type:
                    pr_notes.append(
                        f"Please manully add a return type in method {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                    )
                    return_type = "<failed to generate>"
                else:
                    return_type = result.return_type
            docstring_builder.add_return(
                return_type=return_type, return_description=return_description
            )
    elif isinstance(code_obj, ClassObject):
        docstring_builder = DocstringBuilderClass(indentation_level=indentation_level)
        if isinstance(result.description, bool) and not result.description:
            pr_notes.append(
                f"Please manully add a description for class {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
            )
            description = "<failed to generate>"
        else:
            description = result.description
        docstring_builder.add_description(description)
        for class_attribute_name in result.class_attribute_descriptions.keys():
            if (
                isinstance(
                    result.class_attribute_descriptions[class_attribute_name], bool
                )
                and not result.class_attribute_descriptions[class_attribute_name]
            ):
                pr_notes.append(
                    f"Please manully add a description for class attribute {class_attribute_name} for class {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                class_attribute_description = "<failed to generate>"
            else:
                class_attribute_description = result.class_attribute_descriptions[
                    class_attribute_name
                ]
            class_attr_annotation = [
                attr["type"]
                for attr in code_obj.class_attributes
                if attr["name"] == class_attribute_name and "type" in attr.keys()
            ][0]
            if len(class_attr_annotation) > 0:
                attr_type = class_attr_annotation
            else:
                if (
                    isinstance(result.class_attribute_types[class_attribute_name], bool)
                    and not result.class_attribute_types[class_attribute_name]
                ):
                    pr_notes.append(
                        f"Unknown type for class attribute {class_attribute_name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                    )
                    attr_type = "<unknown>"
                else:
                    attr_type = result.class_attribute_types[class_attribute_name]
            docstring_builder.add_class_attribute(
                class_attribute_name=class_attribute_name,
                class_attribute_type=attr_type,
                class_attribute_description=class_attribute_description,
            )
        for instance_attribute_name in result.instance_attribute_descriptions.keys():
            if (
                isinstance(
                    result.instance_attribute_descriptions[instance_attribute_name],
                    bool,
                )
                and not result.instance_attribute_descriptions[instance_attribute_name]
            ):
                pr_notes.append(
                    f"Please manully add a description for instance attribute {instance_attribute_name} for class {code_obj.name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                instance_attribute_description = "<failed to generate>"
            else:
                instance_attribute_description = result.instance_attribute_descriptions[
                    instance_attribute_name
                ]
            class_attr_annotation = [
                attr["type"]
                for attr in code_obj.instance_attributes
                if attr["name"] == instance_attribute_name and "type" in attr.keys()
            ]
            if len(class_attr_annotation) > 0:
                attr_type = class_attr_annotation[0]
            else:
                if (
                    isinstance(
                        result.instance_attribute_types[instance_attribute_name], bool
                    )
                    and not result.instance_attribute_types[instance_attribute_name]
                ):
                    pr_notes.append(
                        f"Unknown type for class attribute {instance_attribute_name} in {code_obj.filename}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                    )
                    attr_type = "<unknown>"
                else:
                    attr_type = result.instance_attribute_types[instance_attribute_name]
            docstring_builder.add_instance_attribute(
                instance_attribute_name=instance_attribute_name,
                instance_attribute_type=attr_type,
                instance_attribute_description=instance_attribute_description,
            )

    elif isinstance(code_obj, ModuleObject):
        docstring_builder = DocstringBuilderModule(indentation_level=indentation_level)
        if isinstance(result.description, bool) and not result.description:
            pr_notes.append(
                f"Please manully add a description for module {code_obj.name} in {code_obj.filename}"
            )
            description = "<failed to generate>"
        else:
            description = result.description
        docstring_builder.add_description(description)
        for exception, exception_description in result.exception_descriptions.items():
            if isinstance(exception_description, bool) and not exception_description:
                pr_notes.append(
                    f"Please manully add a description for exception {exception} in module {code_obj.name} in {code_obj.filename}"
                )
                exception_description = "<failed to generate>"
            docstring_builder.add_exception(
                exception_name=exception, exception_description=exception_description
            )
    else:
        raise NotImplementedError
    return docstring_builder.build(), pr_notes
