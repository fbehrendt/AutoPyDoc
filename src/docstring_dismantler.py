import re


class DocstringDismantler:
    def __init__(self, docstring: str):
        self.docstring = docstring

        self.description_pattern = (
            r"\n?[ ]*([^:]+)(?::param|:return|:raises|:class attribute|:instance attribute)?"
        )

        self.func_param_pattern = r"\n[ ]*:param (\w+): ([^\n]+)\n[ ]*:type (\w+): ([^\n]+)"
        self.func_param_name_pattern = r"\n[ ]*:param (\w+):"
        self.func_param_description_pattern = r"\n[ ]*:param \w+: ([^\n]+)"
        self.func_param_type_pattern = r"\n[ ]*:param \w+: [^\n]+\n[ ]*:type \w+: ([^\n]+)"

        self.func_return_pattern = r"\n[ ]*:return: ([^\n]+)\n[ ]*:rtype: ([^\n]+)"

        self.func_return_description_pattern = r"\n[ ]*:return: ([^\n]+)"
        self.func_return_type_pattern = r"\n[ ]*:rtype: ([^\n]+)"

        self.exception_pattern = r"\n[ ]*:raises (\w+): ([^\n]+)"
        self.exception_name_pattern = r"\n[ ]*:raises (\w+): [^\n]+"
        self.exception_description_pattern = r"\n[ ]*:raises \w+: ([^\n]+)"

        self.class_attr_pattern = (
            r"\n[ ]*:class attribute (\w+): ([^\n]+)\n[ ]*:type (\w+): ([^\n]+)"
        )
        self.class_attr_name_pattern = r"\n[ ]*:class attribute (\w+): [^\n]+"
        self.class_attr_description_pattern = r"\n[ ]*:class attribute \w+: ([^\n]+)"
        self.class_attr_type_pattern = (
            r"\n[ ]*:class attribute \w+: [^\n]+\n[ ]*:type \w+: ([^\n]+)"
        )

        self.instance_attr_pattern = (
            r"\n[ ]*:instance attribute (\w+): ([^\n]+)\n[ ]*:type (\w+): ([^\n]+)"
        )
        self.instance_attr_name_pattern = r"\n[ ]*:instance attribute (\w+): [^\n]+"
        self.instance_attr_description_pattern = r"\n[ ]*:instance attribute \w+: ([^\n]+)"
        self.instance_attr_type_pattern = (
            r"\n[ ]*:instance attribute \w+: [^\n]+\n[ ]*:type \w+: ([^\n]+)"
        )

        if len(docstring) > 0:
            self.description = self.apply_pattern(self.description_pattern)[0].rstrip()
        else:
            self.description = ""
        self.params = [
            {"name": param[0], "description": param[1], "type": param[3]}
            for param in self.apply_pattern(self.func_param_pattern)
        ]
        return_info = self.apply_pattern(self.func_return_pattern)
        if len(return_info) > 0:
            return_info = return_info[0]
        else:
            return_info = None

        if return_info and len(return_info) > 0:
            self.return_info = {"description": return_info[0], "type": return_info[1]}

        self.exceptions = [
            {"name": exception[0], "description": exception[1]}
            for exception in self.apply_pattern(self.exception_pattern)
        ]

        self.class_attrs = [
            {"name": attr[0], "description": attr[1], "type": attr[3]}
            for attr in self.apply_pattern(self.class_attr_pattern)
        ]

        self.instance_attrs = [
            {"name": attr[0], "description": attr[1], "type": attr[3]}
            for attr in self.apply_pattern(self.instance_attr_pattern)
        ]

    def apply_pattern(self, pattern):
        pattern = re.compile(pattern)
        return re.findall(pattern, self.docstring)

    def compare_docstrings(self, docstring_unbuilder):
        def get_by_name(dict_list, name):
            for item in dict_list:
                if item["name"] == name:
                    return item

        differences = []

        # compare description
        if self.description != docstring_unbuilder.description:
            differences.append(
                {
                    "place": "description",
                    "change": "description",
                    "old": self.description,
                    "new": docstring_unbuilder.description,
                }
            )

        # compare parameters
        for old_param in self.params:
            if old_param["name"] not in [
                new_param["name"] for new_param in docstring_unbuilder.params
            ]:
                differences.append(
                    {
                        "place": "parameters",
                        "name": old_param["name"],
                        "change": "deleted",
                    }
                )
                continue
            new_param = get_by_name(docstring_unbuilder.params, old_param["name"])
            if old_param["type"] != new_param["type"]:
                differences.append(
                    {
                        "place": "parameters",
                        "name": old_param["name"],
                        "change": "type",
                        "old": old_param["type"],
                        "new": new_param["type"],
                    }
                )
            if old_param["description"] != new_param["description"]:
                differences.append(
                    {
                        "place": "parameters",
                        "name": old_param["name"],
                        "change": "description",
                        "old": old_param["description"],
                        "new": new_param["description"],
                    }
                )
        for new_param in docstring_unbuilder.params:
            if new_param["name"] not in [old_param["name"] for old_param in self.params]:
                differences.append(
                    {
                        "place": "parameters",
                        "name": new_param["name"],
                        "change": "added",
                        "description": new_param["description"],
                        "type": new_param["type"],
                    }
                )

        # compare return
        if hasattr(docstring_unbuilder, "return_info") and not hasattr(self, "return_info"):
            differences.append(
                {
                    "place": "return",
                    "change": "added",
                    "type": docstring_unbuilder.return_info["type"],
                    "description": docstring_unbuilder.return_info["description"],
                }
            )
        if not hasattr(docstring_unbuilder, "return_info") and hasattr(self, "return_info"):
            differences.append({"place": "return", "change": "deleted"})
        if hasattr(docstring_unbuilder, "return_info") and hasattr(self, "return_info"):
            if self.return_info["description"] != docstring_unbuilder.return_info["description"]:
                differences.append(
                    {
                        "place": "return",
                        "change": "description",
                        "old": self.return_info["description"],
                        "new": docstring_unbuilder.return_info["description"],
                    }
                )
            if self.return_info["type"] != docstring_unbuilder.return_info["type"]:
                differences.append(
                    {
                        "place": "return",
                        "change": "type",
                        "old": self.return_info["type"],
                        "new": docstring_unbuilder.return_info["type"],
                    }
                )

        # compare exceptions
        for old_exception in self.exceptions:
            if old_exception["name"] not in [
                new_exception["name"] for new_exception in docstring_unbuilder.exceptions
            ]:
                differences.append(
                    {
                        "place": "exceptions",
                        "name": old_exception["name"],
                        "change": "deleted",
                    }
                )
                continue
            new_exception = get_by_name(docstring_unbuilder.exceptions, old_exception["name"])
            if old_exception["description"] != new_exception["description"]:
                differences.append(
                    {
                        "place": "exceptions",
                        "name": old_exception["name"],
                        "change": "description",
                        "old": old_exception["description"],
                        "new": new_exception["description"],
                    }
                )
        for new_exception in docstring_unbuilder.exceptions:
            if new_exception["name"] not in [
                old_exception["name"] for old_exception in self.exceptions
            ]:
                differences.append(
                    {
                        "place": "exceptions",
                        "name": new_exception["name"],
                        "change": "added",
                    }
                )

        # compare class attributes
        for old_class_attr in self.class_attrs:
            if old_class_attr["name"] not in [
                new_class_attr["name"] for new_class_attr in docstring_unbuilder.class_attrs
            ]:
                differences.append(
                    {
                        "place": "class_attributes",
                        "name": old_class_attr["name"],
                        "change": "deleted",
                    }
                )
                continue
            new_class_attr = get_by_name(docstring_unbuilder.class_attrs, old_class_attr["name"])
            if old_class_attr["type"] != new_class_attr["type"]:
                differences.append(
                    {
                        "place": "class_attributes",
                        "change": "type",
                        "name": old_class_attr["name"],
                        "old": old_class_attr["type"],
                        "new": new_class_attr["type"],
                    }
                )
            if old_class_attr["description"] != new_class_attr["description"]:
                differences.append(
                    {
                        "place": "class_attributes",
                        "change": "description",
                        "name": old_class_attr["name"],
                        "old": old_class_attr["description"],
                        "new": new_class_attr["description"],
                    }
                )
        for new_class_attr in docstring_unbuilder.class_attrs:
            if new_class_attr["name"] not in [
                old_class_attr["name"] for old_class_attr in self.class_attrs
            ]:
                differences.append(
                    {
                        "place": "class_attributes",
                        "name": new_class_attr["name"],
                        "change": "added",
                        "description": new_class_attr["description"],
                        "type": new_class_attr["type"],
                    }
                )

        # compare instance attributes
        for old_instance_attr in self.instance_attrs:
            if old_instance_attr["name"] not in [
                new_instance_attr["name"]
                for new_instance_attr in docstring_unbuilder.instance_attrs
            ]:
                differences.append(
                    {
                        "place": "instance_attributes",
                        "name": old_instance_attr["name"],
                        "change": "deleted",
                    }
                )
                continue
            new_instance_attr = get_by_name(
                docstring_unbuilder.instance_attrs, old_instance_attr["name"]
            )
            if old_instance_attr["type"] != new_instance_attr["type"]:
                differences.append(
                    {
                        "place": "instance_attributes",
                        "change": "type",
                        "name": old_instance_attr["name"],
                        "old": old_instance_attr["type"],
                        "new": new_instance_attr["type"],
                    }
                )
            if old_instance_attr["description"] != new_instance_attr["description"]:
                differences.append(
                    {
                        "place": "instance_attributes",
                        "change": "description",
                        "name": old_instance_attr["name"],
                        "old": old_instance_attr["description"],
                        "new": new_instance_attr["description"],
                    }
                )
        for new_instance_attr in docstring_unbuilder.instance_attrs:
            if new_instance_attr["name"] not in [
                old_instance_attr["name"] for old_instance_attr in self.instance_attrs
            ]:
                differences.append(
                    {
                        "place": "instance_attributes",
                        "name": new_instance_attr["name"],
                        "change": "added",
                        "description": new_instance_attr["description"],
                        "type": new_instance_attr["type"],
                    }
                )
        return differences


