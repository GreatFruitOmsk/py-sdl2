Installing PySDL2
=================
This section provides an overview and guidance for installing PySDL2 on
various target platforms.

Prerequisites
-------------
PySDL2 relies on some 3rd party packages to be fully usable and to
provide you full access to all of its features.

You must have at least one of the following Python versions installed:

* Python 2.7, 3.2+     (http://www.python.org)
* PyPy 1.9.0+          (http://www.pypy.org)

Other Python versions or Python implementations might work, but are
(currently) not officially tested or supported by the PySDL2
distribution.

Installation
------------
You can either use the python way of installing the package or the make
command using the Makefile on POSIX-compatible platforms, such as Linux
or BSD, or the make.bat batch file on Windows platforms.

Simply type ::

  python setup.py install

for the traditional python way or ::

  make install

for using the Makefile or make.bat. Both will try to perform a default
installation with as many features as possible.

Trying out
^^^^^^^^^^
You also can test out PySDL2 without actually installing it. You just
need to set up your ``PYTHONPATH`` to point to the location of the
source distribution package. On Windows-based platforms, you might use
something like ::

   set PYTHONPATH=C:\path\to\pysdl2\:$PYTHONPATH

to define the ``PYTHONPATH`` on a command shell. On Linux/Unix, use ::

   export PYTHONPATH=/path/to/pysdl2:$PYTHONPATH

For bourne shell compatibles or ::

   setenv PYTHONPATH /path/to/pysdl2:$PYTHONPATH

for C shell compatibles. You can omit the `:$PYTHONPATH``, if you did not use
it so far and if your environment settings do not define it.

.. note::

   If you are using IronPython, use ``IRONPYTHONPATH`` instead of
   ``PYTHONPATH``.

Notes on Mercurial usage
^^^^^^^^^^^^^^^^^^^^^^^^
The Mercurial version of PySDL2 is not intended to be used in a
production environment. Interfaces may change from one checkin to
another, methods, classes or modules can be broken and so on. If you
want more reliable code, please refer to the official releases.
