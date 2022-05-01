def foo():
    pass


def bar():
    pass


def scope_function():
    def foo():
        pass

    def baz():
        foo()
        bar()

    return baz()
