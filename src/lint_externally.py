import restructuredtext_lint
import ast
import os
import sys


class UnsupportedSyntaxError(Exception):
    """
    Exception raised when an unsupported syntax is requested.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


def validate_docstring(docstring: str, syntax: str = "reStructuredText") -> list[str]:
    """
    Validate docstring

    :param docstring: docstring
    :type docstring: str
    :param syntax: the docstring syntax to check against. Currently only reStructuredText is implemented
    :type syntax: str

    :return: list of errors
    :return type: list[str]

    :raises UnsupportedSyntaxError: raised when the syntax is not reStructuredText, because no other syntax is implemented yet
    """
    if syntax != "reStructuredText":
        raise UnsupportedSyntaxError
    errors = restructuredtext_lint.lint(docstring)
    # filter out INFO level errors such as
    # "Unexpected possible title overline or transition.\nTreating it as ordinary text because it's so short."
    errors = [error for error in errors if error.type.upper() != "INFO"]
    return errors


def get_files_in_repo(repo_path) -> list[str]:
    """
    Get all python files in the target repository

    :return: list of python files in the repository
    :return type: list[str]
    """

    repo_files = [
        os.path.join(dirpath, f)
        for (dirpath, dirnames, filenames) in os.walk(repo_path)
        for f in filenames
    ]
    repo_files = [
        file for file in repo_files if not file.startswith(os.path.join(repo_path, "venv"))
    ]
    repo_files = [file for file in repo_files if file.endswith(".py")]
    return repo_files


if __name__ == "__main__":
    result = "validation sucessfull"
    num_validated_files = 0
    num_errors = 0
    sys.stderr = open(os.devnull, "w")
    for file in get_files_in_repo("C:\\Users\\Fabian\\Github\\AutoPyDoc\\working_repo"):
        num_validated_files += 1
        for node in ast.walk(ast.parse(open(file).read())):
            if (
                isinstance(node, ast.Module)
                or isinstance(node, ast.ClassDef)
                or isinstance(node, ast.FunctionDef)
                or isinstance(node, ast.AsyncFunctionDef)
            ):
                docstring = ast.get_docstring(node=node, clean=True)
                if docstring is not None and len(docstring) > 0:
                    errors = validate_docstring(docstring)
                    if len(errors) > 0:
                        print(f"Invalid docstring in file {file}: {docstring}")
                        result = "validation failed"
                        num_errors += 1
    sys.stderr = sys.__stderr__
    print(result, num_validated_files, "files were validated with", num_errors, "error(s)")
