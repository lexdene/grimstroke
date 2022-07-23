import os
import logging

from argparse import ArgumentParser
from pkg_resources import iter_entry_points

from .parser import Action
from .models import Module, Collector, match_qual_name, Scope
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


def iter_modules(path, excludes=None, allow_exts=None):
    if os.path.isfile(path):
        yield make_module(path)
    else:
        for root, dirs, filenames in os.walk(path):
            rel_dir_name = os.path.relpath(root, path)
            if excludes and match_paths(rel_dir_name, excludes):
                continue

            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if allow_exts and ext not in allow_exts:
                    continue

                fullpath = os.path.join(root, filename)
                yield make_module(fullpath, path)


def get_parser_cls_map():
    r = {}

    for ep in iter_entry_points('grimstroke.parsers'):
        parser_cls = ep.load()
        ext = '.' + parser_cls.ext
        r[ext] = parser_cls

    return r


def get_parser(pcm, module):
    _, ext = os.path.splitext(module.path)
    return pcm[ext]()


def collect(path, input_excludes=None):
    col = Collector()

    parser_cls_map = get_parser_cls_map()
    input_allow_exts = list(parser_cls_map.keys())

    for m in iter_modules(
        path,
        excludes=input_excludes, allow_exts=input_allow_exts
    ):
        parser = get_parser(parser_cls_map, m)
        for action, item in parser.parse(m):
            if action == Action.add_node:
                col.add_node(item)
            elif action == Action.add_edge:
                col.add_edge(*item)
            elif action == Action.export_node:
                col.export_node(item)
            else:
                raise ValueError('no such action: %s' % action)

        module_scope = Scope.create_from_module(m)
        col.add_node(module_scope.caller_name)

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
