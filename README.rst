***************************
Cloud Backup API Python SDK
***************************

:version: 0.20.0
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
* Designed to be easy to use on multiple platforms

.. code-block:: python

	#TODO: Update this for the new API
	#	Create a backup
	#	Run a backup
	#	Get the backup report

=======
Install
=======

Make sure you have libgmp, libssl, and the Python development headers installed::

    sudo apt-get install python-dev python3-dev

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
* Keep the code clean - pep8
* Be wary of warnings and errors - pylint
* 100% code coverage - keep it strong

For more details, checkout the `Contributing`_ guide.

If you have any questions, please check in with Alejandro Cabrera
<alejandro.cabrera@rackspace.com>.

.. _backup_config.json: https://github.com/rackerlabs/python-cloudbackup-sdk/blob/master/examples/create_a_backup/backup_config.json
.. _Contributing: https://github.com/rackerlabs/python-cloudbackup-sdk/blob/master/CONTRIBUTING.rst
