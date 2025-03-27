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


if __name__ == "__main__":
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
