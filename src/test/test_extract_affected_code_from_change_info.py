import pathlib
import sys
import os
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


def test_extract_methods_from_change_info():
    # TODO
    pass


def test_extract_classes_from_change_info():
    # TODO
    pass


def test_extract_module_from_change_info():
    # TODO
    pass
