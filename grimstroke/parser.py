import os

import ast

from .models import Scope


def iter_nodes_from_module(env, module):
    top_scope = Scope.create_from_module(module)
    tree = parse_module(env, module)
    return iter_nodes(top_scope, tree)


def parse_module(env, module):
    path = os.path.join(env.directory, module.path)
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

    if isinstance(node, ast.Assign):
        return '%s(%s)' % (
            node.__class__.__name__,
            ', '.join([n.id for n in node.targets])
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


def get_calling_function_name(node):
    func = node.func

    if isinstance(func, ast.Name):
        return func.id
    elif isinstance(func, ast.Attribute):
        return '%s.%s' % (func.value.id, func.attr)
    else:
        raise ValueError(
            'cannot parse calling function node: %s' % ast.dump(node)
        )
