from repo_controller import RepoController

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
        change_context = repo.get_context(change)
        change_old_docstring = repo.extract_docstring(change)
        change_code = repo.extract_code(change)
        if change["type"] == "method":
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