import configparser

class RepoController():
    def __init__(repo_path: str):
        """
        :param repo: Path to the repository. Can be local or a GitHub link
        :type repo: str
        """
        # self.repo_path = repo_path
        # self.is_local_repo
        # self.repo = {} # {file_name: 'filename', 'methods': {'name': 'method_name', 'content': 'method content'}, 'classes': {'name': 'classname', 'methods' = {'name': 'method_name', 'content': 'method content'}}}
        raise NotImplementedError
    
    def get_changes():
        """returns changed methods, classes and modules"""
        raise NotImplementedError
    
    def extract_docstring(file, class_name=None, method_name = None):
        if class_name == None and method_name == None:
            # extract module docstring
            raise NotImplementedError
        elif class_name != None and method_name == None:
            # extract class docstring
            raise NotImplementedError
        elif method_name != None:
            # extract method docstring
            raise NotImplementedError
        else:
            # throw error
            raise NotImplementedError
            

    def apply_changes():
        """Applies the new docstring to the repo in the way configured"""
        config = configparser.ConfigParser()
        config.read('src/config.ini')
        # if repo_path is local filepath:
            # if config['Default']['local_repo_behaviour'] == "commit":
                # commit changes
            # elif config['Default']['local_repo_behaviour'] == "amend":
                # amend commit
            # elif config['Default']['local_repo_behaviour'] == "stage":
                # stage changes
            # elif config['Default']['local_repo_behaviour'] == "none":
                # pass
            # else:
                # raise error
        # elif repo_path is GitHub link:
            # if config['Default']['remote_repo_behaviour'] == "pull_request":
                # create pull request
            # elif config['Default']['remote_repo_behaviour'] == "push":
                # push changes
            # else:
                # raise error
        raise NotImplementedError