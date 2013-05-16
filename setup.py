import os
import re
from setuptools import setup, find_packages

pip_requires = os.path.join(os.getcwd(), 'tools', 'pip-requires')
test_requires = os.path.join(os.getcwd(), 'tools', 'test-requires')

def file_lines(path):
    reqs = None
    with open(path, 'rt') as f:
        reqs = f.read().split()
    return reqs


def parse_version():
    data = None
    with open('README.rst', 'rt') as f:
        data = f.read()
    return '.'.join(re.search(r':version: (\d)\.(\d)\.(\d)', data).groups())


setup(
    name='rackspace-backup-client',
    version=parse_version(),
    author='Alejandro Cabrera',
    author_email='alejandro.cabrera@rackspace.com',
    description='A Python client for the Rackspace Cloud Backup API.',
    long_description=open('README.rst').read(),
    url='https://github.com/racker/python-cloudbackup-client',
    packages=find_packages(),
    zip_safe=False,
    install_requires=file_lines(pip_requires),
    include_package_data=True,
    classifiers=file_lines('docs/CLASSIFIERS')
)
