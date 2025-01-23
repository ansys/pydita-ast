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

GET_BOLD_COMMANDS = r"([^\*])(\*\*)(\*)(.*?)(\*\*)([^\*])"
BEFORE_DEF = r"[\s\S]*?(?=def "
GET_CLASSNAME = r"(\S+)(?=:)"
GET_CODE_BLOCK = r"(\s*\.\. code:: apdl\n\s*(?: +.+\n)+)"
GET_GROUP = r"(?<=&)(.*?)(?=;)"
# Not used, can be added in case of complications with imports in the future
GET_IMPORTS = r"(?:(?:from [a-zA-Z0-9_.]* import [a-zA-Z0-9_.]* as [a-zA-Z0-9_.]*)|(?:from [a-zA-Z0-9_.]* import [a-zA-Z0-9_.]*)|(?:import [a-zA-Z0-9_.]* as [a-zA-Z0-9_.]*)|(?:import [a-zA-Z0-9_.]*)\s)"  # noqa: E501
GET_ITALIC_COMMANDS = r"([^\*])(\*)(\*)([A-Z]+)(\*)([^\*])"  # TODO: Not supported yet
GET_STAR_COMMANDS = r"([^\*])(\*)([A-Z]+)(\`|\,|\.|\s)"
GET_STAR_FUNCTIONS = r"([^\*\s\\]+)(\*)([^\*\s]+)"
GET_TYPENAME_1OPT = r"(?<=:)(.*)"
GET_TYPENAME_2OPT = r"(?<=:)(.*?)(?=[A-Z][A-Z])"
REPLACE_BOLD_COMMANDS = r"\1\2" + r"\*" + r"\4\5\6"
REPLACE_ITALIC_COMMANDS = r"\1\2" + r"\*" + r"\4\5\6"  # TODO: Not supported yet
REPLACE_STAR_COMMANDS = r"\1" + r"\*" + r"\3\4"
REPLACE_STAR_FUNCTIONS = r"\1\\2\3"
