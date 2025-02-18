from repo_controller import RepoController
from extract_methods_from_change_info import extract_methods_from_change_info
from docstring_builder import DocstringBuilder
from validate_docstring import validate_docstring
import gpt_interface

class AutoPyDoc():
    def __init__(self):
        pass

    def main(self, repo_path: str = None, debug=False) -> None: # repo_path will be required later
        """ Generates new docstrings for modified parts of the code

        :param repo_path: Path to the repository. Can be local or a GitHub link
        :type repo_path: str
        :param debug: toggle debug mode
        :type debug: boolean
        """

        self.repo = RepoController(repo_path=repo_path, debug=debug)
        self.debug = debug

        self.code_parts = {}
        self.changes = self.repo.get_changes()
        self.queued_code_ids = []

        for change in self.changes:
            changed_methods = extract_methods_from_change_info(filename=change["filename"], change_start=change["start"], change_length=change["lines_changed"])
            changed_classes = [] # TODO
            if not self.debug:
                raise NotImplementedError
            changed_modules = [] # TODO
            if not self.debug:
                raise NotImplementedError
            for changed_method in changed_methods: # TODO not only methods
                method_id = self.repo.get_method_id(changed_method)
                self.queued_code_ids.append(method_id)
                method_obj = self.repo.code_parser.code_representer.get(method_id)
                method_obj.outdated = True
                context = self.repo.get_context(method_id) # get methods called by this method, get methods calling this this method, if this method is part of a class, get the class, get the module. Instead of the full methods/class/module, their docstring may be used
                old_docstring = self.repo.code_parser.code_representer.get_docstring(method_id)
                code = self.repo.code_parser.code_representer.get_code(method_id)
                args_types_exceptions = self.repo.extract_args_types_exceptions(method_id)
                if len(args_types_exceptions["missing_arg_types"]) > 0:
                    # inferr missing types
                    if not self.debug:
                        raise NotImplementedError
                if args_types_exceptions["return_type_missing"]:
                    # inferr return type
                    if not self.debug:
                        raise NotImplementedError
                dev_comments = self.repo.extract_dev_comments(change)

        first_batch = self.generate_next_batch()
        self.queries_sent_to_gpt = len(first_batch)
        gpt_interface.send_batch(first_batch, callback=self.process_gpt_result)

    def generate_next_batch(self):
        ids = [id for id in self.queued_code_ids if not self.repo.code_parser.code_representer.depends_on_outdated_code(id)]
        batch = []
        for id in ids:
            method_obj = self.repo.code_parser.code_representer.get(id)
            # TODO add instance and class variables to above dict if code_obj.type is class
            batch.append({
                "id": method_obj.id,
                "type": method_obj.type,
                "name": method_obj.name,
                "parent class": method_obj.class_obj_id,
                "docstring": method_obj.get_docstring(),
                "code": method_obj.code,
                "context": method_obj.get_context(),
                "context docstrings": self.repo.code_parser.code_representer.get_context_docstrings(method_obj.id),
                "parameters": self.repo.code_parser.code_representer.get_arguments(method_obj.id),
                "missing parameters": method_obj.get_missing_arg_types(),
                "return missing": method_obj.missing_return_type,
                "exceptions": self.repo.code_parser.code_representer.get_exceptions(method_obj.id),
            })
        return batch

    def process_gpt_result(self, result):
        self.queries_sent_to_gpt -= 1
        code_obj = self.repo.code_parser.code_representer.get(result["id"])
        if "no_change_necessary" in result.keys() and result["no_change_necessary"] == True:
            self.repo.code_parser.code_representer.update_docstring(code_obj.id, code_obj.docstring)
        if not self.debug:
            raise NotImplementedError
        if code_obj.type != "method": # TODO remove
            raise NotImplementedError
        # TODO parallelize
        # flag developer comments
        # if only_comments_changed:
            # continue
        # generate description
        # inferr missing arg/return types
        for missing_param in code_obj.missing_arg_types:
            for i in range(len(code_obj.arguments)):
                if code_obj.arguments[i]["name"] == missing_param:
                    code_obj.arguments[i]["type"] = "MOCK inferred type" # TODO
        if code_obj.missing_return_type:
            code_obj.return_type = "MOCK return type"
        # generate parameter descriptions
        # generate exception descriptions (?)
        start_pos, indentation_level, end_pos = self.repo.identify_code_location(code_obj.id)
        docstring_builder = DocstringBuilder(indentation_level=indentation_level)
        if not self.debug:
            raise NotImplementedError
        docstring_builder.add_description("MOCK This part of code (probably) does something.") # TODO
        if code_obj.type == "method":
            for param in code_obj.arguments:
                if "default" in param.keys():
                    docstring_builder.add_param(param_name=param["name"], param_type=param["type"], param_default=param["default"], param_description="MOCK parameter description") # TODO
                else:
                    docstring_builder.add_param(param_name=param["name"], param_type=param["type"], param_description="MOCK parameter description") # TODO
            for exception in code_obj.exceptions:
                docstring_builder.add_exception(exception_name=exception, exception_description="MOCK exception description") # TODO
            docstring_builder.add_return(return_type=code_obj.return_type, return_description="MOCK return description") # TODO
        else:
            raise NotImplementedError # TODO
        new_docstring = docstring_builder.build()
        # build docstring
        if not self.debug:
            raise NotImplementedError
        # merge new docstring with developer comments

        # validate docstring syntax
        errors = validate_docstring(new_docstring)
        # insert new docstring in code_obj
        # insert new docstring in the file
        # if parts are still outdated
        if len([item for item in self.queued_code_ids if self.repo.code_parser.code_representer.get(item["id"]).outdated]):
            next_batch = self.get_next_batch()
            self.queries_sent_to_gpt += len(next_batch)
            gpt_interface.send_batch(next_batch, callback=self.process_gpt_result)
        elif self.queries_sent_to_gpt < 1:
            missing_items = [item for item in self.queued_code_ids if item.outdated]
            if len(missing_items) > 0:
                raise NotImplementedError
            # TODO validate code integrity
            self.repo.apply_changes()
            if not self.debug:
                raise NotImplementedError
                

if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True)