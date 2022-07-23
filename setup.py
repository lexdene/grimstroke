from setuptools import setup, find_packages

setup(
    name='grimstroke',
    version='0.0.5',
    packages=find_packages(exclude=['tests*']),
    entry_points="""
    [console_scripts]
    grimstroke = grimstroke.main:console_entry""",
    python_requires='>3.10.0',
)
