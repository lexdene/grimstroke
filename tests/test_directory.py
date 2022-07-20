import os
from unittest import TestCase

from grimstroke.main import collect


class TestDirectory(TestCase):
    def _get_useless_functions(self, name):
        path = os.path.join('examples', name)
        col = collect(path)
        return list(col.get_useless_nodes())

    def test_simple_project(self):
        self.assertEqual(
            self._get_useless_functions('simple_project'),
            ['hello:hello', 'world:never_called_function']
        )
