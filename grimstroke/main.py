import os
import logging

from argparse import ArgumentParser

from .parser import (
    iter_nodes_from_module,
    is_func_call, is_func_def,
    is_import, get_symbol, get_import_names,
    is_import_from, get_import_from_names,
    is_export, get_export_names,
    dump_node, Action,
)
from .models import (
    Module, Env, ExternalModule, Collector, Scope,
    match_qual_name,
)
from .formatter import get_formatter

logger = logging.getLogger(__name__)


def make_module(path: str, base_dir: str = ''):
    if base_dir:
        rel_path = os.path.relpath(path, base_dir)
        name = os.path.splitext(rel_path)[0].replace('/', '.')
        return Module(name=name, path=path)
    else:
        name = os.path.splitext(os.path.split(path)[1])[0]
        return Module(name=name, path=path)


def match_path(path, condition):
    if path == condition:
        return True

    if path.startswith(condition + '/'):
        return True

    return False


def match_paths(path, conditions):
    for cond in conditions:
        if match_path(path, cond):
            return True

    return False


def iter_modules(path, input_excludes=None):
    if os.path.isfile(path):
        yield make_module(path)
    else:
        for root, dirs, filenames in os.walk(path):
            rel_dir_name = os.path.relpath(root, path)
            if input_excludes and match_paths(rel_dir_name, input_excludes):
                continue

            for filename in filenames:
                if filename.endswith('.py'):
                    fullpath = os.path.join(root, filename)
                    yield make_module(fullpath, path)


def collect_node(scope, node):
    if is_func_call(node):
        yield Action.add_edge, (scope, node)
    elif is_func_def(node):
        func_name = node.name
        smb = scope.declare_function(func_name)
        yield Action.add_node, smb.qual_name
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
            yield Action.export_node, (scope, name)


def collect(path, input_excludes=None):
    env = Env(path)
    col = Collector()

    for m in iter_modules(path, input_excludes=input_excludes):
        callings = []
        export_names = []
        for scope, node in iter_nodes_from_module(env, m):
            try:
                for action, ele in collect_node(scope, node):
                    if action == Action.add_node:
                        col.add_node(ele)
                    elif action == Action.add_edge:
                        callings.append(ele)
                    elif action == Action.export_node:
                        export_names.append(ele)
                    else:
                        raise ValueError('no such action: %s' % action)
            except AttributeError:
                logger.debug(
                    'collect node fail, %s at %s:%d',
                    dump_node(node), m.path, node.lineno
                )

        for scope, node in callings:
            try:
                callee_smb = get_symbol(scope, node)
                callee_qual_name = callee_smb.qual_name
                col.add_edge(scope.caller_name, callee_qual_name)
            except AttributeError:
                logger.debug(
                    'get symbol fail. %s.%s at %s:%d',
                    scope.qual_name, dump_node(node), m.path, node.lineno
                )

        for scope, name in export_names:
            smb = scope.find_symbol(name)
            if not smb:
                logger.debug(
                    'cannot get symbol. %s.%s',
                    scope.qual_name, name
                )
                continue
            col.export_node(smb.qual_name)

        module_scope = Scope.create_from_module(m)
        col.export_node(module_scope.caller_name)

    return col


def main(
    path,
    entries=None, input_excludes=None,
    output_filter=None, output_format=None
):
    col = collect(path, input_excludes=input_excludes)

    if entries:
        for n in col.nodes:
            if _match_entries(n, entries):
                col.export_node(n)

    formatter = get_formatter(output_format)

    print('useless nodes:')
    for n in col.get_useless_nodes():
        if match_qual_name(n, output_filter):
            formatter.output(col, n)


def _match_entries(name, entries):
    for entry in entries:
        if match_qual_name(name, entry):
            return True

    return False


def console_entry():
    args = parse_args()
    return main(**vars(args))


def parse_args():
    parser = ArgumentParser(description='Grimstroke')
    parser.add_argument('path')
    parser.add_argument('--entry', action='append', dest='entries')
    parser.add_argument(
        '--input-exclude', action='append', dest='input_excludes'
    )
    parser.add_argument('--output-filter')
    parser.add_argument('--output-format', default='simple')
    return parser.parse_args()
