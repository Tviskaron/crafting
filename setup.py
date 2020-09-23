 
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
    name='craft',
    version=find_version("craft", "__init__.py"),
    description='TODO',
    long_description=long_description,
    long_description_content_type='TODO',
    url='https://github.com/Tviskaron/craft',
    packages=find_packages(),
    py_modules=['craft', 'utils'],
    include_package_data=True,
    package_data={'': ['minecraft_names.json', 'basic_config.yaml']},
    install_requires=[
        "PyYAML",
        "docker"
    ],
    classifiers=[
        'Intended Audience :: Teachers, Students',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={"console_scripts": ["craft=craft.craft:main"]},
)
