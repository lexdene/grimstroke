import os

from argparse import ArgumentParser

from .parser import (
    iter_nodes_from_module,
    is_func_call, is_func_def, get_calling_function_name,
)
from .models import Module, Env


def iter_modules(env):
    directory = env.directory
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                fullpath = os.path.join(root, filename)
                yield Module(os.path.relpath(fullpath, directory))


def main(directory):
    env = Env(directory)

    modules = list(iter_modules(env))
    for m in modules:
        print(m)
        for scope, node in iter_nodes_from_module(env, m):
            if is_func_call(node):
                print('calling from %s to %s' % (
                    scope.caller_name, get_calling_function_name(node)
                ))
            elif is_func_def(node):
                print('define function %s' % (node.name))


def console_entry():
    args = parse_args()
    return main(**vars(args))


def parse_args():
    parser = ArgumentParser(description='Grimstroke')
    parser.add_argument('directory')
    return parser.parse_args()
