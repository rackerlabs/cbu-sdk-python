***************************
Cloud Backup API Python SDK
***************************

:version: 0.19.3
:Presentations: `Introduction`_
.. image:: https://requires.io/github/cabrera/python-cloudbackup-sdk/requirements.png?branch=master
   :target: https://requires.io/github/cabrera/python-cloudbackup-sdk/requirements/?branch=master
   :alt: Requirements Status
.. image:: https://travis-ci.org/cabrera/python-cloudbackup-sdk.png?branch=master
   :target: https://travis-ci.org/cabrera/python-cloudbackup-sdk
   :alt: TravisCI Status
 
Welcome to the Python bindings to the Rackspace Cloud Backup
API. These bindings will help you make the most of the Cloud Backup
system and integrate it into your workflows.

**Table of Contents**

.. contents::
    :local:
    :depth: 2
    :backlinks: none

========
Features
========

* Python 2.7 and 3.3+ supported
* Easy to install (pip)
* Easy to test (nose + tox)
* Designed to be easy to use with `ipython`_
    - Tab-completion and smart introspection
    - verbs map to object functions: backup.start()
    - nouns map to object properties: backup.report

I'll let the code speak for ease of use:

.. code-block:: python

    from rcbu.client.client import Client
    from rcbu.client.connection import Connection
    import rcbu.client.backup_configuration as backup_config

    conn = Connection('username', 'dfw',
                      apikey='981263y1hq82yh8y9q38q2')
    client = Client(conn)
    myconf = backup_config.from_file('backup_config.json', conn)

    # Upload a new backup configuration to the Backup API
    myconf.create()

    backup = client.create_backup(myconf)
    status = backup.start()

    # block here until the backup completes
    # polls once a minute by default
    backup.wait_for_completion(poll_interval=.5)

    # easy reporting and checking for success
    report = backup.report
    report.raise_if_not_ok()


Check out the `backup_config.json`_

=======
Install
=======

Make sure you have libgmp, libssl, and the Python development headers installed::

    sudo apt-get install libgmp-dev libssl-dev python-dev
    sudo apt-get install libgmp-dev libssl-dev python3-dev  # for Py3

On Windows, make sure that the proper Visual Studio path is configured::

    SET VS90COMNTOOLS=%VS100COMNTOOLS%  # MSVS 2010
    SET VS90COMNTOOLS=%VS110COMNTOOLS%  # MSVS 2012

.. code-block:: bash

    pip install git+https://github.com/rackerlabs/python-cloudbackup-sdk

============
Contributing
============

Some simple guidelines:

* Unit tests for new features
* Keep the code clean - flake8
* Be wary of warnings and errors - pylint
* >95% code coverage - keep it strong
* Be `Pythonic`_

For more details, checkout the `Contributing`_ guide.

If you have any questions, please check in with Alejandro Cabrera
<alejandro.cabrera@rackspace.com>.

.. _Pythonic: http://www.python.org/dev/peps/pep-0020/
.. _backup_config.json: https://github.com/rackerlabs/python-cloudbackup-sdk/blob/master/examples/create_a_backup/backup_config.json
.. _ipython: http://ipython.org/
.. _Introduction: https://one.rackspace.com/download/attachments/21615636/python-sdk.pdf
.. _Contributing: https://github.com/rackerlabs/python-cloudbackup-sdk/blob/master/CONTRIBUTING.rst
