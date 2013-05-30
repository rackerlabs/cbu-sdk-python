***************************
Cloud Backup API Python SDK
***************************

.. image:: https://jenkins.drivesrvr-dev.com/job/python-cloudbackup-client/badge/icon
    :target: http://sonar.drivesrvr-dev.com:9000/dashboard/index/2941

:version: 0.7.1

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
* Easy to use

I'll let the code speak for ease of use:

.. code-block:: python

    from rcbu.client.client import Connection
    import rcbu.client.backup_configuration as backup_config

    conn = Connection('username', apikey='981263y1hq82yh8y9q38q2')
    myconf = backup_config.from_file('backup_config.json')
    myconf.connect(conn)

    # Upload a new backup configuration to the Backup API
    myconf.create()

    backup = conn.create_backup(myconf)
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

.. code-block:: bash

    pip install git+https://github.com/racker/python-cloudbackup-client

============
Contributing
============

Some simple guides:

* Unit tests for new features
* Keep the code clean - flake8
* Keep the code free of warnings and errors - pylint
* >95% code coverage - keep it strong
* Be `Pythonic`_

If you have any questions, please check in with Alejandro Cabrera
<alejandro.cabrera@rackspace.com>.

.. _Pythonic: http://www.python.org/dev/peps/pep-0020/
.. _backup_config.json: https://github.com/racker/python-cloudbackup-client/blob/master/examples/create_a_backup/backup_config.json
