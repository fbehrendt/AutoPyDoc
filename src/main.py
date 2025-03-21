import logging

from docstring_builder import create_docstring
from docstring_input_selector import (
    DocstringInputSelectorClass,
    DocstringInputSelectorMethod,
    DocstringInputSelectorModule,
)
from validate_docstring_input import validate_docstring_input
from gpt_input import GptOutput
from gpt_interface import GptInterface
from repo_controller import RepoController
from validate_docstring import validate_docstring
from get_context import CodeParser
from code_representation import CodeRepresenter, MethodObject, ClassObject, ModuleObject

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
        repo_path: str = None,
        pull_request_token=None,
        branch: str = "main",
        debug=False,
    ) -> None:  # repo_path will be required later
        """Generates new docstrings for modified parts of the code

        :param repo_path: Path to the repository. Can be local or a GitHub link
        :type repo_path: str
        :param debug: toggle debug mode
        :type debug: boolean
        """

        # initialize gpt interface early to fail early if model is unavailable or unable to load
        self.gpt_interface = GptInterface("mock")
        # self.gpt_interface = GptInterface("local_deepseek")

        # pull repo, create code representation, create dependencies
        self.debug = debug

        self.repo = RepoController(
            repo_path=repo_path,
            pull_request_token=pull_request_token,
            branch=branch,
            logger=self.logger,
            debug=debug,
        )
        self.code_parser = CodeParser(
            code_representer=CodeRepresenter(),
            working_dir=self.repo.working_dir,
            debug=True,
            files=self.repo.get_files_in_repo(),
            logger=self.logger,
        )

        self.code_parser.extract_class_and_method_calls()
        self.code_parser.extract_args_and_return_type()
        self.code_parser.extract_exceptions()
        self.code_parser.check_return_type()
        self.code_parser.extract_attributes()

        # get changes between last commit the tool ran for and now
        self.changes = self.repo.get_changes()
        self.code_parser.set_code_affected_by_changes_to_outdated(changes=self.changes)
        self.extract_dev_comments()

        first_batch = self.code_parser.code_representer.generate_next_batch()
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
                self.gpt_interface.process_batch(
                    next_batch, callback=self.process_gpt_result
                )

        # if every docstring is updated
        if not self.repo.validate_code_integrity():
            raise Exception("Code integrity no longer given!!! aborting")
            quit()  # saveguard in case someone tries to catch the exception and continue anyways
        self.logger.info("Code integrity validated")

        self.repo.apply_changes(
            changed_files=self.code_parser.code_representer.get_changed_files()
        )
        if not self.debug:
            raise NotImplementedError
        self.logger.info("Finished successfully")

    def process_gpt_result(self, result: GptOutput) -> None:
        self.logger.info("Received" + str(result.id))
        self.logger.info(
            "Waiting for"
            + str(len(self.code_parser.code_representer.get_sent_to_gpt_ids()))
            + "more results"
        )
        code_obj = self.code_parser.code_representer.get(result.id)
        if not result.no_change_necessary:
            start_pos, indentation_level, end_pos = (
                self.repo.identify_docstring_location(
                    code_obj.id, code_representer=self.code_parser.code_representer
                )
            )

            # merge new docstring with developer comments
            developer_docstring_changes = self.extract_dev_comments(code_obj)
            if isinstance(code_obj, MethodObject):
                docstring_input = DocstringInputSelectorMethod(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                ).get_result()
            if isinstance(code_obj, ClassObject):
                docstring_input = DocstringInputSelectorClass(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                ).get_result()
            if isinstance(code_obj, ModuleObject):
                docstring_input = DocstringInputSelectorModule(
                    code_obj=code_obj,
                    gpt_result=result,
                    developer_docstring_changes=developer_docstring_changes,
                ).get_result()

            # validate if docstring input was generated successfully
            docstring_input, new_pr_notes = validate_docstring_input(
                docstring_input=docstring_input,
                code_representer=self.code_parser.code_representer,
            )
            self.repo.pr_notes.extend(new_pr_notes)

            # build docstring
            new_docstring = create_docstring(
                docstring_input,
                result,
                indentation_level,
                code_representer=self.code_parser.code_representer,
                debug=True,
            )

            # validate docstring syntax
            errors = validate_docstring(new_docstring)
            if len(errors) > 0:
                # TODO resent to GPT, with note. If this is the second time, don't update this docstring and put note in pull request description
                if not self.debug:
                    raise NotImplementedError

            # insert new docstring in the file
            self.repo.insert_docstring(
                filename=code_obj.filename,
                start=start_pos,
                end=end_pos,
                new_docstring=new_docstring,
            )
            code_obj.update_docstring(new_docstring=new_docstring)

            code_obj.is_updated = True
        code_obj.outdated = False
        # if parts are still outdated
        next_batch = self.code_parser.code_representer.generate_next_batch()
        if len(next_batch) > 0:
            self.gpt_interface.process_batch(
                next_batch, callback=self.process_gpt_result
            )

    @staticmethod
    def print_diff(a, b):
        if a == b:
            return
        import difflib

        print("{} => {}".format(a, b))
        for i, s in enumerate(difflib.unified_diff([a], [b])):
            print("DIFF:\n", s)

    def extract_dev_comments(self, code_obj):
        import ast
        import sys
        import os
        import pathlib
        from code_representation import MethodObject, ClassObject, ModuleObject
        from docstring_dismantler import DocstringDismantler

        self.repo.repo.git.checkout(self.repo.latest_commit_hash)
        sys.stderr = open(os.devnull, "w")
        code_ast = ast.parse(open(code_obj.filename).read())
        sys.stderr = sys.__stderr__
        for node in ast.walk(code_ast):
            if isinstance(code_obj, MethodObject) and (
                isinstance(node, ast.FunctionDef)
                or isinstance(node, ast.AsyncFunctionDef)
            ):
                if code_obj.name == node.name:
                    old_docstring = ast.get_docstring(node, clean=True) or ""
            elif isinstance(code_obj, ClassObject) and isinstance(node, ast.ClassDef):
                if code_obj.name == node.name:
                    old_docstring = ast.get_docstring(node, clean=True) or ""
            elif isinstance(code_obj, ModuleObject) and isinstance(node, ast.Module):
                old_docstring = ast.get_docstring(node, clean=True) or ""
        if old_docstring == code_obj.old_docstring:
            print("+++docstrings are equal+++")
            return
        else:
            print("---docstrings are different---")
            new_docstring_dismantler = DocstringDismantler(
                docstring=code_obj.old_docstring or ""
            )
            old_docstring_dismantler = DocstringDismantler(
                docstring=old_docstring or ""
            )
            developer_changes = new_docstring_dismantler.compare_docstrings(
                old_docstring_dismantler
            )
            if len(developer_changes) > 0:
                print(
                    f"=============\n{code_obj.name} in {pathlib.Path(code_obj.filename).stem}\n============="
                )
            for developer_change in developer_changes:
                print(developer_change)
        self.repo.repo.git.checkout("HEAD")
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
        repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True
    )
    # auto_py_doc.main(repo_path="C:\\Users\\Fabian\Github\\bachelor_testing_repo", debug=True)
