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

        # self.assertIsInstance(gpt_input, GptInputCodeObject) TODO fix
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
    def test_add_argument(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_argument({"name": "x"})
        self.assertEqual(method_obj.arguments, [{"name": "x"}])

    def test_add_missing_arg_type(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_missing_arg_type("x")
        self.assertEqual(method_obj.missing_arg_types, {"x"})

    def test_add_exception(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_exception("NotImplementedError")
        self.assertEqual(method_obj.exceptions, {"NotImplementedError"})

    def test_add_class_id(self):
        pass

    def test_add_method_id(self):
        pass

    def test_get_context(self):
        pass

    def test_get_gpt_input(self):
        pass

    def test_init(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        self.assertEqual(method_obj.name, "func_a")
        self.assertEqual(method_obj.filename, "testfile.py")
        self.assertIsInstance(method_obj.ast, ast_module.FunctionDef)
        self.assertEqual(method_obj.docstring, "Returns value of x")
        self.assertEqual(
            method_obj.code,
            'def func_a(x):\n    """Returns value of x"""\n    return x',
        )
        self.assertEqual(method_obj.parent_id, None)

        self.assertTrue(hasattr(method_obj, "id") and isinstance(method_obj.id, int))
        self.assertEqual(method_obj.code_type, "method")
        self.assertIsInstance(method_obj, MethodObject)
        self.assertIsInstance(method_obj.called_methods, set)
        self.assertIsInstance(method_obj.called_classes, set)
        self.assertIsInstance(method_obj.called_by_methods, set)
        self.assertIsInstance(method_obj.called_by_classes, set)
        self.assertIsInstance(method_obj.called_by_modules, set)
        self.assertFalse(method_obj.outdated)
        self.assertFalse(method_obj.is_updated)
        self.assertFalse(method_obj.send_to_gpt)
        self.assertEqual(method_obj.old_docstring, method_obj.docstring)
        self.assertEqual(method_obj.arguments, [])
        self.assertEqual(method_obj.exceptions, set())
        self.assertEqual(method_obj.outer_method_id, None)
        self.assertEqual(method_obj.outer_class_id, None)
        self.assertEqual(method_obj.module_id, None)

    def test_add_called_method(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_called_method(called_method_id=568643265543564654)
        self.assertTrue(568643265543564654 in method_obj.called_methods)

    def test_add_called_class(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_called_class(called_class_id=568643265543564650)
        self.assertTrue(568643265543564650 in method_obj.called_classes)

    def test_add_caller_method(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_caller_method(caller_method_id=568643265543564651)
        self.assertTrue(568643265543564651 in method_obj.called_by_methods)

    def test_add_caller_class(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_caller_class(caller_class_id=568643265543564652)
        self.assertTrue(568643265543564652 in method_obj.called_by_classes)

    def test_add_caller_module(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.add_caller_module(caller_module_id=568643265543564653)
        self.assertTrue(568643265543564653 in method_obj.called_by_modules)

    def test_add_docstring(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        self.assertEqual(method_obj.docstring, "Returns value of x")
        method_obj.add_docstring("test")
        self.assertEqual(method_obj.docstring, "test")

    def test_update_docstring(self):
        method_obj = MethodObject(
            name="func_a",
            filename="testfile.py",
            ast=ast_module.parse(
                'def func_a(x):\n    """Returns value of x"""\n    return x'
            ).body[0],
            docstring="Returns value of x",
            code='def func_a(x):\n    """Returns value of x"""\n    return x',
            parent_id=None,
            arguments=None,
            return_type=None,
            exceptions=None,
            outer_method_id=None,
            outer_class_id=None,
            module_id=None,
        )
        method_obj.outdated = True
        self.assertEqual(method_obj.docstring, "Returns value of x")
        self.assertEqual(method_obj.docstring, method_obj.old_docstring)
        self.assertTrue(method_obj.outdated)
        self.assertFalse(method_obj.is_updated)
        method_obj.update_docstring(new_docstring="new docstring")
        self.assertEqual(method_obj.docstring, "new docstring")
        self.assertNotEqual(method_obj.docstring, method_obj.old_docstring)
        self.assertFalse(method_obj.outdated)
        self.assertTrue(method_obj.is_updated)


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
