import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestDocstringInput(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestDocstringInputMethod(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestDocstringInputClass(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestDocstringInputModule(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestDocstringDocstringInputSelectorMethod(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_get_result(self):
        pass
        # TODO

    def test___select_description(self):
        pass
        # TODO

    def test___select_parameters(self):
        pass
        # TODO

    def test___select_return_info(self):
        pass
        # TODO

    def test___select_exceptions(self):
        pass
        # TODO


class TestDocstringInputSelectorModule(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_get_result(self):
        pass
        # TODO

    def test___select_description(self):
        pass
        # TODO

    def test___select_exceptions(self):
        pass
        # TODO


class TestDocstringInputSelectorClass(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_get_result(self):
        pass
        # TODO

    def test___select_description(self):
        pass
        # TODO

    def test___select_class_attributes(self):
        pass
        # TODO

    def test___select_instance_attributes(self):
        pass
        # TODO
