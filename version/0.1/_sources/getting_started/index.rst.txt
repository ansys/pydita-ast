Getting started
===============

Installation
------------

Two installation modes of the ``pydita-ast`` package are provided: user and developer.

User installation
^^^^^^^^^^^^^^^^^

Install the latest release for use with this command:

.. code:: bash

    python -m pip install pydita-ast


For developers
^^^^^^^^^^^^^^

Installing the ``pydita-ast`` package in developer mode allows
you to modify the source and enhance it.

Before contributing to the project, see the `PyAnsys Developer's Guide`_.

Follow these steps to install the package in developer mode:

#. Clone the repository:

    .. code:: bash

        git clone https://github.com/ansys/pydita-ast

#. Create a fresh-clean Python environment and activate it. If you require
   additional information on creation of a virtual environment, see the
   official Python `venv`_ documentation.

    .. code:: bash

        # Create a virtual environment
        python -m venv .venv

        # Activate it in a POSIX system
        source .venv/bin/activate

        # Activate it in Windows CMD environment
        .venv\Scripts\activate.bat

        # Activate it in Windows Powershell
        .venv\Scripts\Activate.ps1

#. Make sure you have the latest version of `pip`_:

    .. code:: bash

        python -m pip install -U pip

#. Install the project in editable mode:

    .. code:: bash
    
        python -m pip install -e .

#. Install additional requirements (if needed):

     .. code:: bash

        python -m pip install .[doc,tests]

#. Verify your development installation:

    .. code:: bash
        
        pytest tests -v


Style and testing
-----------------

If required, you can call style commands (such as `black`_, `isort`_,
and `flake8`_) or unit testing commands (such as `pytest`_) from the command line.
However, this does not guarantee that your project is being tested in an isolated
environment, which is why you might consider using `tox`_.


Documentation
-------------

For building documentation, you can run the usual rules provided in the
`Sphinx`_ Makefile:

.. code:: bash

    python -m pip install .[doc]
    make -C doc/ html

    # subsequently open the documentation with (under Linux):
    your_browser_name doc/html/index.html

Distributing
------------

If you would like to create either source or wheel files, start by installing
the building requirements:

.. code:: bash

    python -m pip install -e .[doc,tests]

Then, execute these commands:

    .. code:: bash

        python -m build
        python -m twine check dist/*
