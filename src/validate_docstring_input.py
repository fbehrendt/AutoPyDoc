from code_representation import (
    CodeObject,
    CodeRepresenter,
)
from docstring_input_selector import (
    DocstringInput,
    DocstringInputMethod,
    DocstringInputClass,
    DocstringInputModule,
)
from repo_controller import UnknownCodeObjectError


def validate_docstring_input(
    docstring_input: DocstringInput, code_representer: CodeRepresenter, repo_path: str
):
    def generate_parent_chain(code_obj, code_representer: CodeRepresenter):
        parent_chain = code_obj.name
        code_obj_2 = code_obj
        while code_obj_2.parent_id is not None:
            code_obj_2 = code_representer.get(code_obj_2.parent_id)
            parent_chain = code_obj_2.name + "->" + parent_chain
        return parent_chain

    def get_rel_filename(abs_filename, repo_path):
        return abs_filename.lstrip(repo_path)[1].lstrip("/").lstrip("\\")

    code_obj = code_representer.get(docstring_input.id)
    pr_notes = []
    if isinstance(docstring_input, DocstringInputMethod):
        # check description
        if isinstance(docstring_input.description, bool) and not docstring_input.description:
            pr_notes.append(
                f"Please manully add a description for method {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
            )
            docstring_input.description = "<failed to generate>"
        # arguments
        for param in docstring_input.arguments.keys():
            if param == "self":  # skip self
                continue
            if (
                isinstance(docstring_input.arguments[param], bool)
                and not docstring_input.arguments[param]
            ):
                pr_notes.append(
                    f"Please manully add a description for parameter {param} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.arguments[param] = "<failed to generate>"
            if (
                isinstance(docstring_input.argument_types[param], bool)
                and not docstring_input.argument_types[param]
            ):
                pr_notes.append(
                    f"Unknown type for param {param} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.argument_types[param] = "<unknown>"
        # return
        if code_obj.return_type is not None:
            if (
                isinstance(docstring_input.return_description, bool)
                and not docstring_input.return_description
            ):
                pr_notes.append(
                    f"Please manully add a return description in method {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.return_description = "<failed to generate>"
            if isinstance(docstring_input.return_type, bool) and not docstring_input.return_type:
                pr_notes.append(
                    f"Please manully add a return type in method {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.return_type = "<failed to generate>"
        # exceptions
        for exception in docstring_input.exceptions.keys():
            if (
                isinstance(docstring_input.exceptions[exception], bool)
                and not docstring_input.exceptions[exception]
            ):
                pr_notes.append(
                    f"Please manully add a description for exception {exception} in method {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.exceptions[exception] = "<failed to generate>"
    elif isinstance(docstring_input, DocstringInputClass):
        # description
        if isinstance(docstring_input.description, bool) and not docstring_input.description:
            pr_notes.append(
                f"Please manully add a description for class {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
            )
            docstring_input.description = "<failed to generate>"
        # class attributes
        for class_attribute_name in docstring_input.class_attributes.keys():
            if (
                isinstance(
                    docstring_input.class_attributes[class_attribute_name],
                    bool,
                )
                and not docstring_input.class_attributes[class_attribute_name]
            ):
                pr_notes.append(
                    f"Please manully add a description for class attribute {class_attribute_name} for class {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.class_attributes[class_attribute_name] = "<failed to generate>"
            if (
                isinstance(
                    docstring_input.class_attribute_types[class_attribute_name],
                    bool,
                )
                and not docstring_input.class_attribute_types[class_attribute_name]
            ):
                pr_notes.append(
                    f"Unknown type for class attribute {class_attribute_name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.class_attribute_types[class_attribute_name] = "<unknown>"
        # instance attributes
        for instance_attribute_name in docstring_input.instance_attributes.keys():
            if (
                isinstance(
                    docstring_input.instance_attributes[instance_attribute_name],
                    bool,
                )
                and not docstring_input.instance_attributes[instance_attribute_name]
            ):
                pr_notes.append(
                    f"Please manully add a description for instance attribute {instance_attribute_name} for class {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.instance_attributes[instance_attribute_name] = (
                    "<failed to generate>"
                )
            else:
                docstring_input.instance_attributes[instance_attribute_name] = (
                    docstring_input.instance_attributes[instance_attribute_name]
                )
            if (
                isinstance(
                    docstring_input.instance_attribute_types[instance_attribute_name],
                    bool,
                )
                and not docstring_input.instance_attribute_types[instance_attribute_name]
            ):
                pr_notes.append(
                    f"Unknown type for class attribute {instance_attribute_name} in {get_rel_filename(code_obj.filename, repo_path)}->{generate_parent_chain(code_obj=code_obj, code_representer=code_representer)}"
                )
                docstring_input.instance_attribute_types[instance_attribute_name] = "<unknown>"
    elif isinstance(docstring_input, DocstringInputModule):
        # description
        if isinstance(docstring_input.description, bool) and not docstring_input.description:
            pr_notes.append(
                f"Please manully add a description for module {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}"
            )
            docstring_input.description = "<failed to generate>"
        # exceptions
        for exception in docstring_input.exceptions.keys():
            if (
                isinstance(docstring_input.exceptions[exception], bool)
                and not docstring_input.exceptions[exception]
            ):
                pr_notes.append(
                    f"Please manully add a description for exception {exception} in module {code_obj.name} in {get_rel_filename(code_obj.filename, repo_path)}"
                )
                docstring_input.exceptions[exception] = "<failed to generate>"
    else:
        raise UnknownCodeObjectError
    return docstring_input, pr_notes
