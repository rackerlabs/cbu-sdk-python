import os
import re
from setuptools import setup, find_packages

pip_requires = os.path.join(os.getcwd(), 'tools', 'pip-requires')
test_requires = os.path.join(os.getcwd(), 'tools', 'test-requires')

def credentials():
    install_path = os.path.join(os.path.expanduser('~'),
                                '.pysdk')
    if os.path.exists(os.path.join(install_path, 'credentials.json')):
        return ('.', ['setup.py'])  # null install
    conf_path = os.path.join('conf', 'credentials.json')
    return (install_path, [conf_path])


def file_lines(path):
    reqs = None
    with open(path, 'rt') as f:
        reqs = f.read().split()
    return reqs


def parse_version():
    data = None
    with open('README.rst', 'rt') as f:
        data = f.read()
    return '.'.join(re.search(r':version: (\d+)\.(\d+)\.(\d+)', data).groups())


data_files = []
data_files.append(credentials())
setup(
    name='rackspace-backup-client',
    version=parse_version(),
    author='Alejandro Cabrera',
    author_email='alejandro.cabrera@rackspace.com',
    description='A Python client for the Rackspace Cloud Backup API.',
    long_description=open('README.rst').read(),
    url='https://github.com/rackerlabs/python-cloudbackup-sdk',
    packages=find_packages(),
    zip_safe=False,
    install_requires=file_lines(pip_requires),
    include_package_data=True,
    classifiers=file_lines('docs/CLASSIFIERS'),
    data_files=data_files
)
