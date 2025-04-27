import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestAutoPyDoc(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_main(self):
        pass
        # TODO

    def test_process_gpt_result(self):
        pass
        # TODO

    def test_print_diff(self):
        pass
        # TODO

    def test_extract_dev_comments(self):
        pass
        # TODO
