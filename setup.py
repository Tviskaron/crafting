import codecs
import os
import re

from setuptools import setup, find_packages

cur_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(cur_dir, 'README.md'), 'rb') as f:
    lines = [x.decode('utf-8') for x in f.readlines()]
    lines = ''.join([re.sub('^<.*>\n$', '', x) for x in lines])
    long_description = lines


def read(*parts):
    with codecs.open(os.path.join(cur_dir, *parts), 'r') as fp:
        return fp.read()


# Reference: https://github.com/pypa/pip/blob/master/setup.py
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file,
        re.M,
    )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


setup(
    name='crafting',
    author='Alexey Skrynnik',
    license='MIT',
    version=find_version("crafting", "__init__.py"),
    description='Tool to run your DL/RL experiments with Docker',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Tviskaron/crafting',
    install_requires=[
        "PyYAML",
        "docker"
    ],
    package_data={'crafting': ['minecraft_names.json', 'basic_config.yaml']},
    include_package_data=True,
    package_dir={'': './'},
    packages=find_packages(where='./', include='crafting*'),
        entry_points={"console_scripts": ["crafting=crafting.crafting:main"]},
    python_requires='>=3.6',
)
