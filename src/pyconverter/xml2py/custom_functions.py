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

import logging as log
from pathlib import Path
from typing import Tuple

import regex as re


def get_docstring_lists(filename: str) -> Tuple[list[str], list[str], list[str], list[str]]:
    """
    Get lists of strings depending on Python file sections.

    Parameters
    ----------
    filename: str
        Path containing the Python file.

    Returns
    -------
    List[str]
        List containing the docstring ``Returns`` section.
    List[str]
        List containing the docstring ``Examples`` section.
    List[str]
        List containing the source code.
    List[str]
        List containing the library import section.
    """
    lines = None
    with open(filename, "r") as pyfile:
        lines = pyfile.readlines()
    bool_def = False
    end_def = False
    bool_param = False
    bool_return = False
    bool_notes = False
    bool_examples = False
    begin_docstring = False
    end_docstring = False
    list_py_args = []
    list_py_params = []
    list_py_returns = []
    list_py_notes = []
    list_py_examples = []
    list_py_code = []
    list_import = []
    for line in lines:
        if "import " in line and bool_def is False:
            list_import.append(line)
        # Need to accept the case where the function is defined in multiple lines
        elif "def " in line and bool_def is False:
            bool_def = True
        if bool_def and not end_def:
            if ")" in line:
                end_def = True
                line = re.search(r".+(?=\))", line)
                if line is not None:
                    line = line.group()
                else:
                    continue
            # TODO: Union types are ignored for now
            if re.search(r"\[(\w+, )+\w+\]", line) is not None:
                line = re.sub(r"\[(\w+, )+\w+\]", "", line)
            elif re.search(r'\[("\w*", )+"\w*"\]', line):
                line = re.sub(r'\[("\w*", )+"\w*"\]', "", line)
            split_def = line.split(",")
            for split_arg in split_def:
                split_arg = split_arg.strip()
                if "**kwarg" in split_arg or split_arg == "self":
                    break
                elif re.search(r"\w+", split_arg) is None:
                    break
                elif ":" in split_arg and "=" in split_arg:
                    find = re.search(r"\w*(?=\:)", split_arg).group()
                    list_py_args.append(find)
                elif "=" in split_arg:
                    find = re.search(r"\w*(?=\=)", split_arg).group()
                    list_py_args.append(find)
                elif "def " in split_arg:
                    pass
                else:
                    find = re.search(r"\S+", split_arg).group()
                    list_py_args.append(find)
        elif '"""' in line and begin_docstring is False:
            begin_docstring = True
        elif '"""' in line and begin_docstring is True:
            bool_return = False
            bool_examples = False
            end_docstring = True
        elif "Parameters\n" in line:
            bool_param = True
            bool_return = False
            bool_examples = False
            bool_notes = False
        elif "Returns\n" in line:
            bool_return = True
            bool_param = False
            bool_examples = False
            bool_notes = False
            list_py_returns.append(line.strip())
        elif "Examples\n" in line:
            bool_examples = True
            bool_param = False
            bool_return = False
            bool_notes = False
            list_py_examples.append(line.strip())
        elif "Notes\n" in line:
            bool_notes = True
            bool_param = False
            bool_return = False
            bool_examples = False
            list_py_notes.append(line.strip())
        # Section order within docstrings: Returns, Notes, Examples
        elif end_docstring is True:
            list_py_code.append(line)
        elif bool_examples is True:
            list_py_examples.append(line.strip())
        elif bool_return is True:
            no_indent = ["int\n", "float\n", "str\n", "-------\n", "None\n", "bool\n"]
            if any(n in line for n in no_indent):
                list_py_returns.append(line.strip())
            else:
                list_py_returns.append(4 * " " + line.strip())
        elif bool_notes is True:
            list_py_notes.append(line.strip())  # Notes are obtained from the converter
        elif bool_param is True:
            no_indent = [
                "int\n",
                "float\n",
                "str\n",
                "-------\n",
                "None\n",
                "bool\n",
                ", optional\n",
            ]
            if any(n in line for n in no_indent):
                list_py_params.append(line.strip())
            else:
                list_py_params.append(4 * " " + line.strip())

    return (
        list_py_args,
        list_py_params,
        list_py_returns,
        list_py_notes,
        list_py_examples,
        list_py_code,
        list_import,
    )


