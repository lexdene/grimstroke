def foo():
    return 1


def bar():
    return 2


def add(a, b):
    return a + b


def call_in_func_args():
    return add(foo(), bar())


def call_with_plus():
    return foo() + bar()
