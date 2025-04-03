import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestDocstringBuilder(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_add_description(self):
        pass
        # TODO

    def test_build(self):
        pass
        # TODO


class TestDocstringBuilderMethod(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_add_param(self):
        pass
        # TODO

    def test_add_exception(self):
        pass
        # TODO

    def test_add_return(self):
        pass
        # TODO

    def test_build(self):
        pass
        # TODO


class TestDocstringBuilderClass(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_add_class_attribute(self):
        pass
        # TODO

    def test_add_instance_attribute(self):
        pass
        # TODO

    def test_build(self):
        pass
        # TODO


class TestDocstringBuilderModule(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_add_exception(self):
        pass
        # TODO

    def test_build(self):
        pass
        # TODO


def test_create_docstring():
    pass
    # TODO
