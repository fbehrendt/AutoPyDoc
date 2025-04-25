"""Holds classes A, B, C and a keep_b_updated method"""

from time import sleep


class A:
    """Do calculations based on instance variable x"""

    def __init__(self):
        """Initialize x"""
        self.x = 1

    def func_a(self, y: int) -> int:
        """
        Return self.x + y

        :param y: number to be added to self.x
        :type y: int

        :return: self.x + y
        :rtype: int
        """
        return self.x + y

    def func_b(self, a):
        """
        Add a to self.x by adding one to self.x a times

        :param a: number to be added to self.x
        :type a: int
        """
        for i in range(a):
            self.x += 1

    def func_c(self, n):
        """Divide self.x by n"""
        if n == 0:
            raise ZeroDivisionError
        return self.x / n


class B:
    def __init__(self):
        self.text = "Hello world!"

    def update(self):
        self.text = self.text[1:] + self.text[:1]
        self.display()

    def display(self):
        print(self.text)


class C:
    """The king class"""

    def new_king(self):
        return "I am your new king"


def keep_b_updated(b_instance):
    """
    call update method of b_instance indefinitely

    :param b_instance: instance of class B
    :type b_instance: B
    """
    while True:
        sleep(0.5)
        b_instance.update()
