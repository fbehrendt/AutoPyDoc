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


def test_called_by_module_main(code_parser):
    main_module = [
        code_obj
        for code_obj in code_parser.code_representer.objects.values()
        if code_obj.code_type == "module" and "main.py" in code_obj.filename
    ][0]
    assert len(main_module.called_methods) > 0
    assert len(main_module.called_classes) > 0
