import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestGptInputCodeObject(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptInputMethodObject(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptInputClassObject(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptInputModuleObject(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptOutput(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptOutputMethod(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptOutputClass(unittest.TestCase):
    def test_init(self):
        pass
        # TODO


class TestGptOutputModule(unittest.TestCase):
    def test_init(self):
        pass
        # TODO
