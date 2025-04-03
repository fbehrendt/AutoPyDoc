import pathlib
import sys
import os
import unittest
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)


class TestRepoController(unittest.TestCase):
    def test_init(self):
        pass
        # TODO

    def test_get_files_in_repo(self):
        pass
        # TODO

    def test_get_latest_commit(self):
        pass
        # TODO

    def test_clear_working_dir(self):
        pass
        # TODO

    def test_pull_repo(self):
        pass
        # TODO

    def test_get_changes(self):
        pass
        # TODO

    def test_identify_docstring_location(self):
        pass
        # TODO

    def test_save_file_for_comparison(self):
        pass
        # TODO

    def test_insert_docstring(self):
        pass
        # TODO

    def test_remove_comments(self):
        pass
        # TODO

    def test_validate_code_integrity(self):
        pass
        # TODO

    def test_update_latest_commit(self):
        pass
        # TODO

    def test_commit_to_new_branch(self):
        pass
        # TODO

    def test_create_pull_request(self):
        pass
        # TODO

    def test_apply_changes(self):
        pass
        # TODO
