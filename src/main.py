import logging
import os
from dotenv import load_dotenv
import requests

from code_representation import ClassObject, CodeRepresenter, MethodObject, ModuleObject
from docstring_builder import create_docstring
from docstring_input_selector import (
    DocstringInputSelectorClass,
    DocstringInputSelectorMethod,
    DocstringInputSelectorModule,
)
from extract_outdated_ids import extract_code_affected_by_change
from get_context import CodeParser
from gpt_input import GptOutput
from gpt_interface import GptInterface
from repo_controller import RepoController, CodeIntegrityViolationError
from validate_docstring import validate_docstring
from validate_docstring_input import validate_docstring_input

from save_data import save_data

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)8s: [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AutoPyDoc:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def main(
        self,
        repo_path: str,
        username: str,
        model_strategy_name: str,
        model_strategy_params: dict[str, str],
        pull_request_token=None,
        branch: str = "main",
        debug=False,
        repo_owner=None,
    ) -> None:  # repo_path will be required later
        """Generates new docstrings for modified parts of the code

        :param repo_path: Path to the repository. Can be local or a GitHub link
        :type repo_path: str
        :param debug: toggle debug mode
        :type debug: boolean
        """

        # Initialize gpt interface with the chosen strategy and its parameters early to fail early if model is unavailable or unable to load
        self.logger.info(f"Using {model_strategy_name} strategy.")
        self.gpt_interface = GptInterface(model_strategy_name, **model_strategy_params)

        # pull repo, create code representation, create dependencies
        self.debug = debug

        self.repo = RepoController(
            repo_path=repo_path,
            pull_request_token=pull_request_token,
            username=username,
            branch=branch,
            logger=self.logger,
            debug=debug,
            repo_owner=repo_owner,
        )
        self.code_parser = CodeParser(
            code_representer=CodeRepresenter(),
            working_dir=self.repo.working_dir,
            debug=True,
            files=self.repo.get_files_in_repo(),
            logger=self.logger,
        )

        def save_objects(objects):
            content = ""
            for object in objects.values():
                print(str(object.__dict__))
                content += str(object.__dict__)
                content += "\n"
            with open(file="saved_objects.txt", mode="w") as f:
                f.write(content)

        # save_objects(self.code_parser.code_representer.objects)

        self.code_parser.extract_class_and_method_calls()
        self.code_parser.extract_args_and_return_type()
        self.code_parser.extract_exceptions()
        self.code_parser.check_return_type()
        self.code_parser.extract_attributes()

        self.repo.repo.git.checkout(self.repo.latest_commit_hash)
        self.logger.info(f"Checked out branch {self.repo.repo.active_branch.name}")
        self.code_parser_old = CodeParser(
            code_representer=CodeRepresenter(),
            working_dir=self.repo.working_dir,
            debug=True,
            files=self.repo.get_files_in_repo(),
            logger=self.logger,
        )
        self.repo.repo.git.checkout(self.repo.current_commit)
        self.logger.info(f"Checked out branch {self.repo.repo.active_branch.name}")
        outdated_ids = extract_code_affected_by_change(
            code_parser_old=self.code_parser_old, code_parser_new=self.code_parser
        )
        self.code_parser.code_representer.set_multiple_outdated(outdated_ids)

        # get changes between last commit the tool ran for and now
        # self.changes = self.repo.get_changes()
        # self.code_parser.set_code_affected_by_changes_to_outdated(changes=self.changes)

        full_input_for_estimation = self.code_parser.code_representer.generate_next_batch(
            ignore_dependencies=True, dry=True
        )
        self.gpt_interface.estimate(full_input=full_input_for_estimation)

        save_data(
            branch="semantic_validation",
            code_type="",
            code_name="",
            code_id="",
            content_type="total_objects_" + str(len(self.code_parser.code_representer.objects)),
            data="",
        )
        first_batch = self.code_parser.code_representer.generate_next_batch()
        save_data(
            branch="semantic_validation",
            code_type="",
            code_name="",
            code_id="",
            content_type="batch_" + str(len(first_batch)),
            data="",
        )
        if len(self.code_parser.code_representer.get_sent_to_gpt_ids()) == 0:
            self.logger.info("No need to do anything")
            quit()
        self.gpt_interface.process_batch(first_batch, callback=self.process_gpt_result)

        # if parts are still outdated
        while len(self.code_parser.code_representer.get_outdated_ids()) > 0:
            missing_items = self.code_parser.code_representer.get_outdated_ids()
            self.logger.info("Some parts are still missing updates")
            self.logger.info("\n".join([str(item) for item in missing_items]))
            # force generate all, ignore dependencies
            next_batch = self.code_parser.code_representer.generate_next_batch(
                ignore_dependencies=True
            )
            if len(next_batch) > 0:
                self.gpt_interface.process_batch(next_batch, callback=self.process_gpt_result)

        # if every docstring is updated
        if not self.repo.validate_code_integrity():
            self.logger.fatal("Code integrity no longer given!!! aborting")
            raise CodeIntegrityViolationError("Code integrity no longer given!!! aborting")
            quit()  # saveguard in case someone tries to catch the exception and continue anyways
        self.logger.info("Code integrity validated")

        self.repo.apply_changes(changed_files=self.code_parser.code_representer.get_changed_files())
        self.logger.info("Finished successfully")

    def process_gpt_result(self, result: GptOutput) -> None:
        self.logger.debug(f"Received {str(result.id)}")
        self.logger.debug(
            f"Waiting for {str(len(self.code_parser.code_representer.get_sent_to_gpt_ids()))} more results"
        )
        code_obj = self.code_parser.code_representer.get(result.id)

        start_pos, indentation_level, end_pos = self.repo.identify_docstring_location(
            code_obj.id, code_representer=self.code_parser.code_representer
        )

        if result.no_change_necessary:
            save_data(
                branch="semantic_validation",
                code_type=code_obj.code_type,
                code_name=code_obj.name,
                code_id=code_obj.id,
                content_type="accurate",
                data="",
            )
            code_obj.outdated = False
        else:
            save_data(
                branch="semantic_validation",
                code_type=code_obj.code_type,
                code_name=code_obj.name,
                code_id=code_obj.id,
                content_type="inaccurate",
                data="",
            )

        if not result.no_change_necessary:
            # merge new docstring with developer comments
            developer_docstring_changes = self.extract_dev_comments(code_obj)
            if isinstance(code_obj, MethodObject):
                docstring_input = DocstringInputSelectorMethod(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                    indentation_level=indentation_level,
                ).get_result()
            if isinstance(code_obj, ClassObject):
                docstring_input = DocstringInputSelectorClass(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                    indentation_level=indentation_level,
                ).get_result()
            if isinstance(code_obj, ModuleObject):
                docstring_input = DocstringInputSelectorModule(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                    indentation_level=indentation_level,
                ).get_result()

            # validate if docstring input was generated successfully
            docstring_input, new_pr_notes = validate_docstring_input(
                docstring_input=docstring_input,
                code_representer=self.code_parser.code_representer,
                repo_path=self.repo.working_dir,
            )
            self.repo.pr_notes.extend(new_pr_notes)

            # build docstring
            new_docstring = create_docstring(
                code_obj=code_obj,
                docstring_input=docstring_input,
                indentation_level=indentation_level,
                code_representer=self.code_parser.code_representer,
                debug=True,
            )

            # validate docstring syntax
            errors = validate_docstring(new_docstring)
            if len(errors) > 0:
                save_data(
                    branch="syntax_validation",
                    code_type=code_obj.code_type,
                    code_name=code_obj.name,
                    code_id=code_obj.id,
                    content_type="error",
                    data=str(errors),
                )
                save_data(
                    branch="syntax_validation",
                    code_type=code_obj.code_type,
                    code_name=code_obj.name,
                    code_id=code_obj.id,
                    content_type="new_docstring",
                    data=new_docstring,
                )
                # TODO re-sent to GPT, with note. If this is the second time, don't update this docstring and put note in pull request description
                self.logger.warning("Docstring is not valid. Retry")
                if hasattr(code_obj, "retry") and code_obj.retry > 0:
                    if code_obj.retry > 2:
                        self.logger.error("Docstring is still invalid after 3 attempts. Skipping")
                        code_obj.outdated = False
                        code_obj.is_updated = True
                        return
                    code_obj.retry += 1
                else:
                    code_obj.retry = 1
                return  # this prevents code_obj.outdated from being set to False and code_obj.is_updated from being set to True, causing it to be included in the next batch again. # TODO what about sent_to_gpt?

            # insert new docstring in the file
            try:
                self.repo.insert_docstring(
                    filename=code_obj.filename,
                    start=start_pos,
                    end=end_pos,
                    new_docstring=new_docstring,
                    old_docstring=code_obj.old_docstring,
                )
            except CodeIntegrityViolationError:
                code_obj.send_to_gpt = False
            else:
                code_obj.update_docstring(new_docstring=new_docstring)
                code_obj.is_updated = True
                code_obj.outdated = False
        # if parts are still outdated
        next_batch = self.code_parser.code_representer.generate_next_batch()
        if len(next_batch) > 0:
            save_data(
                branch="semantic_validation",
                code_type="",
                code_name="",
                code_id="",
                content_type="batch_" + str(len(next_batch)),
                data="",
            )
            self.gpt_interface.process_batch(next_batch, callback=self.process_gpt_result)

    # TODO move elsewhere
    @staticmethod
    def print_diff(a, b):
        if a == b:
            return
        import difflib

        print("{} => {}".format(a, b))
        for i, s in enumerate(difflib.unified_diff([a], [b])):
            print("DIFF:\n", s)

    # TODO move elsewhere
    def extract_dev_comments(self, code_obj):
        import ast
        import pathlib
        import sys

        from code_representation import ClassObject, MethodObject, ModuleObject
        from docstring_dismantler import DocstringDismantler

        developer_changes = []

        self.repo.repo.git.stash("save")
        self.repo.repo.git.checkout(self.repo.latest_commit_hash)

        sys.stderr = open(os.devnull, "w")
        # if the file is new, all existing docstrings are manually generated
        if os.path.isfile(code_obj.filename):
            code_ast = ast.parse(open(code_obj.filename).read())
            sys.stderr = sys.__stderr__
            old_docstring = -1

            for node in ast.walk(code_ast):
                if isinstance(code_obj, MethodObject) and (
                    isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)
                ):
                    if code_obj.name == node.name:
                        old_docstring = ast.get_docstring(node, clean=True) or ""
                        break
                elif isinstance(code_obj, ClassObject) and isinstance(node, ast.ClassDef):
                    if code_obj.name == node.name:
                        old_docstring = ast.get_docstring(node, clean=True) or ""
                        break
                elif isinstance(code_obj, ModuleObject) and isinstance(node, ast.Module):
                    old_docstring = ast.get_docstring(node, clean=True) or ""
                    break

            if old_docstring == -1:
                # new method/class
                return []
            if code_obj.old_docstring is not None and old_docstring == code_obj.old_docstring:
                print("+++docstrings are equal+++")
                return []

        # if the file does not exist, all docstrings were made manually
        print("---docstrings are different---")
        new_docstring_dismantler = DocstringDismantler(docstring=code_obj.old_docstring or "")
        if not ("old_docstring" in locals() or "old_docstring" in globals()):
            old_docstring = ""
        old_docstring_dismantler = DocstringDismantler(docstring=old_docstring or "")
        developer_changes = old_docstring_dismantler.compare_docstrings(new_docstring_dismantler)
        if len(developer_changes) > 0:
            print(
                f"=============\n{code_obj.name} in {pathlib.Path(code_obj.filename).stem}\n============="
            )
        for developer_change in developer_changes:
            print(developer_change)

        self.repo.repo.git.checkout(self.repo.current_commit)
        git_stash_list = self.repo.repo.git.stash("list")
        if len(git_stash_list) > 0:
            self.repo.repo.git.stash("pop")
            self.repo.repo.git.stash("clear")

        if developer_changes is None:
            print()
        return developer_changes
        # tree = self.repo.repo.head.commit.tree
        # self.repo.latest_commit_hash
        # print("Latest commit hash:", self.repo.latest_commit_hash)
        # self.repo.repo.head.commit
        # steps_in_the_past = 1
        # while self.repo.repo.commit(f"HEAD~{steps_in_the_past}").hexsha != self.repo.latest_commit_hash:
        #    commit = self.repo.repo.commit(f"HEAD~{steps_in_the_past}")
        #    print(steps_in_the_past, "    " + commit.message, "    " + commit.hexsha)
        #    steps_in_the_past += 1
        # steps_in_the_past -= 1 # The commit after the AutoPyDoc commit is a merge commit
        # search in between for commit message starting with "Automatically generated docstrings using AutoPyDoc"
        # if such a commit exists, compare to that commit, if not, compare to latest commit, if not exists compare to empty file
        # get docstrings of codeobj using ast.parse() and ast.docstring()
        # for code_obj_id in self.code_parser.code_representer.get_outdated_ids():
        #    code_obj = self.code_parser.code_representer.get(code_obj_id)
        #    filename = code_obj.filename
        #    commits = list(
        #        self.repo.repo.iter_commits(all=True, max_count=10, paths=filename)
        #    )
        #    print(filename)
        #    for commit in commits:
        #        print("    " + commit.message, "    " + commit.hexsha)
        #    print()
        # TODO get version before and after
        # TODO ast parse visit code ast.docstring() on both files
        # diff
        # print()


if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()

    auto_py_doc.main(
        repo_path="https://github.com/fbehrendt/bachelor_testing_repo_small",
        username="fbehrendt",
        model_strategy_name="mock",
        model_strategy_params={"context_size": 2**13},
        branch="module_docstrings",
        repo_owner="fbehrendt",
        debug=True,
    )

    # auto_py_doc.main(repo_path="C:\\Users\\Fabian\Github\\bachelor_testing_repo", debug=True)
