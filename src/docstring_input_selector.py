from dataclasses import dataclass, field


@dataclass
class DocstringInput:
    id: int = field(compare=True, hash=True)
    description: str = ""


@dataclass
class DocstringInputMethod:
    id: int = field(compare=True, hash=True)
    description: str = ""
    arguments: dict = field(default_factory=dict, compare=False, hash=False)
    argument_types: dict = field(default_factory=dict, compare=False, hash=False)
    return_description: str | None = field(default=None, compare=False, hash=False)
    return_type: str | None = field(default=None, compare=False, hash=False)
    exceptions: dict = field(default_factory=dict, compare=False, hash=False)


@dataclass
class DocstringInputClass:
    id: int = field(compare=True, hash=True)
    description: str = ""
    class_attributes: dict = field(default_factory=dict, compare=False, hash=False)
    class_attribute_types: dict = field(default_factory=dict, compare=False, hash=False)
    instance_attributes: dict = field(default_factory=dict, compare=False, hash=False)
    instance_attribute_types: dict = field(
        default_factory=dict, compare=False, hash=False
    )


@dataclass
class DocstringInputModule:
    id: int = field(compare=True, hash=True)
    description: str = ""
    exceptions: dict = field(default_factory=dict, compare=False, hash=False)


# TODO The super class DocstringInputSelector caused nothing but problems and was hence removed


class DocstringInputSelectorMethod:
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        self.code_obj = code_obj
        self.gpt_result = gpt_result
        self.developer_docstring_changes = developer_docstring_changes
        self.docstring_input = DocstringInputMethod(id=code_obj.id)
        self.__select_description()
        self.__select_parameters()
        self.__select_exceptions()
        self.__select_return_info()

    def get_result(self):
        return self.docstring_input

    def __select_description(self):
        # description
        for developer_docstring_change in self.developer_docstring_changes:
            if (
                developer_docstring_change["place"] == "description"
                and developer_docstring_change["change"] == "description"
                and len(developer_docstring_change["new"]) > 10
            ):
                self.docstring_input.description = developer_docstring_change["new"]
                break
        if len(self.docstring_input.description) < 10:
            self.docstring_input.description = self.gpt_result.description

    def __select_parameters(self):
        # parameters
        for argument in self.code_obj.arguments:
            if argument["name"] == "self":
                continue
            self.docstring_input.arguments[argument["name"]] = (
                self.gpt_result.parameter_descriptions[argument["name"]]
            )
            if "type" in argument.keys():
                self.docstring_input.argument_types[argument["name"]] = argument["type"]
            else:
                self.docstring_input.argument_types[argument["name"]] = (
                    self.gpt_result.parameter_types[argument["name"]]
                )
            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == argument["name"]
                ):
                    if developer_docstring_change["change"] == "added":
                        self.docstring_input.arguments[argument["name"]] = (
                            developer_docstring_change["description"]
                        )
                        self.docstring_input.argument_types[argument["name"]] = (
                            developer_docstring_change["type"]
                        )
                    elif developer_docstring_change["change"] == "type":
                        self.docstring_input.argument_types[argument["name"]] = (
                            developer_docstring_change["new"]
                        )
                    elif developer_docstring_change["change"] == "description":
                        self.docstring_input.arguments[argument["name"]] = (
                            developer_docstring_change["new"]
                        )
                    break

    def __select_return_info(self):
        if self.code_obj.return_type is None and self.code_obj.missing_return_type:
            self.docstring_input.return_type = self.gpt_result.return_type
        else:
            self.docstring_input.return_type = self.code_obj.return_type
        self.docstring_input.return_description = self.gpt_result.return_description

        for developer_docstring_change in self.developer_docstring_changes:
            if developer_docstring_change["place"] == "return":
                if developer_docstring_change["change"] == "added":
                    self.docstring_input.return_type = developer_docstring_change[
                        "type"
                    ]
                    self.docstring_input.return_description = (
                        developer_docstring_change["description"]
                    )
                elif developer_docstring_change["change"] == "type":
                    self.docstring_input.return_type = developer_docstring_change["new"]
                elif developer_docstring_change["change"] == "description":
                    self.docstring_input.return_description = (
                        developer_docstring_change["new"]
                    )
                break

    def __select_exceptions(self):
        # exceptions
        for exception_name in self.code_obj.exceptions:
            self.docstring_input.exceptions[exception_name] = (
                self.gpt_result.exception_descriptions[exception_name]
            )
            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "exceptions"
                    and developer_docstring_change["name"] == exception_name
                ):
                    if developer_docstring_change["change"] == "added":
                        self.docstring_input.exceptions[exception_name] = (
                            developer_docstring_change["description"]
                        )
                    if developer_docstring_change["change"] == "description":
                        self.docstring_input.exceptions[exception_name] = (
                            developer_docstring_change["new"]
                        )
                    break


