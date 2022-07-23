from setuptools import setup, find_packages

setup(
    name='grimstroke',
    version='0.0.10',
    packages=find_packages(exclude=['tests*']),
    entry_points="""
    [console_scripts]
    grimstroke = grimstroke.main:console_entry

    [grimstroke.parsers]
    Python = grimstroke.parser:PyParser""",
    python_requires='>3.10.0',
)
