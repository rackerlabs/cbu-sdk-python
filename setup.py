import os
from setuptools import setup, find_packages

pip_requires = os.path.join(os.getcwd(), 'tools', 'pip-requires')
test_requires = os.path.join(os.getcwd(), 'tools', 'test-requires')

def file_lines(path):
    reqs = None
    with open(path, 'rt') as f:
        reqs = f.read().split()
    return reqs

setup(
    name='rackspace-backup-client',
    version='0.1.0',
    author='Alejandro Cabrera',
    author_email='alejandro.cabrera@rackspace.com',
    description='A Python client for the Rackspace Cloud Backup API.',
    long_description=open('README.rst').read(),
    url='https://github.com/cabrera/rackspace-backup-client',
    packages=find_packages(),
    zip_safe=False,
    install_requires=file_lines(pip_requires),
    include_package_data=True,
    classifiers=file_lines('docs/CLASSIFIERS')
)
