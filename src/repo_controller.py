import configparser
import validators
from git import Repo, Actor
import os
import re
import pathlib
from pathlib import Path
from github import Github
from dotenv import load_dotenv

from get_context import CodeParser
from code_representation import CodeRepresenter, MethodObject, ClassObject

class RepoController():
    def __init__(self, repo_path: str, pull_request_token = None, debug=False) -> None:
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

        self.pull_request_token = pull_request_token

        self.is_local_repo = validators.url(repo_path)
        if self.is_local_repo:
            self.repo_url = repo_path
            self.pull_repo()
        else:
            self.working_dir = repo_path
            self.repo = Repo(self.working_dir)
            # self.copy_repo(repo_path)
            if not self.debug:
                raise NotImplementedError
        self.branch = "main" # TODO change
        
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
            repo_files = [file for file in repo_files if not file.startswith(os.path.join(self.working_dir,"venv"))]
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
                # diff = self.repo.index.diff(None, current_commit)
                # latest_commit = self.repo.commit("4b825dc642cb6eb9a060e54bf8d69288fbee4904") # https://jiby.tech/post/git-diff-empty-repo/ fails
                # TODO change
                result = []
                for file in self.get_files_in_repo():
                    with open(file=file, mode="r") as f:
                        result.append({
                            "filename": os.path.normpath(file),
                            "start": 0,
                            "lines_changed": len(f.readlines())
                            })
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
                        "filename": os.path.normpath(os.path.join(self.working_dir, change[0])),
                        "start": int(change[3]),
                        "lines_changed": int(change[4])
                        })
            return result
    
    @staticmethod
    def get_method_id(changed_method):
        pattern = re.compile('def ([^\(]+)')
        method_name = re.findall(pattern, changed_method["content"])[0]
        return changed_method["filename"] + "_" + changed_method["type"] + "_" + method_name
    
    @staticmethod
    def get_class_id(changed_class):
        pattern = re.compile('class ([^\(:]+)')
        class_name = re.findall(pattern, changed_class["content"])[0]
        return changed_class["filename"] + "_" + changed_class["type"] + "_" + class_name

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
    
    def identify_docstring_location(self, code_obj_id: MethodObject|ClassObject) -> tuple:
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
                    start_pos = i+1
                    start_line = lines[start_pos]
                    break
            # get indentation level
            indentation_level = sum(4 if char == '\t' else 1 for char in start_line[:-len(start_line.lstrip())])
            end_pos = len(lines)
            i = start_pos
            for j in range(start_pos, len(lines)):
                if len(lines[j].strip()) > 0:
                    i = j
                    break
            if lines[i].strip().startswith('"""'):
                if lines[i].strip().rstrip("\n").endswith('"""') and len(lines[i].strip()) >= 6: # inline docstring
                    end_pos = i+1
                else:
                    for j in range(i+1, len(lines)):
                        if lines[j].strip().rstrip("\n").endswith('"""'):
                            end_pos = j+1
                            break
                        if j == len(lines)-1:
                            raise Exception("End of docstring not found")
            else:
                end_pos = start_pos
        return (start_pos, indentation_level, end_pos)

    @staticmethod
    def insert_docstring(filename, start, end, new_docstring):
        with open(filename, 'r') as f:
            content = f.readlines()
            before = content[:start]
            after = content[end:]
            new_content = "".join(before) + new_docstring + "\n" + "".join(after)
            
            with open(filename, 'w') as file:
                file.write(new_content)
            
    def update_latest_commit(self):
        # TODO create_commit
        current_commit = self.repo.head.commit.hexsha  # get most recent commit
        print("Commit of docstring update:", current_commit)
        with open(self.latest_commit_file_name, mode="w") as f:
            f.write(current_commit)
        self.repo.index.add([self.latest_commit_file_name])
        # connection = sqlite3.connect("repos.db")
        # cursor = connection.cursor()
        # cursor.execute("CREATE TABLE IF NOT EXISTS repo_states (url PRIMARY KEY, last_commit)")
        # row = cursor.execute(f"INSERT OR REPLACE INTO repo_states VALUES({self.repo_url},{current_commit})")
        # connection.commit()
        
        if not self.debug:
            raise NotImplementedError

    def commit_to_new_branch(self, changed_files: list = None):
        if self.repo != None:

            # create new branch
            new_branch = self.branch + "_AutoPyDoc"
            current = self.repo.create_head(new_branch)
            current.checkout()
            main = self.repo.heads.main
            self.repo.git.pull('origin', main)

            # committing changed files and commit tracking file to new branch
            self.update_latest_commit()
            for file in changed_files:
                self.repo.index.add([file])

            # verify staging area
            modified_files = self.repo.index.diff(None)
            count_modified_files = len(modified_files)
            print("Modified files:", count_modified_files, "\n", "\n".join([modified_file.b_path for modified_file in modified_files]))

            staged_files = self.repo.index.diff("HEAD")
            count_staged_files = len(staged_files)
            print("Staged files:", count_staged_files, "\n", "\n".join([staged_file.b_path for staged_file in staged_files]))

            print("Modified files:", count_modified_files)
            print("Staged files:", count_staged_files)
            if count_staged_files < 2:
                print("No files modified. Quitting")
                quit()
                
            # create commit
            author = Actor("AutoPyDoc", "alltheunnecessaryjunk@gmail.com")
            committer = Actor("AutoPyDoc", "alltheunnecessaryjunk@gmail.com")
            self.repo.index.commit("Automatically updated docstrings using AutoPyDoc", author=author, committer=committer)

            # pushing to new branch
            self.repo.git.push('--set-upstream', 'origin', current)
            return new_branch
        raise Exception # TODO

    def create_pull_request(self, repo_name, title, description, head_branch, base_branch):
        # Public Web Github
        if self.pull_request_token is not None:
            auth_token = self.pull_request_token
        else:
            load_dotenv()
            auth_token = os.getenv('GitHubAuthToken')
        github_object = Github("fbehrendt", auth_token)
        repo = github_object.get_repo(repo_name)

        pull_request = repo.create_pull(
            title=title,
            body=description,
            head=head_branch,
            base=base_branch
        )
        # To close connections after use
        github_object.close()
        return pull_request

    def apply_changes(self, changed_files: list = None) -> None:
        """ Applies new docstrings to the repo in the way configured in src/config.ini
        
        :param changes: List of changes to apply, defaults to all
        :type changes: list|str
        """
        print("###MOCK### Applying changes")
        config = configparser.ConfigParser()
        config.read('src/config.ini')

        current_commit = self.repo.head.commit.hexsha  # get most recent commit
        print("Commit before docstring update:", current_commit)
        new_branch = self.commit_to_new_branch(changed_files=changed_files)
        
        # create pull request
        self.create_pull_request(repo_name="fbehrendt/bachelor_testing_repo", title="Autogenerated Docstrings", description="Automatically created docstrings for recently changed code", head_branch=new_branch, base_branch=self.branch) # TODO

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