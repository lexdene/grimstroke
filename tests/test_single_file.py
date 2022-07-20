import os
from unittest import TestCase

from grimstroke.main import collect


class TestSingleFile(TestCase):
    def _get_useless_functions(self, name):
        path = os.path.join(
            'examples/single_file',
            name + '.py'
        )
        col = collect(path)
        return list(col.get_useless_nodes())

    def test_call_by_module(self):
        r = self._get_useless_functions('call_by_module')

        self.assertEqual(r, ['call_by_module:bar'])

    def test_async_functions(self):
        self.assertEqual(
            self._get_useless_functions('async_functions'),
            []
        )

    def test_bin_op(self):
        self.assertEqual(
            self._get_useless_functions('bin_op'),
            []
        )

    def test_export_by_all(self):
        self.assertEqual(
            self._get_useless_functions('export_by_all'),
            ['export_by_all:baz']
        )

    def test_nested_func(self):
        self.assertEqual(
            self._get_useless_functions('nested_func'),
            ['nested_func:foo']
        )
