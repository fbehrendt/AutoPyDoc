import pathlib
import sys
import os
import logging
import pytest

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir)

from src.get_context import CodeParser
from src.code_representation import (
    CodeRepresenter,
    ModuleObject,
    MethodObject,
    ClassObject,
    CodeObject,
)


@pytest.fixture
def code_parser():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)8s: [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    working_dir = os.path.join(project_dir, "src/test/test_data")
    logger = logging.getLogger(__name__)

    code_parser = CodeParser(
        code_representer=CodeRepresenter(),
        working_dir=working_dir,
        debug=True,
        files=[
            os.path.join(working_dir, "src/main.py"),
            os.path.join(working_dir, "src/second_file.py"),
            os.path.join(working_dir, "src/third_file.py"),
            os.path.join(working_dir, "src/fourth_file.py"),
        ],
        logger=logger,
    )
    return code_parser


def test_init():
    pass
    # TODO


def test_add_file():
    pass
    # TODO


def test_extract_file_modules_classes_and_methods():
    pass
    # TODO


def test_extract_sub_classes_and_methods():
    pass
    # TODO


def test_extract_class_and_method_calls():
    pass
    # TODO


def test_resolve_variable():
    pass
    # TODO


def test_extract_exceptions():
    pass
    # TODO


def test_extract_args_and_return_type():
    pass
    # TODO


def test_check_return_type():
    pass
    # TODO


def test_extract_attributes():
    pass
    # TODO


def test_set_code_affected_by_changes_to_outdated():
    pass
    # TODO


def test_extract_dev_comments():
    pass
    # TODO


def test_extracted_code_objects(code_parser):
    assert hasattr(code_parser, "code_representer")
    assert hasattr(code_parser.code_representer, "objects")
    assert len(code_parser.code_representer.objects) > 0
    print("?")
    modules = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "module"
    ]
    classes = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "class"
    ]
    methods = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "method"
    ]
    assert len(modules) > 0
    assert len(classes) > 0
    assert len(methods) > 0

    # check main->ClassX
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "class"
                and "main.py" in code_obj.filename
                and code_obj.name == "ClassX"
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check main->ClassX->__init__
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "main.py" in code_obj.filename
                and code_obj.name == "__init__"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassX"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check main->ClassX->func_a
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "main.py" in code_obj.filename
                and code_obj.name == "func_a"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassX"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check main->func_c
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "main.py" in code_obj.filename
                and code_obj.name == "func_c"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )

    # check second_file->func_a
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "second_file.py" in code_obj.filename
                and code_obj.name == "func_a"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )

    # check third_file->ClassA
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "class"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "ClassA"
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check third_file->ClassA->__init__
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "__init__"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassA"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check third_file->ClassA->func_a
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "func_a"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassA"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check third_file->ClassB
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "class"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "ClassB"
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check third_file->ClassB->__init__
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "__init__"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassB"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check third_file->ClassB->func_a
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "func_a"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassB"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )
    # check third_file->func_a
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "func_a"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check third_file->func_b
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "third_file.py" in code_obj.filename
                and code_obj.name == "func_b"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )

    # check fourth_file->func_b
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "fourth_file.py" in code_obj.filename
                and code_obj.name == "func_b"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check fourth_file->ClassA
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "class"
                and "fourth_file.py" in code_obj.filename
                and code_obj.name == "ClassA"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).code_type == "module"
            ]
        )
        > 0
    )
    # check fourth_file->ClassA->__init__
    assert (
        len(
            [
                code_obj
                for code_obj in code_parser.code_representer.objects.values()
                if code_obj.code_type == "method"
                and "fourth_file.py" in code_obj.filename
                and code_obj.name == "__init__"
                and code_obj.parent_id is not None
                and code_parser.code_representer.get(code_obj.parent_id).name == "ClassA"
                and code_parser.code_representer.get(
                    code_parser.code_representer.get(code_obj.parent_id).parent_id
                ).code_type
                == "module"
            ]
        )
        > 0
    )


