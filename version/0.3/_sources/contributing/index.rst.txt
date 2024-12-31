.. _ref_contributing:

Contribute
==========

Overall guidance on contributing to a PyAnsys library appears in the
`Contributing <dev_guide_contributing_>`_ topic
in the *PyAnsys Developer's Guide*. Ensure that you are thoroughly familiar
with this guide before attempting to contribute to PyConverter-XML2Py.

The following contribution information is specific to PyConverter-XML2Py.

Developer installation
----------------------

Follow these steps to install the package in developer mode:

#. Clone the repository:

    .. code:: bash

        git clone https://github.com/ansys/pyconverter-xml2py.git

#. Create a fresh-clean Python environment and activate it. If you require
   additional information on creation of a virtual environment, see the
   official Python `venv`_ documentation.

    .. tab-set::

      .. tab-item:: Linux
        :sync: linux

        ::

          python -m venv .venv
          source .venv/bin/activate

      .. tab-item:: macOS
        :sync: macos

        ::

          python -m venv .venv
          source .venv/bin/activate

      .. tab-item:: Windows
        :sync: windows

        ::

          python -m venv .venv
          .\.venv\Scripts\activate


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
`Sphinx`_ Makefile or make.bat:

.. tab-set::

  .. tab-item:: Makefile

    ::

      python -m pip install .[doc]
      make -C doc html


  .. tab-item:: make.bat

    ::

      python -m pip install .[doc]
      .\doc\make.bat html

Once the documentation is built, you can open it as follows.

.. tab-set::

  .. tab-item:: Linux
      :sync: linux

      By running the command: 
      ::

        your_browser_name doc/html/index.html

  .. tab-item:: macOS
      :sync: macos

      By opening the documentation, which you do by going to the ``doc/html`` directory
      and opening the ``index.html`` file.

  .. tab-item:: Windows
      :sync: windows

      By opening the documentation, which you do by going to the ``doc/html`` directory
      and opening the ``index.html`` file.


Adhere to code style
--------------------

PyConverter-XML2Py follows the PEP8 standard as outlined in the `PyAnsys Developer's Guide
<dev_guide_pyansys_>`_ and implements style checking using
`pre-commit <pre-commit_>`_.

To ensure your code meets minimum code styling standards, run this code:

.. code:: console

  pip install pre-commit
  pre-commit run --all-files

You can also install this as a pre-commit hook by running this code:

.. code:: console

  pre-commit install


This way, it's not possible for you to push code that fails the style checks

.. code:: text

  $ git commit -am "added my cool feature"
  black....................................................................Passed
  blacken-docs.............................................................Passed
  isort....................................................................Passed
  flake8...................................................................Passed
  codespell................................................................Passed
  check for merge conflicts................................................Passed
  debug statements (python)................................................Passed
  Validate GitHub Workflows................................................Passed


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
