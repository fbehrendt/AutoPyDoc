import logging

from docstring_builder import create_docstring

from gpt_input import GptOutput
from gpt_interface import GptInterface
from repo_controller import RepoController
from validate_docstring import validate_docstring
from get_context import CodeParser
from code_representation import CodeRepresenter

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
        # TODO validate code integrity
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

            # build docstring
            new_docstring, new_pr_notes = create_docstring(
                code_obj,
                result,
                indentation_level,
                code_representer=self.code_parser.code_representer,
                debug=True,
            )
            self.repo.pr_notes.extend(new_pr_notes)

            # merge new docstring with developer comments
            if not self.debug:
                raise NotImplementedError

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


if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(
        repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True
    )
    # auto_py_doc.main(repo_path="C:\\Users\\Fabian\Github\\bachelor_testing_repo", debug=True)
