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
        i = 0
        while i < a:
            self.x += 1
            i += 1

    def func_c(self, n):
        """Multiply self.x with n"""
        return self.x * n


class B:
    def __init__(self):
        """Initializes a ball"""
        self.x = 5
        self.y = 5
        self.speed_x = 2
        self.speed_y = -1
        self.diameter = 2

    def update(self):
        """Move the ball"""
        self.x += self.speed_x
        self.y += self.speed_y
        if not 0 + (self.diameter / 2) < self.x < 20 - (self.diameter / 2):
            self.speed_x = -self.speed_x
        if not 0 + (self.diameter / 2) < self.y < 20 - (self.diameter / 2):
            self.speed_y = -self.speed_y
        self.display()

    def display(self):
        for row in range(20):
            for column in range(20):
                if row in range(
                    self.x - (self.diameter // 2), self.x + (self.diameter // 2)
                ) and column in range(self.y - (self.diameter // 2), self.y + (self.diameter // 2)):
                    print("x", end="")
                else:
                    print("_", end="")
            print()
        print("\n")


class C:
    """The king class"""

    def old_king(self):
        """print goodbye message"""
        return "The king is dead, long live the king"


def keep_b_updated(b_instance):
    """
    call update method of b_instance indefinitely

    :param b_instance: instance of class B
    :type b_instance: B
    """
    while True:
        sleep(0.5)
        b_instance.update()
