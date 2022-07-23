import ast
import logging
from enum import Enum

from .models import Scope, ScopeType, ExternalModule

Action = Enum(
    'Action',
    ['add_node', 'add_edge', 'export_node'],
)

logger = logging.getLogger(__name__)


def iter_nodes(scope, tree):
    yield scope, tree

    if isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
        sub_scope = scope.create_function_scope(tree.name)
    else:
        sub_scope = scope

    for node in ast.iter_child_nodes(tree):
        yield from iter_nodes(sub_scope, node)


def dump_node(node):
    if isinstance(node, ast.Module):
        return node

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Assign):
        return '%s(%s)' % (
            node.__class__.__name__,
            ', '.join([dump_node(n) for n in node.targets])
        )

    if isinstance(node, ast.Import):
        return '%s(%s)' % (
            node.__class__.__name__,
            ', '.join([a.name for a in node.names])
        )

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return '%s(%s)' % (
            node.__class__.__name__,
            node.name
        )

    return ast.dump(node)


def is_func_call(node):
    return isinstance(node, ast.Call)


def is_func_def(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))


def is_import(node):
    return isinstance(node, ast.Import)


def get_import_names(node):
    return [
        a.name for a in node.names
    ]


def is_import_from(node):
    return isinstance(node, ast.ImportFrom)


def get_import_from_names(node):
    return [
        (
            node.module,
            [
                a.name for a in node.names
            ]
        )
    ]


def get_symbol(scope, node):
    func = node.func

    if isinstance(func, ast.Name):
        name = func.id
        return scope.find_symbol(name)
    elif isinstance(func, ast.Attribute):
        name = func.value.id
        sub_scope = scope.find_symbol(name)
        sub_name = func.attr
        return sub_scope.find_symbol(sub_name)


def is_export(scope, node):
    if scope.type != ScopeType.module_body:
        return False

    if not isinstance(node, ast.Assign):
        return False

    if len(node.targets) != 1:
        return False

    target = node.targets[0]
    target_name = target.id
    if target_name != '__all__':
        return False

    return True


def get_export_names(node):
    names = ast.literal_eval(node.value)
    return names


def parse_node(scope, node):
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


def parse_code(top_scope, content):
    callings = []
    export_names = []

    tree = ast.parse(content)

    for scope, node in iter_nodes(top_scope, tree):
        try:
            for action, ele in parse_node(scope, node):
                if action == Action.add_node:
                    yield Action.add_node, ele
                elif action == Action.add_edge:
                    callings.append(ele)
                elif action == Action.export_node:
                    export_names.append(ele)
                else:
                    raise ValueError('no such action: %s' % action)
        except AttributeError:
            logger.debug(
                'collect node fail, %s at %d',
                dump_node(node), node.lineno
            )

    for scope, node in callings:
        try:
            callee_smb = get_symbol(scope, node)
            callee_qual_name = callee_smb.qual_name
            yield Action.add_edge, (scope.caller_name, callee_qual_name)
        except AttributeError:
            logger.debug(
                'get symbol fail. %s.%s at %d',
                scope.qual_name, dump_node(node), node.lineno
            )

    for scope, name in export_names:
        smb = scope.find_symbol(name)
        if not smb:
            logger.debug(
                'cannot get symbol. %s.%s',
                scope.qual_name, name
            )
            continue
        yield Action.export_node, smb.qual_name


class ParserBase:
    ext = None

    def parse(self, module):
        raise NotImplementedError


class PyParser(ParserBase):
    ext = 'py'

    def parse(self, module):
        with open(module.path) as f:
            content = f.read()

        top_scope = Scope.create_from_module(module)
        yield from parse_code(top_scope, content)

        module_scope = Scope.create_from_module(module)
        yield Action.export_node, module_scope.caller_name