def print_diff(a, b):
    if a == b:
        return
    import difflib

    print("{} => {}".format(a, b))
    for i, s in enumerate(difflib.unified_diff([a], [b])):
        print("DIFF:\n", s)


def compare_docstrings(old_docstring: str, new_docstring: str):
    def get_by_name(dict_list, name):
        for item in dict_list:
            if item["name"] == name:
                return item

    differences = []
    old_docstring_dismantler = DocstringDismantler(docstring=old_docstring)
    new_docstring_dismantler = DocstringDismantler(docstring=new_docstring)

    # compare description
    if old_docstring_dismantler.description != new_docstring_dismantler.description:
        differences.append(
            f"Docstring description was changed from {old_docstring_dismantler.description} to {new_docstring_dismantler.description}"
        )

    # compare parameters
    for old_param in old_docstring_dismantler.params:
        if old_param["name"] not in [
            new_param["name"] for new_param in new_docstring_dismantler.params
        ]:
            differences.append("New docstring no longer has param " + old_param["name"])
            continue
        new_param = get_by_name(new_docstring_dismantler.params, old_param["name"])
        if old_param["type"] != new_param["type"]:
            differences.append(
                f"Type of param {old_param['name']} was changed to {new_param['type']} from {old_param['type']}"
            )
        if old_param["description"] != new_param["description"]:
            differences.append(
                f"Description of param {old_param['name']} was changed to {new_param['description']} from {old_param['description']}"
            )
    for new_param in new_docstring_dismantler.params:
        if new_param["name"] not in [
            old_param["name"] for old_param in old_docstring_dismantler.params
        ]:
            differences.append("Docstring has new param " + new_param["name"])

    # compare return
    if hasattr(new_docstring_dismantler, "return_info") and not hasattr(
        old_docstring_dismantler, "return_info"
    ):
        differences.append("Return information added")
    if not hasattr(new_docstring_dismantler, "return_info") and hasattr(
        old_docstring_dismantler, "return_info"
    ):
        differences.append("Return information removed")
    if hasattr(new_docstring_dismantler, "return_info") and hasattr(
        old_docstring_dismantler, "return_info"
    ):
        if (
            old_docstring_dismantler.return_info["description"]
            != new_docstring_dismantler.return_info["description"]
        ):
            differences.append(
                f"Return description changed from {old_docstring_dismantler.return_info['description']} to {new_docstring_dismantler.return_info['description']}"
            )
        if (
            old_docstring_dismantler.return_info["type"]
            != new_docstring_dismantler.return_info["type"]
        ):
            differences.append(
                f"Return type changed from {old_docstring_dismantler.return_info['type']} to {new_docstring_dismantler.return_info['type']}"
            )

    # compare exceptions
    for old_exception in old_docstring_dismantler.exceptions:
        if old_exception["name"] not in [
            new_exception["name"] for new_exception in new_docstring_dismantler.exceptions
        ]:
            differences.append("New docstring no longer has exception " + old_exception["name"])
            continue
        new_exception = get_by_name(new_docstring_dismantler.exceptions, old_exception["name"])
        if old_exception["description"] != new_exception["description"]:
            differences.append(
                f"Description of exception {old_exception['name']} was changed to {new_exception['description']} from {old_exception['description']}"
            )
    for new_exception in new_docstring_dismantler.exceptions:
        if new_exception["name"] not in [
            old_exception["name"] for old_exception in old_docstring_dismantler.exceptions
        ]:
            differences.append("Docstring has new exception " + new_exception["name"])

    # compare class attributes
    for old_class_attr in old_docstring_dismantler.class_attrs:
        if old_class_attr["name"] not in [
            new_class_attr["name"] for new_class_attr in new_docstring_dismantler.class_attrs
        ]:
            differences.append(
                "New docstring no longer has class attribute " + old_class_attr["name"]
            )
            continue
        new_class_attr = get_by_name(new_docstring_dismantler.class_attrs, old_class_attr["name"])
        if old_class_attr["type"] != new_class_attr["type"]:
            differences.append(
                f"Type of class attribute {old_class_attr['name']} was changed to {new_class_attr['type']} from {old_class_attr['type']}"
            )
        if old_class_attr["description"] != new_class_attr["description"]:
            differences.append(
                f"Description of class attribute {old_class_attr['name']} was changed to {new_class_attr['description']} from {old_class_attr['description']}"
            )
    for new_class_attr in new_docstring_dismantler.class_attrs:
        if new_class_attr["name"] not in [
            old_class_attr["name"] for old_class_attr in old_docstring_dismantler.class_attrs
        ]:
            differences.append("Docstring has new class attribute " + new_class_attr["name"])

    # compare instance attributes
    for old_instance_attr in old_docstring_dismantler.instance_attrs:
        if old_instance_attr["name"] not in [
            new_instance_attr["name"]
            for new_instance_attr in new_docstring_dismantler.instance_attrs
        ]:
            differences.append(
                "New docstring no longer has instance attribute " + old_instance_attr["name"]
            )
            continue
        new_instance_attr = get_by_name(
            new_docstring_dismantler.instance_attrs, old_instance_attr["name"]
        )
        if old_instance_attr["type"] != new_instance_attr["type"]:
            differences.append(
                f"Type of instance attribute {old_instance_attr['name']} was changed to {new_instance_attr['type']} from {old_instance_attr['type']}"
            )
        if old_instance_attr["description"] != new_instance_attr["description"]:
            differences.append(
                f"Description of instance attribute {old_instance_attr['name']} was changed to {new_instance_attr['description']} from {old_instance_attr['description']}"
            )
    for new_instance_attr in new_docstring_dismantler.instance_attrs:
        if new_instance_attr["name"] not in [
            old_instance_attr["name"]
            for old_instance_attr in old_docstring_dismantler.instance_attrs
        ]:
            differences.append("Docstring has new instance attribute " + new_instance_attr["name"])
    return differences


