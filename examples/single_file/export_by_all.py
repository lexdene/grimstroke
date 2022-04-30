__all__ = ['foo']


def foo():
    return bar()


def bar():
    return 'hello'


def baz():
    return 'this should be useless'
