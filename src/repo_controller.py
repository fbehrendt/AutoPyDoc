import configparser

import validators
from git import Repo
import os
import tempfile
import shutil

class RepoController():
    def __init__(self, repo_path: str, debug=False) -> None:
        """ Initializes a RepoController Object

        :param repo: Path to the repository. Can be local or a GitHub link
        :type repo: str
        :param debug: toggle debug mode
        :type debug: boolean
        """
        self.working_dir = 'working_repo'
        self.debug = debug
        self.is_local_repo = validators.url(repo_path)
        if self.is_local_repo:
            self.repo_url = repo_path
            self.pull_repo()
        else:
            self.copy_repo(repo_path)
        # self.repo = {} # {file_name: 'filename', 'methods': {'name': 'method_name', 'content': 'method content'}, 'classes': {'name': 'classname', 'methods' = {'name': 'method_name', 'content': 'method content'}}}
        if not self.debug:
            raise NotImplementedError
    
    def clear_working_dir(self):
        """ Cleans the working directory"""
        if (os.path.exists(self.working_dir)):
            tmp = tempfile.mktemp(dir=os.path.dirname(self.working_dir))
            shutil.move(self.working_dir, tmp)
            shutil.rmtree(tmp)
        os.makedirs(self.working_dir)

    def pull_repo(self):
        """ Pulls a repository into the working_repo folder"""
        print("###MOCK### pulling remote repository")
        self.clear_working_dir()
        repo = Repo.clone_from(self.repo_url, self.working_dir) 
        if not self.debug:
            raise NotImplementedError
    
    def copy_repo(self, repo_path):
        """ Copies local files into the working_repo folder
        
        :param repo_path: Path to the repository
        :type repo_path: str"""
        print("###MOCK### copying repository files to working folder")
        self.clear_working_dir()
        if not self.debug:
            raise NotImplementedError
    
    def get_changes(self) -> list[dict]:
        """ Returns changed methods, classes and modules

        :returns: A list of changed methods/classes/modules as dicts. Keys: type, content, signature, filenames, start, end
        :rtype: list[dict]
        """
        print("###MOCK### extracting changes")
        if not self.debug:
            raise NotImplementedError
        else:
            return [{"type": "method",
                     "content": 'def multiply(a: int,b: int): -> int\n\t"""multiply two numbers\n\n\t:param a: first number\n\t:type a: int\n\t:param b: second number\n\t:type b: int\n\t:returns: a*b\n\t:rtype: int"""\n\treturn a*b',
                     "signature": "def multiply(a: int,b: int): -> int",
                     "filenames": "main.py",
                     "start": 0,
                     "end": 9}]
    
    def get_context(self, code_obj) -> list[dict]:
        """ Returns context of a given method/class/module
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: Context of a given method/class/module
        :rtype: list[dict]
        """
        print("###MOCK### Gathering context")
        if not self.debug:
            raise NotImplementedError
        else:
            return [{"type": "method",
              "content": 'def context_method_1():\n\t"""this is context method 1\n\n\t"""\n\tpass',
              "signature": "def context_method_1():",
              "filenames": "main.py",
              "start": 11,
              "end": 15}]
    
    def extract_docstring(self, code_obj) -> str:
        """ Extract the docstring (if exists)
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: docstring of the given code snippet
        :rtype: str
        """
        print("###MOCK### Extracting docstring")
        if not self.debug:
            raise NotImplementedError
        else:
            return '"""multiply two numbers\n\n\t:param a: first number\n\t:type a: int\n\t:param b: second number\n\t:type b: int\n\t:returns: a*b\n\t:rtype: int"""'
    
    def extract_code(self, code_obj) -> str:
        """ Extract the code without comments
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: code snippet without comments
        :rtype: str
        """
        print("###MOCK### Extracting code")
        if not self.debug:
            raise NotImplementedError
        else:
            return "return a*b"

    def extract_args_types_exceptions(self, method_obj) -> str:
        """ Extract args, types and exceptions of a given method
        
        :param method_obj: A dictionary with details regarding a method
        :method_obj type: dict
        :returns: dict with args, types and exceptions of a method as dict. Format: {params: [{name: str, type: str}], return_type: str, exceptions: list, missing_types: list}
        :rtype: dict{list[dict]}
        """
        print("###MOCK### Extracting arguments, types and exceptions")
        if not self.debug:
            raise NotImplementedError
        else:
            return {"params": [{"name": "a", type: int}], "return_type": int, "exceptions": [], "missing_types": ["b"]} # multiply(a: int, b) -> int:\n\treturn a*b
    
    def extract_dev_comments(self, code_obj) -> list[str]:
        """ Extract developer comments
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: dev comments
        :rtype: list[str]
        """
        print("###MOCK### Extracting developer comments")
        if not self.debug:
            raise NotImplementedError
        else:
            return "A developer comment"
            

    def apply_changes(self, changes: list|str = "all") -> None:
        """ Applies new docstrings to the repo in the way configured in src/config.ini
        
        :param changes: List of changes to apply, defaults to all
        :type changes: list|str
        """
        print("###MOCK### Applying changes")
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
        if not self.debug:
            raise NotImplementedError