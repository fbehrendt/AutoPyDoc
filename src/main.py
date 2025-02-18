from repo_controller import RepoController
from extract_methods_from_change_info import extract_methods_from_change_info
from docstring_builder import DocstringBuilder
from validate_docstring import validate_docstring

def main(repo_path: str = None, debug=False) -> None: # repo_path will be required later
    """ Generates new docstrings for modified parts of the code

    :param repo_path: Path to the repository. Can be local or a GitHub link
    :type repo_path: str
    :param debug: toggle debug mode
    :type debug: boolean
    """

    repo = RepoController(repo_path=repo_path, debug=True)
    code_parts = {}
    changes = repo.get_changes()
    queued_code_parts = []
    for change in changes:
        changed_methods = extract_methods_from_change_info(filename=change["filename"], change_start=change["start"], change_length=change["lines_changed"])
        changed_classes = [] # TODO
        if not debug:
            raise NotImplementedError
        changed_modules = [] # TODO
        if not debug:
            raise NotImplementedError
        for changed_method in changed_methods: # TODO not only methods
            method_id = repo.get_method_id(changed_method)
            method_obj = repo.code_parser.code_representer.get(method_id)
            context = repo.get_context(method_id) # get methods called by this method, get methods calling this this method, if this method is part of a class, get the class, get the module. Instead of the full methods/class/module, their docstring may be used
            old_docstring = repo.code_parser.code_representer.get_docstring(method_id)
            code = repo.code_parser.code_representer.get_code(method_id)
            args_types_exceptions = repo.extract_args_types_exceptions(method_id)
            if len(args_types_exceptions["missing_arg_types"]) > 0:
                # inferr missing types
                if not debug:
                    raise NotImplementedError
            if args_types_exceptions["return_type_missing"]:
                # inferr return type
                if not debug:
                    raise NotImplementedError
            dev_comments = repo.extract_dev_comments(change)
            queued_code_parts.append({
                "id": method_obj.id,
                "type": method_obj.type,
                "name": method_obj.name,
                "parent class": method_obj.class_obj_id,
                "docstring": method_obj.get_docstring(),
                "code": method_obj.code,
                "context": method_obj.get_context(),
                "context docstrings": repo.code_parser.code_representer.get_context_docstrings(method_obj.id),
                "parameters": repo.code_parser.code_representer.get_arguments(method_obj.id),
                "missing parameters": method_obj.get_missing_arg_types(),
                "return missing": method_obj.missing_return_type,
                "exceptions": repo.code_parser.code_representer.get_exceptions(method_obj.id),
            })
            # TODO add instance and class variables to above dict if code_obj.type is class
    # TODO order altered code parts by dependencies
    ordered_code_objects = repo.code_parser.code_representer.objects.values() # TODO
    if not debug:
        raise NotImplementedError
    for code_obj in ordered_code_objects:
        if not debug:
            raise NotImplementedError
        if code_obj.type != "method": # TODO remove
            continue
        # TODO parallelize
        # see if old docstring is up-to-date
        # if up-to-date:
            # continue
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
    for code_obj in ordered_code_objects:
        start_pos, indentation_level, end_pos = repo.identify_code_location(code_obj.id)
        docstring_builder = DocstringBuilder(indentation_level=indentation_level)
        if not debug:
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
            continue
            raise NotImplementedError # TODO
        new_docstring = docstring_builder.build()
        # build docstring
        if not debug:
            raise NotImplementedError
        # merge new docstring with developer comments

        # validate docstring syntax
        errors = validate_docstring(new_docstring)
        # insert new docstring in code_obj
        # insert new docstring in the file
    # validate code integrity
    repo.apply_changes()
    if not debug:
        raise NotImplementedError

if __name__ == "__main__":
    main(repo_path="https://github.com/fbehrendt/bachelor_testing_repo", debug=True)