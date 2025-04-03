import pathlib
import sys
import os
import logging
import pytest
import unittest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestDocstringDismantler(unittest.TestCase):
    def test_docstring_dismantler_init():
        pass
        # TODO

    def test_docstring_dismantler_apply_pattern():
        pass
        # TODO

    def test_docstring_dismantler_compare_docstrings():
        pass
        # TODO


def test_compare_docstrings():
    pass
    # TODO
