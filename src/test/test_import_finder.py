import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestImportFinder(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_add_file(self):
        pass
        # TODO

    def test_resolve_external_call(self):
        pass
        # TODO

    def test_resolve_import_to_file(self):
        pass
        # TODO
