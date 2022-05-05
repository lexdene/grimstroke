import os

from argparse import ArgumentParser

from .parser import (
    iter_nodes_from_module,
    is_func_call, is_func_def,
    is_import, get_symbol, get_import_names,
    is_export, get_export_names,
)
from .models import Module, Env, ExternalModule


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
        callings = []
        for scope, node in iter_nodes_from_module(env, m):
            if is_func_call(node):
                callings.append((scope, node))
            elif is_func_def(node):
                func_name = node.name
                print('define function %s' % func_name)
                scope.declare_function(func_name)
            elif is_import(node):
                for module_name in get_import_names(node):
                    ext_module = ExternalModule(module_name)
                    scope.add_symbol(module_name, ext_module)
            elif is_export(scope, node):
                for name in get_export_names(node):
                    print('export %s' % name)

        for scope, node in callings:
            callee_smb = get_symbol(scope, node)
            callee_full_name = callee_smb.full_name

            print('calling from %s to %s' % (
                scope.caller_name, callee_full_name
            ))

        print()


def console_entry():
    args = parse_args()
    return main(**vars(args))


def parse_args():
    parser = ArgumentParser(description='Grimstroke')
    parser.add_argument('directory')
    return parser.parse_args()
