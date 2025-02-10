"""A module docstring"""

class Class_a():
    """A simple test class a"""
    class_var = 0

    def __init__(self):
        """Instantiates a Class_a object"""
        self.var = "xyz"
        pass

    def func_d(self):
        return func_a()

class Class_b():
    """A simple test class b"""
    def __init__(self):
        """Instantiates a Class_b object"""
        self.var_class_a = Class_a()

class Class_c():
    """A simple test class c"""
    def __init__(self):
        """Instantiates a Class_c object"""
        self.var_end = "End of chain"

def func_a():
    """creates a Class_a object and calls func_b"""
    some_class = Class_c()
    func_b()
    return some_class
    

def func_b():
    """calls print()"""
    print()

def func_c(x: int = 9, y: str = "nine", z: list = [1, 2, 3, 4, 5, 6, 7, 8, 9]) -> dict:
    """calls print()"""
    print()
    return {"x": x, "y": y, "z": z}

class_a = Class_a()
class_a.class_var = 7
var_Ad = class_a.func_d()
var_B = Class_b()
var_B.var_class_a.func_d().var_end
func_a()