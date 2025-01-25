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
            print(changed_method["content"], "\n")
            change_context = repo.get_context(changed_method) # get methods called by this method, get methods calling this this method, if this method is part of a class, get the class, get the module. Instead of the full methods/class/module, their docstring may be used
            change_old_docstring = repo.extract_docstring(changed_method)
            change_code = repo.extract_code(changed_method)
            args_types_exceptions = repo.extract_args_types_exceptions(change)
            if len(args_types_exceptions["missing_types"]) > 0:
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