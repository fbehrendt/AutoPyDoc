import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestGptInterface(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_estimate(self):
        pass
        # TODO

    def test_process_batch(self):
        pass
        # TODO
