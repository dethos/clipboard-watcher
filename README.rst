clipboard-watcher
=================

This repository contains the code of an experiment, in order to understand
how hard would it be (if possible) to have an application that can monitor
the access of other apps to the clipboard on Linux machines.

At the moment it only supports desktop environments that use X.

To learn more please read the
`original blog post <https://blog.ovalerio.net/archives/2346>`_.

Installation
------------

To build and run this demo app, you will need to have the following libraries
on your system:

* ``libdbus-1-dev``
* ``libglib2.0-dev``

You will also need to have `Poetry <http://www.python.org/>`_ in order to be
able to execute the following commands:

.. code-block::

    $ poetry install
    $ poetry run watcher

Contributions
-------------

All contributions and improvements are welcome.