import os

from argparse import ArgumentParser

from .parser import (
    iter_nodes_from_module,
    is_func_call, is_func_def,
    is_import, get_symbol, get_import_names,
    is_import_from, get_import_from_names,
    is_export, get_export_names,
)
from .models import Module, Env, ExternalModule, Collector, Scope


def make_module(path: str, base_dir: str = ''):
    if base_dir:
        rel_path = os.path.relpath(path, base_dir)
        name = os.path.splitext(rel_path)[0].replace('/', '.')
        return Module(name=name, path=path)
    else:
        name = os.path.splitext(os.path.split(path)[1])[0]
        return Module(name=name, path=path)


def iter_modules(path):
    if os.path.isfile(path):
        yield make_module(path)
    else:
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith('.py'):
                    fullpath = os.path.join(root, filename)
                    yield make_module(fullpath, path)


def collect(path):
    env = Env(path)
    col = Collector()

    modules = list(iter_modules(path))
    for m in modules:
        print(m)
        callings = []
        export_names = []
        for scope, node in iter_nodes_from_module(env, m):
            if is_func_call(node):
                callings.append((scope, node))
            elif is_func_def(node):
                func_name = node.name
                smb = scope.declare_function(func_name)
                col.add_node(smb.full_name)
                print('define function %s' % smb.full_name)
            elif is_import(node):
                for module_name in get_import_names(node):
                    ext_module = ExternalModule(module_name)
                    scope.add_symbol(module_name, ext_module)
            elif is_import_from(node):
                for module_name, names in get_import_from_names(node):
                    ext_module = ExternalModule(module_name)
                    for name in names:
                        smb = ext_module.find_symbol(name)
                        scope.add_symbol(name, smb)
            elif is_export(scope, node):
                for name in get_export_names(node):
                    export_names.append((scope, name))

        for scope, node in callings:
            callee_smb = get_symbol(scope, node)
            callee_full_name = callee_smb.full_name

            print('calling from %s to %s' % (
                scope.caller_name, callee_full_name
            ))
            col.add_edge(scope.caller_name, callee_full_name)

        for scope, name in export_names:
            smb = scope.find_symbol(name)
            print('export %s' % smb.full_name)
            col.export_node(smb.full_name)

        module_scope = Scope.create_from_module(m)
        col.export_node(module_scope.caller_name)

        print()

    return col


def main(path):
    col = collect(path)
    print('useless nodes:')
    for n in col.get_useless_nodes():
        print(n)


def console_entry():
    args = parse_args()
    return main(**vars(args))


def parse_args():
    parser = ArgumentParser(description='Grimstroke')
    parser.add_argument('path')
    return parser.parse_args()
