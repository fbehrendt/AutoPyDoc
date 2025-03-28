import second_file
from third_file import ClassA, ClassB, func_a, func_b
from fourth_file import ClassA as ClassAFourthFile
from fourth_file import func_b as func_b_fourth_file


class ClassX:
    def __init__(self):
        pass

    def func_a(self):
        pass


def func_c():
    pass


this_file_class_x = ClassX()
this_file_class_x_func_a = this_file_class_x.func_a()
this_file_func_c = func_c()

second_file_func_a = second_file.func_a()

third_file_class_a = ClassA()
third_file_class_a_func_a = third_file_class_a.func_a()
third_file_class_b = ClassB()
third_file_class_b_func_a = third_file_class_b.func_a()
third_file_func_a = func_a()
third_file_func_b = func_b()

fourth_file_class_a = ClassAFourthFile()
fourth_file_func_b = func_b_fourth_file()


if __name__ == "__main__":
    pass  # TODO calls in here

    # TODO import here
    # TODO call here

    import logging
    import pathlib
    import sys
    import os

    file_path = os.path.dirname(os.path.realpath(__file__))
    project_dir = str(pathlib.Path(file_path).parent.parent.parent.absolute())
    sys.path.append(project_dir)

    from get_context import CodeParser
    from code_representation import (
        CodeRepresenter,
        ModuleObject,
        MethodObject,
        ClassObject,
        CodeObject,
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)8s: [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    working_dir = os.path.join(project_dir, "test/test_data")
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
