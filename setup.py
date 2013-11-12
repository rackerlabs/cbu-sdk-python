import os
import re
from setuptools import setup, find_packages

pip_requires = os.path.join(os.getcwd(), 'requirements.txt')
test_requires = os.path.join(os.getcwd(), 'test-requirements.txt')

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
    license='Apache License (2.0)',
    keywords='rackspace, Cloud Backup, client',
    author_email='alejandro.cabrera@rackspace.com',
    description='A Python client for the Rackspace Cloud Backup API.',
    long_description=open('README.rst').read(),
    url='https://github.com/rackerlabs/python-cloudbackup-sdk',
    packages=find_packages(),
    zip_safe=False,
    install_requires=file_lines(pip_requires),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    data_files=data_files
)
