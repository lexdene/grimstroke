def get_formatter_cls(key):
    FORMATTER_CLS_MAP = {
        'simple': SimpleFormatter,
        'tree': TreeFormatter,
    }

    return FORMATTER_CLS_MAP[key]


def get_formatter(key):
    fmt_cls = get_formatter_cls(key)
    return fmt_cls()


class FormatterBase:
    def output(self, col, name):
        raise NotImplementedError


class SimpleFormatter(FormatterBase):
    def output(self, col, name):
        print(name)


class TreeFormatter(FormatterBase):
    def __init__(self):
        self.visited = set()

    def output(self, col, name):
        self.visited = set()

        for line in self._iter_lines(col, name):
            print(line)

    def _iter_lines(self, col, name):
        if name in self.visited:
            yield '%s (visited)' % name
        else:
            yield name
            self.visited.add(name)

            for sub_name in col.get_callers(name):
                for line in self._iter_lines(col, sub_name):
                    yield '    %s' % line
