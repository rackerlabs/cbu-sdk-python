**********************
Contributors, Welcome!
**********************

Come on in and contribute! The RCBU Python SDK is looking to grow, and
it needs your help. This document is a guide to making **really**
successful contributions.

**Table of Contents**

.. contents::
    :local:
    :depth: 2
    :backlinks: none

=======================
A Little Bit of Process
=======================

----------------
We've Got Issues
----------------

Check out the `Issues`_ and `Milestones`_ tabs. They offer great
starting points for making an effective contribution. If you find an
issue or think of something that you'd like to see in the SDK, the
`Issues`_ page is the place to put it.

Feedback counts as a contribution, too, and it's the easiest one you
can make.

-------
Reviews
-------

Except for feedback, every contribution begins with a pull request. In
order to keep knowledge of the Python SDK distributed, we encourage
code review here.

-------
Testing
-------

All code-based contributions require 100% unit test coverage - no
questions asked.

To be clear about definitions, a unit test is one that:

* Tests expected functionality
* Does not utilize the network
* Does not utilize persistent storage
* Does not utilize unpredictable functionality (e.g., time.time)

In order to achieve 100% code coverage given these constraints, you'll
need to mock. Be sure to use the excellent `httpretty`_ and `mock`_
libraries to accomplish these goals.

To run tests::

	tox

====
Code
====

-----
Style
-----

To be sure your contributions are compliant::

    tox -e pep8

-----
Misc.
-----

Here are the tenants in order of importance:

* Correctness - incorrect code is useless
* Simplicity - easy to use, easy to understand
* Consistentency - new interfaces should feel like existing interfaces
* Performance - almost doesn't matter. "Optimization is the root of all evil".
    - Address performance when it becomes a problem. Don't make it a
      problem before it is.
* Few dependencies - must be simple, explicit and not require a lot of things to be installed
	- Reduces the potential for issues with other projects
	- Keeps the ability to integrate into other projects high

=======
Goodies
=======

Make a successful contribution, and your name will be immortalized in
the `AUTHORS`_ file! Thanks for your help. You make this project
possible.

.. _mock: http://www.voidspace.org.uk/python/mock/
.. _Issues: https://github.com/rackerlabs/python-cloudbackup-sdk/issues
.. _Milestones: https://github.com/rackerlabs/python-cloudbackup-sdk/issues/milestones
.. _pep8: https://pypi.python.org/pypi/pep8
.. _AUTHORS: https://github.com/rackerlabs/python-cloudbackup-sdk/blob/master/AUTHORS
