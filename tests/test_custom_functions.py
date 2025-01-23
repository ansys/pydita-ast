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

import pyconverter.xml2py.custom_functions as cf


def test_customfunctions(custom_functions):
    assert "k" in custom_functions._py_names
    assert "    msg = self.run(command, **kwargs)\n" in custom_functions._py_code["k"]
    assert "import re\n" in custom_functions._lib_import["k"]
    assert "    list" in custom_functions._py_returns["kdist"]
    assert "Compute the distance between two keypoints." in custom_functions._py_examples["kdist"]


def test_get_docstring_lists(path_custom_functions):
    path_custom_function = path_custom_functions / "kdist.py"
    (
        list_py_args,
        list_py_params,
        list_py_returns,
        list_py_notes,
        list_py_examples,
        list_py_code,
        list_import,
    ) = cf.get_docstring_lists(path_custom_function)
    "kp1" in list_py_args
    "    list" in list_py_returns
    "Compute the distance between two keypoints." in list_py_examples
    'return parse.parse_kdist(self.run(f"KDIST,{kp1},{kp2}", **kwargs))' in list_py_code
    "import parse\n" in list_import
