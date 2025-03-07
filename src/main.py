from code_representation import ClassObject, MethodObject
from docstring_builder import create_docstring
from extract_affected_code_from_change_info import (
    extract_classes_from_change_info,
    extract_methods_from_change_info,
)
from gpt_interface import GptInterface
from repo_controller import RepoController
from validate_docstring import validate_docstring


class AutoPyDoc:
    def __init__(self):
        pass

    def main(
        self, repo_path: str = None, pull_request_token=None, debug=False
    ) -> None:  # repo_path will be required later
        """Generates new docstrings for modified parts of the code

        :param repo_path: Path to the repository. Can be local or a GitHub link
        :type repo_path: str
        :param debug: toggle debug mode
        :type debug: boolean
        """

        # initialize gpt interface early to fail early if model is unavailable or unable to load
        # TODO: make name configurable (see factory for available model names)
        self.gpt_interface = GptInterface("local_deepseek")

        # pull repo, create code representation, create dependencies
        self.repo = RepoController(
            repo_path=repo_path, pull_request_token=pull_request_token, debug=debug
        )
        self.debug = debug
        self.queued_code_ids = []

        # get changes between last commit the tool ran for and now
        self.changes = self.repo.get_changes()

        for change in self.changes:
            changed_methods = extract_methods_from_change_info(
                filename=change["filename"],
                change_start=change["start"],
                change_length=change["lines_changed"],
            )
            changed_classes = extract_classes_from_change_info(
                filename=change["filename"],
                change_start=change["start"],
                change_length=change["lines_changed"],
            )
            if not self.debug:
                raise NotImplementedError
            changed_modules = []  # TODO
            if not self.debug:
                raise NotImplementedError
            for changed_method in changed_methods:  # TODO not only methods
                method_id = self.repo.get_method_id(changed_method)
                self.queued_code_ids.append(method_id)
                method_obj = self.repo.code_parser.code_representer.get(method_id)
                method_obj.outdated = True
                method_obj.dev_comments = self.repo.extract_dev_comments(method_obj)

            for changed_class in changed_classes:  # TODO not only methods
                class_id = self.repo.get_class_id(changed_class)
                self.queued_code_ids.append(class_id)
                class_obj = self.repo.code_parser.code_representer.get(class_id)
                class_obj.outdated = True
                class_obj.dev_comments = self.repo.extract_dev_comments(class_obj)

        first_batch = self.generate_next_batch()
        self.queries_sent_to_gpt = len(first_batch)
        if self.queries_sent_to_gpt == 0:
            print("No need to do anything")
            quit()
        self.gpt_interface.process_batch(first_batch, callback=self.process_gpt_result)

    def generate_next_batch(self, ignore_dependencies=False):
        ids = [
            id
            for id in self.queued_code_ids
            if ignore_dependencies
            or not self.repo.code_parser.code_representer.depends_on_outdated_code(id)
            and not self.repo.code_parser.code_representer.get(id).send_to_gpt
        ]
        batch = []
        for id in ids:
            code_obj = self.repo.code_parser.code_representer.get(id)
            code_obj.send_to_gpt = True
            # TODO add instance and class variables to above dict if code_obj.type is class
            batch.append(
                code_obj.get_gpt_input(
                    code_representer=self.repo.code_parser.code_representer
                )
            )
        return batch

    def process_gpt_result(self, result):
        self.queries_sent_to_gpt -= 1
        print("Received", result["id"])
        print("Waiting for", self.queries_sent_to_gpt, "more results")
        code_obj = self.repo.code_parser.code_representer.get(result["id"])
        if not result["no_change_necessary"]:
            if not self.debug:
                raise NotImplementedError
            if code_obj.type != "method" and code_obj.type != "class":  # TODO remove
                raise NotImplementedError
            start_pos, indentation_level, end_pos = (
                self.repo.identify_docstring_location(code_obj.id)
            )

            # build docstring
            new_docstring = create_docstring(
                code_obj, result, indentation_level, debug=True
            )

            # merge new docstring with developer comments
            if not self.debug:
                raise NotImplementedError

            # validate docstring syntax
            errors = validate_docstring(new_docstring)
            if len(errors) > 0:
                if not self.debug:
                    raise NotImplementedError

            # insert new docstring in the file
            self.repo.insert_docstring(
                filename=code_obj.filename,
                start=start_pos,
                end=end_pos,
                new_docstring=new_docstring,
            )
            code_obj.is_updated = True
        code_obj.outdated = False
        # if parts are still outdated
        next_batch = self.generate_next_batch()
        if len(next_batch) > 0:
            self.queries_sent_to_gpt += len(next_batch)
            self.gpt_interface.process_batch(
                next_batch, callback=self.process_gpt_result
            )
        # if every docstring is updated
        elif self.queries_sent_to_gpt < 1:
            missing_items = [
                id
                for id in self.queued_code_ids
                if self.repo.code_parser.code_representer.get(id).outdated
            ]
            if len(missing_items) > 0:
                print("Some parts are still missing updates")
                print("\n".join(missing_items))
                next_batch = self.generate_next_batch(ignore_dependencies=True)
                if len(next_batch) > 0:
                    self.queries_sent_to_gpt += len(next_batch)
                    self.gpt_interface.process_batch(
                        next_batch, callback=self.process_gpt_result
                    )
                if not self.debug:
                    raise NotImplementedError

            # TODO validate code integrity
            if not self.debug:
                raise NotImplementedError

            changed_files = []
            for filename in [
                code_obj.filename
                for code_obj in self.repo.code_parser.code_representer.objects.values()
                if code_obj.is_updated
            ]:
                if filename not in changed_files:
                    changed_files.append(filename)
            self.repo.apply_changes(changed_files=changed_files)
            if not self.debug:
                raise NotImplementedError


if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(
        repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True
    )
    # auto_py_doc.main(repo_path="C:\\Users\\Fabian\Github\\bachelor_testing_repo", debug=True)
