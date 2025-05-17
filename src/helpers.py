import sys
import os
import ast
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