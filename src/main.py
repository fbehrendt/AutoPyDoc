from repo_controller import RepoController
from extract_methods_from_change_info import extract_methods_from_change_info

def main(repo_path: str = None, debug=False) -> None: # repo_path will be required later
    """ Generates new docstrings for modified parts of the code

    :param repo_path: Path to the repository. Can be local or a GitHub link
    :type repo_path: str
    :param debug: toggle debug mode
    :type debug: boolean
    """

    repo = RepoController(repo_path=repo_path, debug=True)
    code_parts = {}
    changes = repo.get_changes()
    for change in changes:
        changed_methods = extract_methods_from_change_info(filename=change["filename"], change_start=change["start"], change_length=change["lines_changed"])
        changed_classes = [] # TODO
        if not debug:
            raise NotImplementedError
        changed_modules = [] # TODO
        if not debug:
            raise NotImplementedError
        for changed_method in changed_methods:
            # print(changed_method["content"], "\n")
            method_id = repo.get_method_id(changed_method)
            change_context = repo.get_context(method_id) # get methods called by this method, get methods calling this this method, if this method is part of a class, get the class, get the module. Instead of the full methods/class/module, their docstring may be used
            change_old_docstring = repo.code_parser.code_representer.get_docstring(method_id)
            change_code = repo.code_parser.code_representer.get_code(method_id)
            args_types_exceptions = repo.extract_args_types_exceptions(method_id)
            if hasattr(args_types_exceptions, "missing_types"):
                # inferr missing types
                if not debug:
                    raise NotImplementedError
            change_dev_comments = repo.extract_dev_comments(change)
            # see if old docstring is up-to-date
            # if up-to-date:
                # continue
            # flag developer comments
            # if only_comments_changed:
                # continue
            # generate description
            # build docstring
            # merge new docstring with developer comments
            # validate docstring syntax
            # insert new docstring
            # validate code integrity
    repo.apply_changes()
    if not debug:
        raise NotImplementedError

if __name__ == "__main__":
    main(repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True)