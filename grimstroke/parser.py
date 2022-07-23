import ast
from enum import Enum

from .models import Scope, ScopeType

Action = Enum(
    'Action',
    ['add_node', 'add_edge', 'export_node'],
)


def iter_nodes_from_module(env, module):
    top_scope = Scope.create_from_module(module)
    tree = parse_module(module.path)
    return iter_nodes(top_scope, tree)


def parse_module(path):
    with open(path) as f:
        content = f.read()

    return ast.parse(content)


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
