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

from click.testing import CliRunner
from pyconverter.xml2py.cli import main


def test_cli_main_group():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0

    assert (
        """A Python wrapper to convert XML documentation into Python source code with"""
        in result.output
    )

    assert "package  Create a Python package from your XML documentation." in result.output
    assert "version  Display current version." in result.output


def test_cli_main_package_group():
    runner = CliRunner()
    result = runner.invoke(main, ["package", "--help"])
    assert result.exit_code == 0

    assert "Create a Python package from your XML documentation." in result.output
    assert "-x, --xml-path PATH" in result.output
    assert "-p, --targ-path PATH" in result.output
    assert "-t, --template-path PATH" in result.output
    assert "-f, --func-path PATH" in result.output
    assert "-r, --run-pre-commit BOOLEAN" in result.output
    assert "-l, --max-length INTEGER" in result.output
