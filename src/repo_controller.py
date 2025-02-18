import configparser
import validators
from git import Repo
import os
import tempfile
import shutil
import sqlite3
import re
import pathlib
from pathlib import Path

from get_context import CodeParser
from code_representation import CodeRepresenter, Method_obj, Class_obj

class RepoController():
    def __init__(self, repo_path: str, debug=False) -> None:
        """ Initializes a RepoController Object

        :param repo: Path to the repository. Can be local or a GitHub link
        :type repo: str
        :param debug: toggle debug mode
        :type debug: boolean
        """
        parent_dir = pathlib.Path().resolve()
        dir = "working_repo"
        self.working_dir = os.path.join(parent_dir, dir)

        self.debug = debug
        self.is_local_repo = validators.url(repo_path)
        if self.is_local_repo:
            self.repo_url = repo_path
            self.pull_repo()
        else:
            self.copy_repo(repo_path)
            raise NotImplementedError
        
        self.code_parser = CodeParser(code_representer=CodeRepresenter(), working_dir=self.working_dir, debug=True)
        for file in self.get_files_in_repo():
            self.code_parser.add_file(file)
        self.code_parser.create_dependencies()
        # self.repo = {} # {file_name: 'filename', 'methods': {'name': 'method_name', 'content': 'method content'}, 'classes': {'name': 'classname', 'methods' = {'name': 'method_name', 'content': 'method content'}}}
        self.get_latest_commit()
        if not self.debug:
            raise NotImplementedError
    
    def get_files_in_repo(self):
        if not hasattr(self, 'repo_files'):
            repo_files = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(self.working_dir) for f in filenames]
            self.repo_files = [file for file in repo_files if file.endswith(".py")]
        return self.repo_files
    
    def get_latest_commit(self):
        self.latest_commit_file_name = os.path.join(self.working_dir, "latest_commit.autopydoc")
        file_obj = Path(self.latest_commit_file_name)
        if file_obj.is_file():
            with open(self.latest_commit_file_name, mode='r') as f:
                self.latest_commit_hash = f.read().split("\n")[0]
                self.initial_run = False
        else:
            self.latest_commit_hash = None
            self.initial_run = True

    def clear_working_dir(self):
        """ Cleans the working directory"""
        # TODO not working. Permission denied
        if (os.path.exists(self.working_dir)):
            #tmp = tempfile.mktemp(dir=os.path.dirname(self.working_dir))
            #shutil.move(self.working_dir, tmp)
            #shutil.rmtree(tmp)
            #shutil.rmtree(self.working_dir)
            print("Please remove working_dir folder manually, then rerun")
            quit()
        os.makedirs(self.working_dir)

    def pull_repo(self):
        """ Pulls a repository into the working_repo folder"""
        print("###pulling remote repository###")
        dir = os.listdir(self.working_dir) 
        if len(dir) == 0:
            self.repo = Repo.clone_from(self.repo_url, self.working_dir) 
            assert not self.repo.bare
        elif self.debug:
            self.repo = Repo(self.working_dir)
            return
        else:
            self.clear_working_dir()
            self.repo = Repo.clone_from(self.repo_url, self.working_dir) 
            assert not self.repo.bare
    
    def copy_repo(self, repo_path):
        """ Copies local files into the working_repo folder
        
        :param repo_path: Path to the repository
        :type repo_path: str"""
        print("###copying repository files to working folder###")
        self.clear_working_dir()
        if not self.debug:
            raise NotImplementedError
    
    def get_changes(self) -> list[dict]:
        """ Returns changed methods, classes and modules

        :returns: A list of changed methods/classes/modules as dicts. Keys: type, content, signature, filenames, start, end
        :rtype: list[dict]
        """
        print("###extracting changes###")
        if not self.debug:
            raise NotImplementedError
        else:
            current_commit = self.repo.head.commit  # get most recent commit
            if self.initial_run:
                latest_commit = self.repo.commit("e2676eba2dcaa478268d1b24397df0c9d0236d16")
                # TODO change
            else:
                latest_commit = self.repo.commit(self.latest_commit_hash)
            diff = self.repo.git.diff(latest_commit, current_commit)

            pattern = re.compile('\+\+\+ b\/([\w.\/]+)\n@@ -(\d+),(\d+) \+(\d+),(\d+) @@')
            changes = re.findall(pattern, diff)
            result = []
            for change in changes:
                # check if change affects a python file
                if not change[0].endswith(".py"):
                    continue
                result.append({
                    "filename": self.working_dir.replace("/", "\\") + "\\" + change[0].replace("/", "\\"),
                    "start": int(change[3]),
                    "lines_changed": int(change[4])
                    })
            return result
    
    @staticmethod
    def get_method_id(changed_method):
        pattern = re.compile('def ([^\(]+)')
        method_name = re.findall(pattern, changed_method["content"])[0]
        return changed_method["filename"] + "_" + changed_method["type"] + "_" + method_name

    def get_context(self, code_obj_id) -> list[dict]:
        """ Returns context of a given method/class/module
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: Context of a given method/class/module
        :rtype: list[dict]
        """
        print("###Gathering context###")
        if code_obj_id in self.code_parser.code_representer.objects.keys():
            return self.code_parser.code_representer.objects[code_obj_id].get_context()
        return None
    
    def extract_docstring(self, code_obj) -> str:
        """ Extract the docstring (if exists)
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: docstring of the given code snippet
        :rtype: str
        """
        return code_obj.get_docstring()
    
    def extract_code(self, code_obj) -> str:
        """ Extract the code without comments
        
        :param code_obj: A dictionary with details regarding a method/class/module
        :code_obj type: dict
        :returns: code snippet without comments
        :rtype: str
        """
        return code_obj.get_code()

    def extract_args_types_exceptions(self, method_id) -> str:
        """ Extract args, types and exceptions of a given method
        
        :param method_obj: A dictionary with details regarding a method
        :method_obj type: dict
        :returns: dict with args, types and exceptions of a method as dict. Format: {params: [{name: str, type: str}], return_type: str, exceptions: list, missing_types: list}
        :rtype: dict{list[dict]}
        """
        return self.code_parser.code_representer.get_extract_args_types_exceptions(method_id)

    @staticmethod
    def print_code(code):
        for line in code.split("\n"):
            print(line)
    
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
    
    def identify_code_location(self, code_obj_id: Method_obj|Class_obj) -> tuple:
        code_obj = self.code_parser.code_representer.get(code_obj_id)
        with open(file=code_obj.filename, mode="r") as f:
            lines = f.readlines()
            # get start pos
            class_nesting = []
            current_code_obj = code_obj
            while hasattr(current_code_obj, "class_obj_id") and current_code_obj.class_obj_id is not None:
                current_code_obj = self.code_parser.code_representer.get(code_obj.class_obj_id)
                class_nesting.append(current_code_obj)
            start_pos = 0
            for outer_class_obj in class_nesting[::-1]: # iterate from outer most class to inner most class
                # search for class
                for i in range(start_pos, len(lines)):
                    if lines[i].lstrip().lower().startswith("class " + outer_class_obj.name.lower()):
                        start_pos = i+1
                        break
            if code_obj.type == "method":
                prefix = "def "
            elif code_obj.type == "class":
                prefix = "class "
            elif code_obj.type == "module":
                return (0, 0, len(lines)) # full file
            else:
                raise NotImplementedError
            for i in range(start_pos, len(lines)):
                if lines[i].lstrip().lower().startswith(prefix + code_obj.name.lower()):
                    start_pos = i
                    start_line = lines[start_pos]
                    break
            # get indentation level
            indentation_level = sum(4 if char == '\t' else 1 for char in start_line[:-len(start_line.lstrip())])
            end_pos = len(lines)
            for i in range(start_pos+1, len(lines)):
                if len(lines[i].strip()) > 0 and sum(4 if char == '\t' else 1 for char in lines[i][:-len(lines[i].lstrip())]) <= indentation_level:
                    # TODO decrease by preceeding blank lines
                    end_pos = i-1
                    break
        return (start_pos, indentation_level, end_pos)


            
    def update_latest_commit(self):
        # TODO create_commit
        current_commit = self.repo.head.commit.hexsha  # get most recent commit
        with open(self.latest_commit_file_name, mode="w") as f:
            f.write(current_commit)
        print(current_commit)
        # connection = sqlite3.connect("repos.db")
        # cursor = connection.cursor()
        # cursor.execute("CREATE TABLE IF NOT EXISTS repo_states (url PRIMARY KEY, last_commit)")
        # row = cursor.execute(f"INSERT OR REPLACE INTO repo_states VALUES({self.repo_url},{current_commit})")
        # connection.commit()
        
        if not self.debug:
            raise NotImplementedError

    def apply_changes(self, changes: list|str = "all") -> None:
        """ Applies new docstrings to the repo in the way configured in src/config.ini
        
        :param changes: List of changes to apply, defaults to all
        :type changes: list|str
        """
        print("###MOCK### Applying changes")
        config = configparser.ConfigParser()
        config.read('src/config.ini')
        self.update_latest_commit()
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