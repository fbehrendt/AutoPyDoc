import re
import sys
import os
import ast

import json5
import astunparse


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
