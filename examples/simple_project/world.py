from .hello import hello, world


def never_called_function():
    hello()


def useful_function():
    world()


if __name__ == '__main__':
    useful_function()
