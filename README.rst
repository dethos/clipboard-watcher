clipboard-watcher
=================

This repository contains the code of an experiment, in order to understand
how hard would it be (if possible) to have an application that can monitor
the access of other apps to the clipboard on Linux machines.

This app can also ask the user for permission before providing the clipboard
contents.

At the moment it only supports desktop environments that use X.

To learn more please read the
`original blog post <https://blog.ovalerio.net/archives/2346>`_.

Installation
------------

To build and run this demo app, you will need to have `Poetry <http://www.python.org/>`_ in order to be
able to execute the following commands:

.. code-block::

    $ poetry install
    $ poetry run watcher --help

Contributions
-------------

All contributions and improvements are welcome.