class DocstringInputSelectorModule:
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        self.code_obj = code_obj
        self.gpt_result = gpt_result
        self.developer_docstring_changes = developer_docstring_changes
        self.docstring_input = DocstringInputModule(id=code_obj.id)
        self.__select_description()
        self.__select_exceptions()

    def get_result(self):
        return self.docstring_input

    def __select_description(self):
        # description
        for developer_docstring_change in self.developer_docstring_changes:
            if (
                developer_docstring_change["place"] == "description"
                and developer_docstring_change["change"] == "description"
                and len(developer_docstring_change["new"]) > 10
            ):
                self.docstring_input.description = developer_docstring_change["new"]
                break
        if len(self.docstring_input.description) < 10:
            self.docstring_input.description = self.gpt_result.description

    def __select_exceptions(self):
        # exceptions
        for exception_name in self.code_obj.exceptions:
            self.docstring_input.exceptions[exception_name] = (
                self.gpt_result.exception_descriptions[exception_name]
            )
            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "exceptions"
                    and developer_docstring_change["name"] == exception_name
                ):
                    if developer_docstring_change["change"] == "added":
                        self.docstring_input.exceptions[exception_name] = (
                            developer_docstring_change["description"]
                        )
                    elif developer_docstring_change["change"] == "description":
                        self.docstring_input.exceptions[exception_name] = (
                            developer_docstring_change["new"]
                        )
                    break


class DocstringInputSelectorClass:
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        self.code_obj = code_obj
        self.gpt_result = gpt_result
        self.developer_docstring_changes = developer_docstring_changes
        self.docstring_input = DocstringInputClass(id=code_obj.id)
        self.__select_description()
        self.__select_class_attributes()
        self.__select_instance_attributes()

    def get_result(self):
        return self.docstring_input

    def __select_description(self):
        # description
        for developer_docstring_change in self.developer_docstring_changes:
            if (
                developer_docstring_change["place"] == "description"
                and developer_docstring_change["change"] == "description"
                and len(developer_docstring_change["new"]) > 10
            ):
                self.docstring_input.description = developer_docstring_change["new"]
                break
        if len(self.docstring_input.description) < 10:
            self.docstring_input.description = self.gpt_result.description

    def __select_class_attributes(self):
        for class_attribute_name in self.gpt_result.class_attribute_descriptions.keys():
            class_attr_annotation = [
                attr["type"]
                for attr in self.code_obj.class_attributes
                if attr["name"] == class_attribute_name and "type" in attr.keys()
            ]
            if len(class_attr_annotation) > 0:
                self.docstring_input.class_attribute_types[class_attribute_name] = (
                    class_attr_annotation[0]
                )
            else:
                self.docstring_input.class_attribute_types[class_attribute_name] = (
                    self.gpt_result.class_attribute_types[class_attribute_name]
                )
            self.docstring_input.class_attributes[class_attribute_name] = (
                self.gpt_result.class_attribute_descriptions[class_attribute_name]
            )

            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == class_attribute_name
                ):
                    if developer_docstring_change["change"] == "added":
                        self.docstring_input.class_attribute_types[
                            class_attribute_name
                        ] = developer_docstring_change["type"]
                        self.docstring_input.class_attributes[class_attribute_name] = (
                            developer_docstring_change["description"]
                        )
                    elif developer_docstring_change["change"] == "type":
                        self.docstring_input.class_attribute_types[
                            class_attribute_name
                        ] = developer_docstring_change["new"]
                    elif developer_docstring_change["change"] == "description":
                        self.docstring_input.class_attributes[class_attribute_name] = (
                            developer_docstring_change["new"]
                        )
                    break

    def __select_instance_attributes(self):
        for (
            instance_attribute_name
        ) in self.gpt_result.instance_attribute_descriptions.keys():
            instance_attr_annotation = [
                attr["type"]
                for attr in self.code_obj.instance_attributes
                if attr["name"] == instance_attribute_name and "type" in attr.keys()
            ]
            if len(instance_attr_annotation) > 0:
                self.docstring_input.instance_attribute_types[
                    instance_attribute_name
                ] = instance_attr_annotation[0]
            else:
                self.docstring_input.instance_attribute_types[
                    instance_attribute_name
                ] = self.gpt_result.instance_attribute_types[instance_attribute_name]
                self.docstring_input.instance_attributes[instance_attribute_name] = (
                    self.gpt_result.instance_attribute_descriptions[
                        instance_attribute_name
                    ]
                )

            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == instance_attribute_name
                ):
                    if developer_docstring_change["change"] == "added":
                        self.docstring_input.instance_attribute_types[
                            instance_attribute_name
                        ] = developer_docstring_change["type"]
                        self.docstring_input.instance_attributes[
                            instance_attribute_name
                        ] = developer_docstring_change["description"]
                    elif developer_docstring_change["change"] == "type":
                        self.docstring_input.instance_attribute_types[
                            instance_attribute_name
                        ] = developer_docstring_change["new"]
                    elif developer_docstring_change["change"] == "description":
                        self.docstring_input.instance_attributes[
                            instance_attribute_name
                        ] = developer_docstring_change["new"]
                    break
