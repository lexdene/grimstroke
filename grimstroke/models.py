from collections import namedtuple, deque
from enum import Enum
from functools import cached_property

from .utils import remove_suffix

CallingRelation = namedtuple(
    'CallingRelation',
    ['from_func', 'to_func']
)
ScopeType = Enum(
    'ScopeType',
    ['module_body', 'class_body', 'function_body']
)


class Module:
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.path)


class ExternalModule:
    def __init__(self, name):
        self.name = name

        self._ref_symbols = {}

    @cached_property
    def full_name(self):
        return self.name

    def find_symbol(self, name: str):
        smb = Symbol(name=name, scope=self)
        self._ref_symbols[name] = smb
        return smb


class Env:
    def __init__(self, directory):
        self.directory = directory


class Collector:
    def __init__(self):
        self.nodes = []
        self.edges = {}
        self.exported_nodes = []

    def add_node(self, name: str):
        self.nodes.append(name)

    def add_edge(self, from_name: str, to_name: str):
        if from_name not in self.edges:
            self.edges[from_name] = set()

        self.edges[from_name].add(to_name)

    def export_node(self, name: str):
        self.exported_nodes.append(name)

    def get_useless_nodes(self):
        queue = deque()
        visited = set()

        for name in self.exported_nodes:
            visited.add(name)
            queue.append(name)

        while queue:
            from_name = queue.popleft()

            for to_name in self.edges.get(from_name, []):
                if to_name not in visited:
                    visited.add(to_name)
                    queue.append(to_name)

        for name in self.nodes:
            if name not in visited:
                yield name


class Scope:
    def __init__(self, name: str, type: ScopeType, outer_scope=None):
        self.name = name
        self.type = type
        self.outer_scope = outer_scope

        self._symbols = {}

    def add_symbol(self, name: str, symbol):
        self._symbols[name] = symbol

    def declare_function(self, name: str):
        smb = Symbol(name=name, scope=self)
        self.add_symbol(name, smb)
        return smb

    def find_symbol(self, name: str):
        if name in self._symbols:
            return self._symbols[name]

        if self.outer_scope:
            return self.outer_scope.find_symbol(name)

    @cached_property
    def full_name(self):
        if self.outer_scope:
            return self.outer_scope.full_name + ':' + self.name

        return self.name

    @cached_property
    def caller_name(self):
        if self.type == ScopeType.module_body:
            return self.full_name + ':(global)'
        else:
            return self.full_name

    def __str__(self):
        return '<Scope %s>' % self.full_name

    def create_function_scope(self, name):
        return Scope(
            name=name,
            type=ScopeType.function_body,
            outer_scope=self
        )

    @classmethod
    def create_from_module(cls, module: Module):
        name = remove_suffix(module.path, '.py').replace('/', '.')

        return cls(
            name=name,
            type=ScopeType.module_body,
        )


class Symbol:
    def __init__(self, name: str, scope: Scope):
        self.name = name
        self.scope = scope

    @cached_property
    def full_name(self):
        return '%s:%s' % (self.scope.full_name, self.name)
