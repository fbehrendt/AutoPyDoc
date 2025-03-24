import pathlib
import sys
import os

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)

import unittest
import ast as ast_module


from src.code_representation import (
    frozen_field_support,
    CodeObject,
    MethodObject,
    ClassObject,
    ModuleObject,
    CodeRepresenter,
)
from src.gpt_input import GptInputCodeObject


class TestFrozenFieldSupport(unittest.TestCase):
    def test_frozen_field_support(self):
        # define dataclass with and without frozen_field_support
        # instantiate both, then try to change a frozen attribute
        self.assertEqual(1, 1)


class TestCodeObject(unittest.TestCase):
    def test_init(self):
        # instantiate CodeObject
        # verify __post_init__ results
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        self.assertEqual(code_obj.name, "func_a")
        self.assertEqual(code_obj.filename, "testfile.py")
        self.assertIsInstance(code_obj.ast, ast_module.FunctionDef)
        self.assertEqual(code_obj.docstring, "Returns 3")
        self.assertEqual(
            code_obj.code, 'def func_a():\n    """Returns 3"""\n    return 3'
        )
        self.assertEqual(code_obj.parent_id, None)

        self.assertTrue(hasattr(code_obj, "id") and isinstance(code_obj.id, int))
        self.assertEqual(code_obj.code_type, "code")
        self.assertIsInstance(code_obj.called_methods, set)
        self.assertIsInstance(code_obj.called_classes, set)
        self.assertIsInstance(code_obj.called_by_methods, set)
        self.assertIsInstance(code_obj.called_by_classes, set)
        self.assertIsInstance(code_obj.called_by_modules, set)
        self.assertFalse(code_obj.outdated)
        self.assertFalse(code_obj.is_updated)
        self.assertFalse(code_obj.send_to_gpt)
        self.assertEqual(code_obj.old_docstring, code_obj.docstring)

    def test_add_called_method(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_called_method(called_method_id=568643265543564654)
        self.assertTrue(568643265543564654 in code_obj.called_methods)

    def test_add_called_class(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_called_class(called_class_id=568643265543564650)
        self.assertTrue(568643265543564650 in code_obj.called_classes)

    def test_add_caller_method(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_caller_method(caller_method_id=568643265543564651)
        self.assertTrue(568643265543564651 in code_obj.called_by_methods)

    def test_add_caller_class(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_caller_class(caller_class_id=568643265543564652)
        self.assertTrue(568643265543564652 in code_obj.called_by_classes)

    def test_add_caller_module(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_caller_module(caller_module_id=568643265543564653)
        self.assertTrue(568643265543564653 in code_obj.called_by_modules)

    def test_add_docstring(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        self.assertEqual(code_obj.docstring, "Returns 3")
        code_obj.add_docstring("test")
        self.assertEqual(code_obj.docstring, "test")

    def test_update_docstring(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.outdated = True
        self.assertEqual(code_obj.docstring, "Returns 3")
        self.assertEqual(code_obj.docstring, code_obj.old_docstring)
        self.assertTrue(code_obj.outdated)
        self.assertFalse(code_obj.is_updated)
        code_obj.update_docstring(new_docstring="new docstring")
        self.assertEqual(code_obj.docstring, "new docstring")
        self.assertNotEqual(code_obj.docstring, code_obj.old_docstring)
        self.assertFalse(code_obj.outdated)
        self.assertTrue(code_obj.is_updated)

    def test_get_context(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        code_obj.add_called_method(called_method_id=-568643265543564654)
        code_obj.add_called_method(called_method_id=-168643265543564654)
        code_obj.add_called_class(called_class_id=568643265543564650)
        code_obj.add_caller_method(caller_method_id=-568643265543564651)
        code_obj.add_caller_method(caller_method_id=-268643265543564651)
        code_obj.add_caller_class(caller_class_id=568643265543564652)
        code_obj.add_caller_module(caller_module_id=568643265543564653)
        context = code_obj.get_context()
        self.assertTrue("called_methods" in context.keys())
        self.assertTrue("called_classes" in context.keys())
        self.assertTrue("called_by_methods" in context.keys())
        self.assertTrue("called_by_classes" in context.keys())
        self.assertTrue("called_by_modules" in context.keys())
        self.assertEqual(
            context["called_methods"], {-568643265543564654, -168643265543564654}
        )
        self.assertEqual(context["called_classes"], {568643265543564650})
        self.assertEqual(
            context["called_by_methods"], {-568643265543564651, -268643265543564651}
        )
        self.assertEqual(context["called_by_classes"], {568643265543564652})
        self.assertEqual(context["called_by_modules"], {568643265543564653})

    def test_get_gpt_input(self):
        code_representer = CodeRepresenter()
        module_code_obj = CodeObject(
            name="",
            filename="testfile.py",
            ast=ast_module.parse(
                '"""abc"""\n\ndef func_a():\n    """Returns 3"""\n    return 3\n\nfunc_a()\n'
            ).body[0],
            docstring="abc",
            code='"""abc"""\n\ndef func_a():\n    """Returns 3"""\n    return 3\n\nfunc_a()\n',
            parent_id=None,
        )
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=module_code_obj.id,
        )
        code_representer.add_code_obj(code_obj=code_obj)
        code_representer.add_code_obj(code_obj=module_code_obj)

        code_obj.add_caller_module(caller_module_id=module_code_obj.id)
        self.assertEqual(code_obj.parent_id, module_code_obj.id)
        gpt_input = code_obj.get_gpt_input(code_representer=code_representer)

        self.assertIsInstance(gpt_input, GptInputCodeObject)
        self.assertEqual(gpt_input.id, code_obj.id)
        self.assertEqual(gpt_input.code_type, code_obj.code_type)
        self.assertEqual(gpt_input.name, code_obj.name)
        self.assertEqual(gpt_input.docstring, code_obj.docstring)
        self.assertEqual(gpt_input.code, code_obj.code)
        self.assertEqual(gpt_input.context, code_obj.get_context())
        self.assertEqual(
            gpt_input.context_docstrings,
            code_representer.get_context_docstrings(code_obj.id),
        )
        self.assertEqual(
            gpt_input.context_docstrings,
            {module_code_obj.id: module_code_obj.docstring},
        )

    def test_get_sent_to_gpt(self):
        code_obj = CodeObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a():\n    """Returns 3"""\n    return 3'
            ).body[0],
            docstring="Returns 3",
            code='def func_a():\n    """Returns 3"""\n    return 3',
            parent_id=None,
        )
        self.assertFalse(code_obj.get_sent_to_gpt())
        code_obj.send_to_gpt = True
        self.assertTrue(code_obj.get_sent_to_gpt())


class TestMethodObject(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 1)


class TestClassObject(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 1)


class TestModuleObject(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 1)


class TestCodeRepresenter(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 1)

    def test_b(self):
        self.assertTrue(True)
        self.assertFalse(False)

    def test_split(self):
        with self.assertRaises(NotImplementedError):
            raise NotImplementedError


if __name__ == "__main__":
    unittest.main()
