import configparser
import validators
from git import Repo, Actor
import os
import re
import pathlib
from pathlib import Path
from github import Github
from dotenv import load_dotenv
import shutil
import ast
import astunparse
import difflib
import filecmp

from code_representation import (
    CodeRepresenter,
    MethodObject,
    ClassObject,
    ModuleObject,
)


class RepoController:
    """A class to control interactions with the target repository"""

    def __init__(
        self,
        repo_path: str,
        pull_request_token: str = None,
        debug: bool = False,
        branch: str = "main",
    ):
        """
        A class to control interactions with the target repository

        :param repo: Path to the repository. Can be local or a GitHub link
        :type repo: str
        :param pull_request_token: token used to create pull requests
        :type pull_request_token: str
        :param debug: toggle debug mode
        :type debug: bool
        """
        parent_dir = pathlib.Path().resolve()
        dir = "working_repo"
        self.working_dir = os.path.join(parent_dir, dir)
        self.cmp_files = []

        self.debug = debug

        self.pull_request_token = pull_request_token

        self.is_local_repo = validators.url(repo_path)
        if self.is_local_repo:
            self.repo_url = repo_path
            self.pull_repo()
        else:
            self.working_dir = repo_path
            self.repo = Repo(self.working_dir)
            if not self.debug:
                raise NotImplementedError
        self.branch = branch

        if os.path.exists(os.path.join(parent_dir, "saved_files")):
            shutil.rmtree(os.path.join(parent_dir, "saved_files"))

        # self.repo = {} # {file_name: 'filename', 'methods': {'name': 'method_name', 'content': 'method content'}, 'classes': {'name': 'classname', 'methods' = {'name': 'method_name', 'content': 'method content'}}}
        self.get_latest_commit()
        if not self.debug:
            raise NotImplementedError

    def get_files_in_repo(self) -> list[str]:
        """
        Get all python files in the target repository

        :return: list of python files in the repository
        :return type: list[str]
        """
        if not hasattr(self, "repo_files"):
            repo_files = [
                os.path.join(dirpath, f)
                for (dirpath, dirnames, filenames) in os.walk(self.working_dir)
                for f in filenames
            ]
            repo_files = [
                file
                for file in repo_files
                if not file.startswith(os.path.join(self.working_dir, "venv"))
            ]
            self.repo_files = [file for file in repo_files if file.endswith(".py")]
        return self.repo_files

    def get_latest_commit(self):
        """Get the latest commit the tool sucessfully ran for. Sets the result internally"""
        self.latest_commit_file_name = os.path.join(
            self.working_dir, "latest_commit.autopydoc"
        )
        file_obj = Path(self.latest_commit_file_name)
        if file_obj.is_file():
            with open(self.latest_commit_file_name, mode="r") as f:
                self.latest_commit_hash = f.read().split("\n")[0]
                self.initial_run = False
        else:
            self.latest_commit_hash = None
            self.initial_run = True

    def clear_working_dir(self):
        """
        Idea: clear the working directory so it can be used by another repository. Reality: permission denied->remove files manually
        """
        # TODO not working. Permission denied
        if os.path.exists(self.working_dir):
            # tmp = tempfile.mktemp(dir=os.path.dirname(self.working_dir))
            # shutil.move(self.working_dir, tmp)
            # shutil.rmtree(tmp)
            # shutil.rmtree(self.working_dir)
            print("Please remove working_dir folder manually, then rerun")
            quit()
        os.makedirs(self.working_dir)

    def pull_repo(self):
        """Pulls a repository into the self.working_dir folder"""
        print("###pulling remote repository###")
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
        dir = os.listdir(self.working_dir)
        if len(dir) == 0:
            self.repo = Repo.clone_from(self.repo_url, self.working_dir)
            self.repo.git.checkout(self.branch)
            assert not self.repo.bare
        elif self.debug:
            self.repo = Repo(self.working_dir)
            return
        else:
            self.clear_working_dir()
            self.repo = Repo.clone_from(self.repo_url, self.working_dir)
            self.repo.git.checkout(self.branch)
            assert not self.repo.bare

    def get_changes(self) -> list[dict]:
        """
        Returns changed methods, classes and modules

        :return: A list of changed methods/classes/modules as dicts. Keys: type, content, signature, filenames, start, end
        :return type: list[dict]
        """
        print("###extracting changes###")
        current_commit = self.repo.head.commit  # get most recent commit
        if self.initial_run:
            result = []
            for file in self.get_files_in_repo():
                with open(file=file, mode="r") as f:
                    result.append(
                        {
                            "filename": os.path.normpath(file),
                            "start": 0,
                            "lines_changed": len(f.readlines()),
                        }
                    )
        else:
            latest_commit = self.repo.commit(self.latest_commit_hash)
            diff = self.repo.git.diff(latest_commit, current_commit)

            pattern = re.compile(
                "\+\+\+ b\/([\w.\/]+)\n@@ -(\d+),(\d+) \+(\d+),(\d+) @@"
            )
            changes = re.findall(pattern, diff)
            result = []
            for change in changes:
                # check if change affects a python file
                if not change[0].endswith(".py"):
                    continue
                result.append(
                    {
                        "filename": os.path.normpath(
                            os.path.join(self.working_dir, change[0])
                        ),
                        "start": int(change[3]),
                        "lines_changed": int(change[4]),
                    }
                )
        return result

    @staticmethod
    def get_class_id(changed_class: dict[str, str]) -> str:
        """
        Get a classes id based on change information. Static method

        :param changed_class: change information of the class. Must contain keys filename, type, content
        :type changed_class: dict[str, str]

        :return: class id
        :return type: str
        """
        pattern = re.compile("class ([^\(:]+)")
        class_name = re.findall(pattern, changed_class["content"])[0]
        return (
            changed_class["filename"] + "_" + changed_class["type"] + "_" + class_name
        )

    def identify_docstring_location(
        self, code_obj_id: str, code_representer: CodeRepresenter
    ) -> tuple[int]:
        """
        Identify the docstring location and indentation given a CodeObject

        :param code_obj_id: CodeObject id
        :type code_obj_id: str
        :param code_representer: CodeRepresenter
        :type code_representer: CodeRepresenter

        :return: tuple(start, indentation level, end)
        :rtype: tuple[int]

        :raises Exception("End of docstring not found"): raised when the end of the docstring cannot be located
        """
        # TODO use ast.get_source_code_segment() and/or look into asttokens
        code_obj = code_representer.get(code_obj_id)
        with open(file=code_obj.filename, mode="r") as f:
            lines = f.readlines()
            if isinstance(code_obj, ModuleObject):
                start_pos = 0
                indentation_level = 0
                start_line = lines[0]
                i = start_pos
            else:
                # get start pos
                class_nesting = []
                current_code_obj = code_obj
                while (
                    hasattr(current_code_obj, "outer_class_id")
                    and current_code_obj.outer_class_id is not None
                ):
                    current_code_obj = code_representer.get(code_obj.outer_class_id)
                    class_nesting.append(current_code_obj)
                start_pos = 0
                for outer_class_obj in class_nesting[
                    ::-1
                ]:  # iterate from outer most class to inner most class
                    # search for class
                    for i in range(start_pos, len(lines)):
                        if (
                            lines[i]
                            .lstrip()
                            .lower()
                            .startswith("class " + outer_class_obj.name.lower())
                        ):
                            start_pos = i + 1
                            break
                if isinstance(code_obj, MethodObject):
                    prefix = "def "
                elif isinstance(code_obj, ClassObject):
                    prefix = "class "
                else:
                    raise NotImplementedError

                # get start of signature
                for i in range(start_pos, len(lines)):
                    if (
                        lines[i]
                        .lstrip()
                        .lower()
                        .startswith(prefix + code_obj.name.lower())
                    ):
                        start_pos = i
                        start_line = lines[start_pos]
                        break

                # find end of signature
                open_brackets = 0
                for j in range(start_pos, len(lines)):
                    # TODO this can still fail for cases like def func(a="sfr("):
                    open_brackets += lines[j].count("(")
                    open_brackets -= lines[j].count(")")
                    if open_brackets < 1:
                        start_pos = j + 1
                        break

                # get indentation level
                indentation_level = (
                    sum(
                        4 if char == "\t" else 1
                        for char in start_line[: -len(start_line.lstrip())]
                    )
                    + 4
                )
                end_pos = len(lines)
                i = start_pos
                for j in range(start_pos, len(lines)):
                    if len(lines[j].strip()) > 0:
                        i = j
                        break
            if lines[i].strip().startswith('"""'):
                if (
                    lines[i].strip().rstrip("\n").endswith('"""')
                    and len(lines[i].strip()) >= 6
                ):  # inline docstring
                    end_pos = i
                else:
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().rstrip("\n").endswith('"""'):
                            end_pos = j + 1
                            break
                        if j == len(lines) - 1:
                            raise Exception("End of docstring not found")
            else:
                end_pos = start_pos
        return (start_pos, indentation_level, end_pos)

    def save_file_for_comparison(self, filename: str):
        new_partial_filename = (
            filename.split("working_repo")[-1].lstrip("/").lstrip("\\\\")
        )
        parent_dir = pathlib.Path().resolve()
        dir = "saved_files"
        dir = os.path.join(parent_dir, dir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        new_filename = os.path.join(dir, new_partial_filename)
        new_location = os.path.dirname(new_filename)
        if not os.path.isfile(new_filename):
            if not os.path.exists(new_location):
                os.makedirs(new_location)
            new_path = shutil.copy(filename, new_location)
            self.cmp_files.append([filename, new_path])

    def insert_docstring(self, filename: str, start: int, end: int, new_docstring: str):
        """
        Insert the new docstring. Lines between start and end will be overridden. Static method

        :param filename: filename
        :type filename: str
        :param start: line where the new docstring should start
        :type start: int
        :param end: line where the new docstring should end
        :type end: int
        :param new_docstring: new docstring
        :type new_docstring: str
        """
        self.save_file_for_comparison(filename)
        with open(filename, "r") as f:
            content = f.readlines()
            before = content[:start]
            after = content[end:]
            new_content = "".join(before) + new_docstring + "\n" + "".join(after)

            with open(filename, "w") as file:
                file.write(new_content)

    def remove_comments(self, filename: str) -> str:
        with open(filename) as f:
            lines = astunparse.unparse(ast.parse(f.read())).split("\n")
            content = []
            for line in lines:
                if line.lstrip()[:1] not in ("'", '"'):
                    content.append(line)
            content = "\n".join(content)
            new_filename = filename.rstrip(".py") + "_no_comments.py"
            with open(new_filename, mode="w") as f:
                f.write(content)
            return new_filename

    def validate_code_integrity(self):
        for file_before, file_after in self.cmp_files:
            file_before_no_comments = self.remove_comments(file_before)
            file_after_no_comments = self.remove_comments(file_after)
            if not filecmp.cmp(file_before_no_comments, file_after_no_comments):
                return False
        return True

    def update_latest_commit(self):
        """
        Update latest_commit file in target repo. Create if none exists
        """
        current_commit = self.repo.head.commit.hexsha  # get most recent commit
        print("Commit of docstring update:", current_commit)
        with open(self.latest_commit_file_name, mode="w") as f:
            f.write(current_commit)
        self.repo.index.add([self.latest_commit_file_name])

    def commit_to_new_branch(self, changed_files: list[str] = []):
        """
        Commit changes to a new branch. The new branch name is <old_branch>_AutoPyDoc

        :param changed_files: list of changed files
        :type change_files: list[str]

        :raises Exception: bare repository
        """
        if self.repo is not None:
            # create new branch
            new_branch = self.branch + "_AutoPyDoc"
            if new_branch not in [ref.name for ref in self.repo.references]:
                current = self.repo.create_head(new_branch)
                current.checkout()
            else:
                i = 1
                while new_branch in [ref.name for ref in self.repo.references]:
                    new_branch = self.branch + "_AutoPyDoc_" + str(i)
                current = self.repo.create_head(new_branch)
                current.checkout()
            main = self.repo.heads.main
            self.repo.git.pull("origin", main)

            # committing changed files and commit tracking file to new branch
            self.update_latest_commit()
            for file in changed_files:
                self.repo.index.add([file])

            # verify staging area
            modified_files = self.repo.index.diff(None)
            count_modified_files = len(modified_files)
            print(
                "Modified files:",
                count_modified_files,
                "\n",
                "\n".join([modified_file.b_path for modified_file in modified_files]),
            )

            staged_files = self.repo.index.diff("HEAD")
            count_staged_files = len(staged_files)
            print(
                "Staged files:",
                count_staged_files,
                "\n",
                "\n".join([staged_file.b_path for staged_file in staged_files]),
            )

            print("Modified files:", count_modified_files)
            print("Staged files:", count_staged_files)
            if count_staged_files < 2:
                print("No files modified. Quitting")
                quit()

            # create commit
            author = Actor("AutoPyDoc", "alltheunnecessaryjunk@gmail.com")
            committer = Actor("AutoPyDoc", "alltheunnecessaryjunk@gmail.com")
            self.repo.index.commit(
                "Automatically updated docstrings using AutoPyDoc",
                author=author,
                committer=committer,
            )

            # pushing to new branch
            self.repo.git.push("--set-upstream", "origin", current)
            return new_branch
        raise Exception("Bare repository")

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str,
    ):
        """
        Create pull request

        :param repo_name: name of the repository
        :type repo_name: str
        :param title: title of the pull request
        :type title: str
        :param description: description for the pull request
        :type description: str
        :param head_branch: head branch. This is the branch you are on
        :type head_branch: str
        :param base_branch: base branch. The branch where changes should be merged into
        :type base_branch: str
        """
        if self.pull_request_token is not None:
            auth_token = self.pull_request_token
        else:
            load_dotenv()
            auth_token = os.getenv("GitHubAuthToken")
        github_object = Github("fbehrendt", auth_token)
        repo = github_object.get_repo(repo_name)

        pull_request = repo.create_pull(
            title=title, body=description, head=head_branch, base=base_branch
        )
        github_object.close()
        return pull_request

    def apply_changes(self, changed_files: list[str] = []):
        """
        Apply to the repo in the way configured in src/config.ini. Currently creates a pull request from a new branch

        :param changed_files: list of changed_files
        :type changed_files: list[str]

        :raises NotImplementedError: raised when not in debug mode, because the config file is not yet implemented
        """
        print("###MOCK### Applying changes")
        config = configparser.ConfigParser()
        config.read("src/config.ini")

        current_commit = self.repo.head.commit.hexsha  # get most recent commit
        print("Commit before docstring update:", current_commit)
        new_branch = self.commit_to_new_branch(changed_files=changed_files)

        # create pull request
        self.create_pull_request(
            repo_name="fbehrendt/bachelor_testing_repo",  # TODO get programmatically
            title="Autogenerated Docstrings",
            description="Automatically created docstrings for recently changed code",
            head_branch=new_branch,
            base_branch=self.branch,
        )

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
