import re
import sys
import os
import ast

import json5
import astunparse

from code_representation import CodeRepresenter


def remove_comments(code):
    sys.stderr = open(os.devnull, "w")
    lines = astunparse.unparse(ast.parse(code)).split("\n")
    sys.stderr = sys.__stderr__
    content = []
    for line in lines:
        if line.lstrip()[:1] not in ("'", '"'):
            content.append(line)
    content = "\n".join(content)
    return content


def parse_first_json_object(s: str):
    """
    Extract and parse the first JSON5 object in the string.
    Returns the parsed object (e.g. a dict), or raises ValueError if none found.
    """

    # 1) Find the first opening brace
    m = re.search(r"\{", s)
    if not m:
        raise ValueError("No JSON object found")

    start = m.start()

    # 2) For each closing brace, try to parse substring
    for idx, ch in enumerate(s[start:], start=start):
        if ch == "}":
            candidate = s[start : idx + 1]
            try:
                return json5.loads(candidate)
            except Exception:
                # Not a complete/correct object yet—keep scanning
                pass

    # 3) If we exhaust the string without success, it wasn't valid JSON5
    raise ValueError("Couldn't parse a complete JSON object")


def get_rel_filename(abs_filename, repo_path):
    return abs_filename.removeprefix(repo_path).lstrip("/").lstrip("\\\\")


def generate_parent_chain(code_obj, code_representer: CodeRepresenter):
    parent_chain = code_obj.code_type + " " + code_obj.name
    code_obj_2 = code_obj
    while code_obj_2.parent_id is not None and code_obj_2.parent_id is not code_obj_2.module_id:
        code_obj_2 = code_representer.get(code_obj_2.parent_id)
        parent_chain = code_obj_2.code_type + " " + code_obj_2.name + " -> " + parent_chain
    return parent_chain
