from collections import namedtuple
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


class Env:
    def __init__(self, directory):
        self.directory = directory


class Collector:
    def __init__(self):
        self._declared_functions = []
        self._calling_relations = []

    def declare_function(self, full_name: str):
        self._declared_functions.append(full_name)

    def add_calling_relation(self, from_func: str, to_func: str):
        self._calling_relations.append(CallingRelation(
            from_func=from_func,
            to_func=to_func
        ))


class Scope:
    def __init__(self, name: str, type: ScopeType, outer_scope=None):
        self.name = name
        self.type = type
        self.outer_scope = outer_scope

        self._declared_functions = []

    def declare_function(self, name: str):
        self._declared_functions.append(name)

    def find_declare_scope(self, name: str):
        if name in self._declared_functions:
            return self

        if self.outer_scope:
            return self.outer_scope.find_declare_scope(name)

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
