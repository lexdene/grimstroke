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
