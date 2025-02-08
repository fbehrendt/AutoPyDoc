"""A module docstring"""

class Class_a():
    """A simple test class a"""
    def __init__(self):
        """Instantiates a Class_a object"""
        pass

    def func_d(self):
        pass

class Class_b():
    """A simple test class b"""
    def __init__(self):
        """Instantiates a Class_b object"""
        self.var_class_a = Class_a()

def func_a():
    """creates a Class_a object and calls func_b"""
    some_class = Class_a()
    func_b()
    

def func_b():
    """calls print()"""
    print()

def func_c(x: int = 9, y: str = "nine", z: list = [1, 2, 3, 4, 5, 6, 7, 8, 9]) -> dict:
    """calls print()"""
    print()
    return {"x": x, "y": y, "z": z}

class_a = Class_a()
var_Ad = class_a.func_d()
var_B = Class_b()
var_B.var_class_a.func_d()
func_a()