# ############################################################################
# CustomFunctions class
# ############################################################################


class CustomFunctions:
    """Provides for creating customized functions."""

    def __init__(self):
        self._path = ""
        self._py_names = []
        self._py_params = {}
        self._py_returns = {}
        self._py_examples = {}
        self._py_code = {}
        self._lib_import = {}

    def __init__(self, path: Path) -> None:
        self._path = path
        if not Path(path).is_dir():
            raise (FileExistsError, f"The path_functions {path} does not exist.")
        self._py_names = []
        self._py_args = {}
        self._py_params = {}
        self._py_returns = {}
        self._py_notes = {}
        self._py_examples = {}
        self._py_code = {}
        self._lib_import = {}
        for filename in Path(path).glob("*.py"):
            py_name = filename.stem
            self._py_names.append(py_name)
            (
                list_py_args,
                list_py_params,
                list_py_returns,
                list_py_notes,
                list_py_examples,
                list_py_code,
                list_import,
            ) = get_docstring_lists(filename)
            if len(list_py_args) > 0:
                self._py_args[py_name] = list_py_args
            if len(list_py_params) > 0:
                self._py_params[py_name] = list_py_params
            if len(list_py_returns) > 0:
                self._py_returns[py_name] = list_py_returns
            if len(list_py_notes) > 0:
                self._py_notes[py_name] = list_py_notes
            if len(list_py_examples) > 0:
                self._py_examples[py_name] = list_py_examples
            if len(list_py_code) > 0:
                self._py_code[py_name] = list_py_code
            else:
                log.warning(f"No code found in {filename}")
            if len(list_import) > 0:
                self._lib_import[py_name] = list_import

    @property
    def path(self) -> Path:
        """Path object where the customized function files are located."""
        return self._path

    @path.setter
    def path(self, path: Path) -> None:
        self._path = path
        try:
            path.is_dir()
        except FileExistsError:
            raise (FileExistsError, f"The path_functions {path} does not exist.")
        self._py_names = []
        for filename in Path(path).glob("*.py"):
            py_name = filename.stem
            self._py_names.append(py_name)
            (
                list_py_args,
                list_py_params,
                list_py_returns,
                list_py_notes,
                list_py_examples,
                list_py_code,
                list_import,
            ) = get_docstring_lists(filename)
            if len(list_py_args) > 0:
                self._py_args[py_name] = list_py_args
            if len(list_py_params) > 0:
                self._py_params[py_name] = list_py_params
            if len(list_py_returns) > 0:
                self._py_returns[py_name] = list_py_returns
            if len(list_py_notes) > 0:
                self._py_notes[py_name] = list_py_notes
            if len(list_py_examples) > 0:
                self._py_examples[py_name] = list_py_examples
            if len(list_py_code) > 0:
                self._py_code[py_name] = list_py_code
            if len(list_import) > 0:
                self._lib_import[py_name] = list_import

    @property
    def py_names(self) -> list:
        """List with all customized functions located in the folder."""
        return self._py_names

    @property
    def py_args(self) -> dict:
        """Dictionary containing the python arguments if any."""
        return self._py_args

    @property
    def py_params(self) -> dict:
        """Dictionary containing the ``Parameters`` section if any."""
        return self._py_params

    @property
    def py_returns(self) -> dict:
        """Dictionary containing the ``Returns`` section if any."""
        return self._py_returns

    @property
    def py_examples(self) -> dict:
        """Dictionary containing the ``Examples`` section if any."""
        return self._py_examples

    @property
    def py_notes(self) -> dict:
        """Dictionary containing the ``Notes`` section if any."""
        return self._py_notes

    @property
    def py_code(self) -> dict:
        """Dictionary containing the customized source code."""
        return self._py_code

    @property
    def lib_import(self) -> dict:
        """Dictionary containing the needed libraries if any."""
        return self._lib_import
