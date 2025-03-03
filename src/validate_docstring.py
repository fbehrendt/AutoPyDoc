import restructuredtext_lint


def validate_docstring(docstring: str, syntax: str = "reStructuredText") -> list[str]:
    """
    Validate docstring

    :param docstring: docstring
    :type docstring: str
    :param syntax: the docstring syntax to check against. Currently only reStructuredText is implemented
    :type syntax: str

    :return: list of errors
    :return type: list[str]

    :raises NotImplementedError: raised when the syntax is not reStructuredText, because no other syntax is implemented yet
    """
    if syntax != "reStructuredText":
        raise NotImplementedError
    errors = restructuredtext_lint.lint(docstring)
    for error in errors:
        if (
            error.message
            == "Unexpected possible title overline or transition.\nTreating it as ordinary text because it's so short."
        ):
            errors.remove(error)
    return errors


if __name__ == "__main__":
    test_docstring = '    """This is a test description for a method\n\n    :param a: First parameter\n    :type a: int"""'
    indentation_level = 4
    description = "This is a test description for a method"
    params = [
        {
            "name": "a",
            "type": "int",
            "description": "Description of param a",
            "default": 1,
        },
        {
            "name": "b",
            "type": "str",
            "description": "Description of param b",
            "default": "one",
        },
    ]
    return_type = "str"
    return_description = "The method returns a string"
    exceptions = [
        {"name": "InvalidInputException", "description": "The given input is invalid"}
    ]

    docstring = " " * indentation_level + '"""'
    docstring += description + "\n"
    # docstring += ' '* indentation_level + '\n'
    if len(params) > 0:
        docstring += "\n"
    for param in params:
        docstring += (
            " " * indentation_level
            + f":param {param['name']}: {param['description']}\n"
        )
        if "default" in param.keys():
            docstring += " " * indentation_level + f" Default is {param['default']}\n"
        docstring += (
            " " * indentation_level + f":type {param['name']}: {param['type']}\n"
        )
    if len(params) > 0:
        docstring += "\n"
    if return_type or return_description:
        docstring += " " * indentation_level + f":return: {return_description}\n"
        docstring += " " * indentation_level + f":rtype: {return_type}\n"
    for exception in exceptions:
        docstring += (
            " " * indentation_level
            + f":raises {exception['name']}: {exception['description']}\n"
        )
    if len(exceptions) > 0:
        docstring += "\n"
    docstring += " " * indentation_level + '"""'
    errors = validate_docstring(docstring)
    print()
    print(docstring)
    print()
    for error in errors:
        print(error.message)
    if len(errors) == 0:
        print("No errors in docstring")
    print()
