import logging
import os

from dotenv import load_dotenv

from code_representation import ClassObject, CodeRepresenter, MethodObject, ModuleObject
from docstring_builder import create_docstring
from docstring_input_selector import (
    DocstringInputSelectorClass,
    DocstringInputSelectorMethod,
    DocstringInputSelectorModule,
)
from get_context import CodeParser
from gpt_input import GptOutput
from gpt_interface import GptInterface
from repo_controller import CodeIntegrityViolationError, RepoController
from validate_docstring import validate_docstring
from validate_docstring_input import validate_docstring_input

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

        if "_AutoPyDoc" in branch:
            self.logger.info("Attempt to run the tool on a branch created by it. Aborting!")
            quit()

        # Initialize gpt interface with the chosen strategy and its parameters early to fail early if model is unavailable or unable to load
        self.logger.info(f"Using {model_strategy_name} strategy.")
        self.gpt_interface = GptInterface(model_strategy_name, **model_strategy_params)

        # pull repo, create code representation, create dependencies
        self.debug = debug

        # handles interactions with the target repository
        self.repo_controller = RepoController(
            repo_path=repo_path,
            pull_request_token=pull_request_token,
            username=username,
            branch=branch,
            logger=self.logger,
            debug=debug,
            repo_owner=repo_owner,
        )

        # creates code representation
        # extracts class and method calls, arguments, return types, exceptions, attributes and outdated code
        self.code_parser = CodeParser(
            code_representer=CodeRepresenter(),
            repo_controller=self.repo_controller,
            logger=self.logger,
            debug=True,
        )
        self.code_parser.detect_outdated_code()

        full_input_for_estimation = self.code_parser.code_representer.generate_next_batch(
            ignore_dependencies=True, dry=True
        )
        self.gpt_interface.estimate(full_input=full_input_for_estimation)
        first_batch = self.code_parser.code_representer.generate_next_batch()

        if len(self.code_parser.code_representer.get_sent_to_gpt_ids()) == 0:
            self.logger.info("No need to do anything")
            quit()
        self.gpt_interface.process_batch(first_batch, callback=self.process_gpt_result)

        # if parts are still outdated
        while len(self.code_parser.code_representer.get_outdated_ids()) > 0:
            missing_items = self.code_parser.code_representer.get_outdated_ids()
            self.logger.debug("Some parts are still missing updates")
            self.logger.debug("\n".join([str(item) for item in missing_items]))
            # force generate all, ignore dependencies
            next_batch = self.code_parser.code_representer.generate_next_batch(
                ignore_dependencies=True
            )
            if len(next_batch) > 0:
                self.gpt_interface.process_batch(next_batch, callback=self.process_gpt_result)

        # if every docstring is updated
        if not self.repo_controller.validate_code_integrity():
            self.logger.fatal("Code integrity no longer given!!! aborting")
            raise CodeIntegrityViolationError("Code integrity no longer given!!! aborting")
            quit()  # saveguard in case someone tries to catch the exception and continue anyways
        self.logger.info("Code integrity validated")

        self.repo_controller.apply_changes(
            changed_files=self.code_parser.code_representer.get_changed_files()
        )
        self.logger.info("Finished successfully")

    def process_gpt_result(self, result: GptOutput) -> None:
        self.logger.debug(f"Received {str(result.id)}")
        self.logger.debug(
            f"Waiting for {str(len(self.code_parser.code_representer.get_sent_to_gpt_ids()))} more results"
        )
        code_obj = self.code_parser.code_representer.get(result.id)

        start_pos, indentation_level, end_pos = self.repo_controller.identify_docstring_location(
            code_obj.id, code_representer=self.code_parser.code_representer
        )

        if result.no_change_necessary:
            code_obj.outdated = False
        else:
            # merge new docstring with developer comments
            developer_docstring_changes = self.repo_controller.extract_dev_comments(code_obj)
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
                repo_path=self.repo_controller.working_dir,
            )
            self.repo_controller.pr_notes.extend(new_pr_notes)

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
                self.repo_controller.insert_docstring(
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


if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()

    auto_py_doc.main(
        repo_path="https://github.com/fbehrendt/bachelor_testing_repo_small",
        username="fbehrendt",
        model_strategy_name="mock",
        model_strategy_params={
            "context_size": 2**13,
            "ollama_host": os.getenv("OLLAMA_HOST", default="http://localhost:7280/"),
        },
        branch="module_docstrings",
        repo_owner="fbehrendt",
        debug=False,
    )

    # auto_py_doc.main(repo_path="C:\\Users\\Fabian\Github\\bachelor_testing_repo", debug=True)
