from repo_controller import RepoController

def main(repo_path: str = None) -> None: # repo_path will be required later
    """ Generates new dosctrings for modified parts of the code

    :param repo_path: Path to the repository. Can be local or a GitHub link
    :type repo_path: str
    """
    
    # repo = RepoController(repo_path)
    # changes = repo.get_changes()
    # for change in changes:
        # extract old docstring
        # see if old docstring is up-to-date
        # continue if up-to-date
        # extract developer comments
        # extract code without comments
        # continue if only comments were changed
        # generate new docstring
        # merge new docstring with developer comments
        # insert new docstring
    # repo.apply_changes()
    raise NotImplementedError

if __name__ == "__main__":
    main()