def test_sub_classes_and_methods(code_parser):
    modules = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "module"
    ]
    classes = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "class"
    ]
    methods = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "method"
    ]
    # test main module
    main_module = [module_obj for module_obj in modules if "main.py" in module_obj.filename][0]
    assert len(main_module.class_ids) == 1
    assert code_parser.code_representer.get(list(main_module.class_ids)[0]).name == "ClassX"
    assert len(main_module.method_ids) == 1
    assert code_parser.code_representer.get(list(main_module.method_ids)[0]).name == "func_c"
    # test main->ClassX
    class_x_class = code_parser.code_representer.get(list(main_module.class_ids)[0])
    assert len(class_x_class.class_ids) == 0
    assert len(class_x_class.method_ids) == 2
    class_x_methods = [
        code_parser.code_representer.get(method_id).name for method_id in class_x_class.method_ids
    ]
    assert "__init__" in class_x_methods
    assert "func_a" in class_x_methods
    # test second_file module
    second_file_module = [
        module_obj for module_obj in modules if "second_file.py" in module_obj.filename
    ][0]
    assert len(second_file_module.class_ids) == 0
    assert len(second_file_module.method_ids) == 1
    assert code_parser.code_representer.get(list(second_file_module.method_ids)[0]).name == "func_a"
    # test third_file module
    third_file_module = [
        module_obj for module_obj in modules if "third_file.py" in module_obj.filename
    ][0]
    assert len(third_file_module.class_ids) == 2
    module_third_file_classes = [
        code_parser.code_representer.get(class_id).name for class_id in third_file_module.class_ids
    ]
    assert "ClassA" in module_third_file_classes
    assert "ClassB" in module_third_file_classes
    assert len(third_file_module.method_ids) == 2
    module_third_file_methods = [
        code_parser.code_representer.get(method_id).name
        for method_id in third_file_module.method_ids
    ]
    assert "func_a" in module_third_file_methods
    assert "func_b" in module_third_file_methods
    # test third_file->ClassA
    third_file_class_A = [
        class_obj
        for class_obj in classes
        if "third_file.py" in class_obj.filename and class_obj.name == "ClassA"
    ][0]
    third_file_class_a_methods = [
        code_parser.code_representer.get(method_id).name
        for method_id in third_file_class_A.method_ids
    ]
    assert "__init__" in third_file_class_a_methods
    assert "func_a" in third_file_class_a_methods
    # test third_file->ClassB
    third_file_class_B = [
        class_obj
        for class_obj in classes
        if "third_file.py" in class_obj.filename and class_obj.name == "ClassB"
    ][0]
    third_file_class_b_methods = [
        code_parser.code_representer.get(method_id).name
        for method_id in third_file_class_B.method_ids
    ]
    assert "__init__" in third_file_class_b_methods
    assert "func_a" in third_file_class_b_methods
    # test fourth_file module
    fourth_file_module = [
        module_obj for module_obj in modules if "fourth_file.py" in module_obj.filename
    ][0]
    assert len(fourth_file_module.class_ids) == 1
    fourth_file_class_a = code_parser.code_representer.get(list(fourth_file_module.class_ids)[0])
    assert fourth_file_class_a.name == "ClassA"
    assert code_parser.code_representer.get(list(fourth_file_module.method_ids)[0]).name == "func_b"
    # test fourth_file->ClassA
    assert len(fourth_file_class_a.class_ids) == 0
    assert len(fourth_file_class_a.method_ids) == 1
    assert (
        code_parser.code_representer.get(list(fourth_file_class_a.method_ids)[0]).name == "__init__"
    )


def test_called_by_module_main(code_parser):
    code_parser.extract_class_and_method_calls()
    # test main module
    main_module = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "module" and "main.py" in code_obj.filename
    ][0]
    assert len(main_module.called_methods) > 0
    assert len(main_module.called_classes) > 0

    main_module_called_methods = [
        code_parser.code_representer.get(method_id) for method_id in main_module.called_methods
    ]
    main_module_called_classes = [
        code_parser.code_representer.get(class_id) for class_id in main_module.called_classes
    ]
    # test call to main->ClassX
    assert (
        len(
            [
                class_obj
                for class_obj in main_module_called_classes
                if class_obj.name == "ClassX"
                and "main.py" in class_obj.filename
                and class_obj.code_type == "class"
            ]
        )
        == 1
    )
    # test call to main->ClassX->func_a
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_a"
                and "main.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).name == "ClassX"
            ]
        )
        == 1
    )
    # test call to main->func_c
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_c"
                and "main.py" in method_obj.filename
                and method_obj.code_type == "method"
            ]
        )
        == 1
    )

    # test call to second_file->func_a
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_a"
                and "second_file.py" in method_obj.filename
                and method_obj.code_type == "method"
            ]
        )
        == 1
    )

    # test call to third_file->ClassA
    assert (
        len(
            [
                class_obj
                for class_obj in main_module_called_classes
                if class_obj.name == "ClassA"
                and "third_file.py" in class_obj.filename
                and class_obj.code_type == "class"
            ]
        )
        == 1
    )
    # test call to third_file->ClassA->func_a
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_a"
                and "third_file.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).name == "ClassA"
            ]
        )
        == 1
    )
    # test call to third_file->ClassB
    assert (
        len(
            [
                class_obj
                for class_obj in main_module_called_classes
                if class_obj.name == "ClassB"
                and "third_file.py" in class_obj.filename
                and class_obj.code_type == "class"
            ]
        )
        == 1
    )
    # test call to third_file->ClassB->func_a
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_a"
                and "third_file.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).name == "ClassB"
            ]
        )
        == 1
    )
    # test call to third_file->func_a
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_a"
                and "third_file.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).code_type == "module"
            ]
        )
        == 1
    )
    # test call to third_file->func_b
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_b"
                and "third_file.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).code_type == "module"
            ]
        )
        == 1
    )

    # test call to fourth_file->ClassA with alias ClassAFourthFile
    assert (
        len(
            [
                class_obj
                for class_obj in main_module_called_classes
                if class_obj.name == "ClassA"
                and "fourth_file.py" in class_obj.filename
                and class_obj.code_type == "class"
                and class_obj.parent_id is not None
                and code_parser.code_representer.get(class_obj.parent_id).code_type == "module"
            ]
        )
        == 1
    )
    # test call to fourth_file->func_b with alias func_b_fourth_file
    assert (
        len(
            [
                method_obj
                for method_obj in main_module_called_methods
                if method_obj.name == "func_b"
                and "fourth_file.py" in method_obj.filename
                and method_obj.code_type == "method"
                and method_obj.parent_id is not None
                and code_parser.code_representer.get(method_obj.parent_id).code_type == "module"
            ]
        )
        == 1
    )
