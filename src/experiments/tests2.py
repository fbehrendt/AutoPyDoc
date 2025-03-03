import os
import pathlib
import re
import sys
import ast

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)

from src.get_context import CodeParser
from src.code_representation import CodeRepresenter


def resolve_variable_chain_by_file(
    code_representer,
    filename="src\experiments\\ast_tests.py",
    variable_chain="var_B.var_class_a.func_d",
):
    dir = pathlib.Path().resolve()
    full_path = os.path.join(dir, filename)
    with open(full_path, "r") as f:
        content = f.read()
        return resolve_variable_chain(
            code_representer=code_representer,
            content=content.split("\n"),
            variable_chain=variable_chain,
            full_path=full_path,
        )


def resolve_variables_with_ast(content):
    variable_chain = variable_chain.split(".")
    current_var = variable_chain.pop(0)
    resolved_assignments = []
    for node in ast.walk(ast.parse(content)):
        if isinstance(node, ast.Assign):
            print()
            var_chain_value = []
            if isinstance(node.value, ast.Constant):
                value = node.value.value
            elif isinstance(node.value.func, ast.Name):
                value = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):
                value = node.value.func.attr
                if hasattr(node.value.func, "value"):
                    sub_node = node.value.func.value
                while True:
                    if isinstance(sub_node, ast.Name):
                        name = sub_node.id
                    elif isinstance(sub_node, ast.Attribute):
                        name = sub_node.attr
                    else:
                        raise NotImplementedError
                    name_type = None
                    if name in [
                        assignment["target_name"] for assignment in resolved_assignments
                    ]:
                        for assignment in resolved_assignments:
                            if assignment["target_name"] == name:
                                name_type = assignment["value"]
                    var_chain_value.append({name: name_type})  # TODO is this ever used?

                    if hasattr(sub_node, "value"):
                        sub_node = sub_node.value
                    else:
                        break
            else:
                raise NotImplementedError
            targets = []
            for target in node.targets:
                var_chain_target = []
                if hasattr(target, "value"):
                    sub_node = target.value
                    while True:
                        if isinstance(sub_node, ast.Name):
                            var_chain_target.insert(0, {sub_node.id: None})
                        elif isinstance(sub_node, ast.Attribute):
                            var_chain_target.insert(
                                0, {sub_node.attr: None}
                            )  # TODO is this ever used?

                        if hasattr(sub_node, "value"):
                            sub_node = sub_node.value
                        else:
                            break

                if isinstance(target, ast.Name):
                    target_name = target.id
                elif isinstance(target, ast.Attribute):
                    target_name = target.attr
                else:
                    raise NotImplementedError
                targets.append(
                    {"name": target_name, "var_chain_target": var_chain_target}
                )
            print(
                "Targets",
                ", ".join([target["name"] for target in targets]),
                "value",
                value,
                "var_chain",
                var_chain_value,
            )
            for target in targets:
                for var in target["var_chain_target"]:
                    print(list(var.keys()))
                    if list(var.keys())[0] in [
                        assignment["target_name"] for assignment in resolved_assignments
                    ]:
                        for assignment in resolved_assignments:
                            if assignment["target_name"] == list(var.keys())[0]:
                                for i, item in enumerate(target["var_chain_target"]):
                                    if list(item.keys())[0] == list(var.keys())[0]:
                                        target["var_chain_target"][i][
                                            list(var.keys())[0]
                                        ] = assignment["value"]
                resolved_assignments.append(
                    {
                        "target_name": target["name"],
                        "var_chain_target": target["var_chain_target"],
                        "value": value,
                        "var_chain_value": var_chain_value,
                    }
                )
            print()
    return resolved_assignments


def resolve_variable_chain(code_representer, content, variable_chain, full_path):
    # currently fails to handle conditional assignments, as it returns when the first match is found
    for line in content:
        if line.lstrip().startswith(variable_chain):
            print("variable chain usage found in line", line)
        if line.lstrip().strip("self.").startswith(variable_chain.split(".")[0]):
            if (
                line.lstrip()
                .strip("self.")
                .lstrip(variable_chain.split(".")[0])
                .lstrip()
                .startswith("=")
            ):
                print("variable chain assignment found in line", line)
                identified_source = (
                    line.lstrip()
                    .strip("self.")
                    .lstrip(variable_chain.split(".")[0])
                    .lstrip()
                    .lstrip("=")
                    .lstrip()
                    .split("#")[0]
                    .rstrip()
                )
                if (
                    "." in identified_source.split("(")[0]
                ):  # case solve right side of assignment
                    # make sure the period is not part of a string
                    pattern = r"\w+"
                    string = identified_source.split("(")[0].split(".")
                    if re.fullmatch(pattern=pattern, string=string):
                        return resolve_variable_chain(
                            code_representer=code_representer,
                            content=content,
                            variable_chain=".".join(
                                variable_chain.split(".")[1:], full_path=full_path
                            ),
                        )
                elif "(" in identified_source:  # case class or method call
                    identified_source = identified_source.split("(")[0]
                    # raise NotImplementedError
                    # TODO resolve method or class
                    # resolve import
                    # get code_obj
                    print(
                        "trying to get code_obj for", identified_source, "in line", line
                    )
                    full_path = full_path  # differs if imported
                    id_case_method = full_path + "_method_" + identified_source
                    id_case_class = full_path + "_class_" + identified_source
                    if id_case_method in code_representer.objects.keys():
                        code_obj = code_representer.objects[id_case_method]
                    elif id_case_class in code_representer.objects.keys():
                        code_obj = code_representer.objects[id_case_class]
                    else:
                        raise NotImplementedError
                    remaining_variable_chain = ".".join(variable_chain.split(".")[1:])
                    if remaining_variable_chain != "":
                        if code_obj.type != "class":
                            raise Exception(
                                "Trying to access variable in method from outside"
                            )
                        result_id = resolve_variable_chain(
                            code_representer=code_representer,
                            content=code_obj.code.split("\n"),
                            variable_chain=".".join(variable_chain.split(".")[1:]),
                            full_path=full_path,
                        )
                        return result_id
                    else:
                        return code_obj.id
                else:  # case assignment is not class or method call
                    raise NotImplementedError
        else:
            if line.lstrip().startswith(
                "def " + variable_chain.split(".")[0]
            ):  # TODO also .lstrip('(') ?
                # get code_obj
                method_id = full_path + "_method_" + variable_chain.split(".")[0]
                if method_id in code_representer.objects.keys():
                    code_obj = code_representer.objects[method_id]
                    remaining_variable_chain = ".".join(variable_chain.split(".")[1:])
                    if remaining_variable_chain != "":
                        result_id = resolve_variable_chain(
                            code_representer=code_representer,
                            content=code_obj.code.split("\n"),
                            variable_chain=remaining_variable_chain,
                            full_path=full_path,
                        )
                        return result_id
                    else:
                        return code_obj.id
                else:
                    raise Exception(
                        f"code_obj with id {method_id} not found in code_representer"
                    )
    raise Exception(
        f"Could not resolve chain. {remaining_variable_chain} not found in {content}"
    )


if __name__ == "__main__":
    code_parser = CodeParser(CodeRepresenter(), debug=True)
    code_parser.add_file(filename="src\experiments\\ast_tests.py")
    code_parser.create_dependencies()
    result = resolve_variable_chain_by_file(
        code_representer=code_parser.code_representer
    )
    print("var_B.var_class_a.func_d is class/method", result)
