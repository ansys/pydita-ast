# Copyright (C) 2024 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def inquire(self, strarray="", func="", arg1="", arg2=""):
    """Returns system information.

    By default, with no arguments, it returns the working directory.

    >>> mapdl.inquire()
    C:\\Users\\user\\AppData\\Local\\Temp\\ansys_nynvxsaooh

    Parameters
    ----------
    strarray : str, optional
        Name of the string array or parameter that will hold the returned values.
        Normally, if used in a python script you should just work with the
        return value from this method.

    func : str, optional
       Specifies the type of system information returned.  See the
       notes section for more information.

    arg1 : str, optional
        First argument. See notes for ``arg1`` definition.

    arg2 : str, optional
        Second argument. See notes for ``arg1`` definition.

    Returns
    -------
    str
        Value of the inquired item.

    Notes
    -----
    The ``/INQUIRE`` command is valid in any processor.

    .. warning::

       Take note that from version 0.60.4 and later, the command behaviour
       has been changed.
       Previously, the ``StrArray`` argument was omitted. For example:
       >>> mapdl.inquire('DIRECTORY')
       C:\\Users\\user\\AppData\\Local\\Temp\\ansys_nynvxsaooh

       Now this will raise an exception.
       The default behaviour now, requires to input ``StrArray``:
       >>> mapdl.inquire('', 'DIRECTORY')
       C:\\Users\\user\\AppData\\Local\\Temp\\ansys_nynvxsaooh

    **GENERAL FUNC OPTIONS**

    - ``LOGIN`` - Returns the pathname of the login directory on Linux
      systems or the pathname of the default directory (including
      drive letter) on Windows systems.
    - ``DOCU`` - Pathname of the ANSYS documentation directory.
    - ``APDL`` - Pathname of the ANSYS APDL directory.
    - ``PROG`` - Pathname of the ANSYS executable directory.
    - ``AUTH`` - Pathname of the directory in which the license file resides.
    - ``USER`` - Name of the user currently logged-in.
    - ``DIRECTORY`` - Pathname of the current directory.
    - ``JOBNAME`` - Current Jobname.
    - ``RSTDIR`` - Result file directory.
    - ``RSTFILE`` - Result file name.
    - ``RSTEXT`` - Result file extension.
    - ``OUTPUT`` - Current output file name.


    **RETURNING THE VALUE OF AN ENVIRONMENT VARIABLE TO A PARAMETER**

    If ``FUNC=ENV``, the command format is ``/INQUIRE,StrArray,ENV,ENVNAME,Substring``.
    In this instance, ENV specifies that the command should return the
    value of an environment variable.
    The following defines the remaining fields:

    Envname:
        Specifies the name of the environment variable.

    Substring:
        If ``Substring = 1``, the first substring (up to the first colon (:)) is returned.
        If ``Substring = 2``, the second substring is returned, etc. For Windows platforms,
        the separating character is semicolon (;).
        If this argument is either blank or 0, the entire value of the environment
        variable is returned.


    **RETURNING THE VALUE OF A TITLE TO A PARAMETER**

    If ``FUNC = TITLE``, the command format is ``/INQUIRE,StrArray,TITLE,Title_num``.
    In this context, the value of Title_num can be blank or ``1`` through ``5``. If the
    value is ``1`` or blank, the title is returned. If the value is ``2`` through ``5``,
    a corresponding subtitle is returned (``2`` denoting the first subtitle, and so on).


    **RETURNING INFORMATION ABOUT A FILE TO A PARAMETER**

    The ``/INQUIRE`` command can also return information about specified files
    within the file system.
    For these capabilities, the format is ``/INQUIRE,Parameter,FUNC,Fname, Ext, --``.
    The following defines the fields:

    Parameter:
        Name of the parameter that will hold the returned values.

    Func:
        Specifies the type of file information returned:

        EXIST:
            Returns a ``1`` if the specified file exists, and ``0`` if it does not.

        DATE:
            Returns the date stamp of the specified file in the format ``*yyyymmdd.hhmmss*``.

        SIZE:
            Returns the size of the specified file in MB.

        WRITE:
            Returns the status of the write attribute. A ``0`` denotes no write permission while a ``1`` denotes
            write permission.

        READ:
            Returns the status of the read attribute. A ``0`` denotes no read permission while a ``1`` denotes read
            permission.

        EXEC:
            Returns the status of the execute attribute (this has meaning only on Linux). A ``0`` denotes no
            execute permission while a ``1`` denotes execute permission.

        LINES:
            Returns the number of lines in an ASCII file.

    Fname:
        File name and directory path (248 characters maximum, including the characters needed for the
        directory path). An unspecified directory path defaults to the working directory; in this case, you
        can use all 248 characters for the file name.

    Ext:
        Filename extension (eight-character maximum).

    Examples
    --------
    Return the MAPDL working directory
    >>> mapdl.inquire('', 'DIRECTORY')
    C:\\Users\\gayuso\\AppData\\Local\\Temp\\ansys_nynvxsaooh

    Or

    >>> mapdl.inquire()
    C:\\Users\\gayuso\\AppData\\Local\\Temp\\ansys_nynvxsaooh

    Return the job name

    >>> mapdl.inquire('', 'JOBNAME')
    file

    Return the result file name

    >>> mapdl.inquire('', 'RSTFILE')
    'file.rst'
    """
    return self.run(f"/INQUIRE,{strarray},{func},{arg1},{arg2}")