if __name__ == "__main__":
    docstring1 = '"""\n    Create a docstring for a CodeObject, using the GPT results\n\n    :param code_obj: CodeObject in question\n    :type code_obj: CodeObject\n    :param result: the 1 GPT results,.;:\n    :type result: dict\n    :param debug: toggle debug mode. Default False\n    :type debug: int\n\n    :return: Docstring of CodeObject\n    :rtype: int\n\n    :raises NotImplementedError: raised when trying to access functionality that is not yet implemented\n\n    :class attribute filename: description for class attr filename\n    :type filename: str\n    :instance attribute filename: description for instance attr filename\n    :type filename: str\n"""'

    docstring2 = '"""\n    Create docstring for CodeObject, using GPT results\n\n    :param code_obj: The CodeObject\n    :type code_obj: CodeObject\n    :param indentation_level: indentation level the docstring should have\n    :type indentation_level: int\n    :param debug: toggle debug mode. Default False\n    :type debug: bool\n\n    :return: docstring for the CodeObject\n    :rtype: str\n\n    :raises NotImplementedError: raised when trying to access functionality that is not yet implemented\n\n    :class attribute filename: description for class attr filename\n    :type filename: str\n    :instance attribute filename: description for instance attr filename\n    :type filename: str\n"""'

    differences = compare_docstrings(docstring1, docstring2)
    print()
    print("\n".join(differences))
    docstring_dismantler1 = DocstringDismantler(docstring=docstring1)
    docstring_dismantler2 = DocstringDismantler(docstring=docstring2)
    differences = docstring_dismantler1.compare_docstrings(
        docstring_unbuilder=docstring_dismantler2
    )
    print(differences)
