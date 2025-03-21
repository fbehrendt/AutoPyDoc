from dataclasses import dataclass, field


@dataclass
class DocstringInput:
    description: str = field(default="", compare=True, hash=True)
    arguments: list = field(default_factory=list, compare=True, hash=True)
    return_info: dict | None = field(default=None, compare=True, hash=True)
    exceptions: list = field(default_factory=list, compare=True, hash=True)
    class_attributes: list = field(default_factory=list, compare=True, hash=True)
    instance_attributes: list = field(default_factory=list, compare=True, hash=True)


class DocstringInputSelector:
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        self.code_obj = code_obj
        self.gpt_result = gpt_result
        self.developer_docstring_changes = developer_docstring_changes
        self.docstring_input = DocstringInput()

        self.__select_description()

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
            for (
                gpt_exception_name,
                exception_description,
            ) in self.gpt_result.exception_descriptions.items():
                if gpt_exception_name == exception_name:
                    new_exception = {
                        "name": exception_name["name"],
                        "description": exception_description,
                    }
            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "exceptions"
                    and developer_docstring_change["name"] == exception_name["name"]
                ):
                    if developer_docstring_change["change"] == "added":
                        new_exception = {
                            "name": developer_docstring_change["name"],
                            "description": developer_docstring_change["description"],
                        }
                    elif developer_docstring_change["change"] == "description":
                        new_exception["description"] = developer_docstring_change[
                            "description"
                        ]
                    break
            self.docstring_input.exceptions.append(new_exception)


class DocstringInputSelectorMethod(DocstringInputSelector):
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        super().__init__(code_obj, gpt_result, developer_docstring_changes)
        self.__select_parameters()
        super().__select_exceptions()
        self.__select_return_info()

    def __select_parameters(self):
        # parameters
        for argument in self.code_obj.arguments:
            new_arg = {
                "name": argument["name"],
                "type": self.gpt_result.parameter_types[argument["name"]],
                "description": self.gpt_result.parameter_descriptions[argument["name"]],
            }
            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == argument["name"]
                ):
                    if developer_docstring_change["change"] == "added":
                        new_arg = {
                            "name": developer_docstring_change["name"],
                            "type": developer_docstring_change["type"],
                            "description": developer_docstring_change["description"],
                        }
                    elif developer_docstring_change["change"] == "type":
                        new_arg["type"] = developer_docstring_change["type"]
                    elif developer_docstring_change["change"] == "description":
                        new_arg["description"] = developer_docstring_change[
                            "description"
                        ]
                    break
            self.docstring_input.arguments.append(new_arg)

    def __select_return_info(self):
        if self.code_obj.return_type is None and self.code_obj.missing_return_type:
            return_type = self.gpt_result.return_type
        else:
            return_type = self.code_obj.return_type
        return_description = self.gpt_result.return_description

        for developer_docstring_change in self.developer_docstring_changes:
            if developer_docstring_change["place"] == "return":
                if developer_docstring_change["change"] == "added":
                    return_type = developer_docstring_change["type"]
                    return_description = developer_docstring_change["description"]
                elif developer_docstring_change["change"] == "type":
                    return_type = developer_docstring_change["type"]
                elif developer_docstring_change["change"] == "description":
                    return_description = developer_docstring_change["description"]
                break

        self.docstring_input.return_info = {
            "type": return_type,
            "description": return_description,
        }


class DocstringInputSelectorModule(DocstringInputSelector):
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        super().__init__(code_obj, gpt_result, developer_docstring_changes)
        super().__select_exceptions()


class DocstringInputSelectorClass(DocstringInputSelector):
    def __init__(self, code_obj, gpt_result, developer_docstring_changes):
        super().__init__(code_obj, gpt_result, developer_docstring_changes)
        self.__select_class_attributes()
        self.__select_instance_attributes()

    def __select_class_attributes(self):
        for class_attribute_name in self.gpt_result.class_attribute_descriptions.keys():
            class_attr_annotation = [
                attr["type"]
                for attr in self.code_obj.class_attributes
                if attr["name"] == class_attribute_name and "type" in attr.keys()
            ][0]
            if len(class_attr_annotation) > 0:
                attr_type = class_attr_annotation
            else:
                attr_type = self.gpt_result.class_attribute_types[class_attribute_name]
            new_class_attr = {
                "name": class_attribute_name,
                "type": attr_type,
                "description": self.gpt_result.class_attribute_descriptions[
                    class_attribute_name
                ],
            }

            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == class_attribute_name
                ):
                    if developer_docstring_change["change"] == "added":
                        new_class_attr = {
                            "name": developer_docstring_change["name"],
                            "type": developer_docstring_change["type"],
                            "description": developer_docstring_change["description"],
                        }
                    elif developer_docstring_change["change"] == "type":
                        new_class_attr["type"] = developer_docstring_change["type"]
                    elif developer_docstring_change["change"] == "description":
                        new_class_attr["description"] = developer_docstring_change[
                            "description"
                        ]
                    break
            self.docstring_input.class_attributes.append(new_class_attr)

    def __select_instance_attributes(self):
        for (
            instance_attribute_name
        ) in self.gpt_result.instance_attribute_descriptions.keys():
            instance_attr_annotation = [
                attr["type"]
                for attr in self.code_obj.instance_attributes
                if attr["name"] == instance_attribute_name and "type" in attr.keys()
            ][0]
            if len(instance_attr_annotation) > 0:
                attr_type = instance_attr_annotation
            else:
                attr_type = self.gpt_result.instance_attribute_types[
                    instance_attribute_name
                ]
            new_instance_attr = {
                "name": instance_attribute_name,
                "type": attr_type,
                "description": self.gpt_result.instance_attribute_descriptions[
                    instance_attribute_name
                ],
            }

            for developer_docstring_change in self.developer_docstring_changes:
                if (
                    developer_docstring_change["place"] == "parameters"
                    and developer_docstring_change["name"] == instance_attribute_name
                ):
                    if developer_docstring_change["change"] == "added":
                        new_instance_attr = {
                            "name": developer_docstring_change["name"],
                            "type": developer_docstring_change["type"],
                            "description": developer_docstring_change["description"],
                        }
                    elif developer_docstring_change["change"] == "type":
                        new_instance_attr["type"] = developer_docstring_change["type"]
                    elif developer_docstring_change["change"] == "description":
                        new_instance_attr["description"] = developer_docstring_change[
                            "description"
                        ]
                    break
            self.docstring_input.instance_attributes.append(new_instance_attr)
