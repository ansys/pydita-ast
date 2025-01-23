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

import shutil

import pyconverter.xml2py.writer as wrt
import pytest


def test_convert(command_map, custom_functions, warning_command_dict):
    assert command_map["/XFRM"].name == "/XFRM"
    assert (
        "Original command: WRITE\n\nShort Description:\nWrites the radiation matrix file.\n\nFunction signature:\nWRITE,"  # noqa : E501
        in command_map["WRITE"].__repr__()
    )
    assert (
        command_map["E"].py_source(custom_functions)
        == '    command = f"E,{i},{j},{k},{l},{m},{n},{o},{p}"\n    return self.run(command, **kwargs)\n'  # noqa : E501
    )
    assert 'def zoom(self, wn: str = "", lab: str = "", x1: str = "", y1: str = "", x2: str = "", y2: str = "", **kwargs):\n    r"""Zooms a region of a display window.\n\n' in command_map[  # noqa : E501
        "/ZOOM"
    ].to_python(
        custom_functions, warning_command_dict
    )
    assert "import re" in command_map["K"].to_python(custom_functions, warning_command_dict)


def test_copy_template_package(cwd):
    new_package_path = cwd / "tmp_directory"
    if new_package_path.is_dir():
        shutil.rmtree(new_package_path)
    new_package_path.mkdir()
    template_path = cwd / "_package"
    wrt.copy_template_package(template_path, new_package_path)
    assert new_package_path.is_dir() is True
    assert (new_package_path / "doc").is_dir() is True
    assert (new_package_path / "LICENSE").is_file() is True
    assert (new_package_path / "doc" / "source" / "_templates").is_dir() is True
    assert (new_package_path / "doc" / "source" / "_templates" / "base.rst").is_file() is True
    shutil.rmtree(new_package_path)


@pytest.fixture
def package_path(cwd):
    return cwd / "package"


def test_write_source_with_custom_functions(
    command_map,
    name_map,
    directory_path,
    cwd,
    package_path,
    path_custom_functions,
    library_name_structured,
):
    wrt.write_source(command_map, name_map, directory_path, cwd, path_custom_functions)
    if not "src" in library_name_structured:
        library_name_structured.insert(0, "src")
    cmd_path = package_path.joinpath(*library_name_structured)
    assert (cmd_path / "apdl" / "abbreviations.py").is_file()
    assert (package_path / "doc" / "source" / "images").is_dir()
    assert (package_path / "doc" / "source" / "images" / "gcmdrsymm1.png").is_file()


def test_write_source_no_custom_function(
    command_map, name_map, directory_path, cwd, package_path, library_name_structured
):
    wrt.write_source(command_map, name_map, directory_path, cwd)
    if not "src" in library_name_structured:
        library_name_structured.insert(0, "src")
    cmd_path = package_path.joinpath(*library_name_structured)
    assert (cmd_path / "apdl" / "abbreviations.py").is_file()
    assert (package_path / "doc" / "source" / "images").is_dir()
    assert (package_path / "doc" / "source" / "images" / "gcmdrsymm1.png").is_file()


def test_write_docs(package_path, package_structure):
    doc_src = wrt.write_docs(package_path, package_structure)
    file = open(doc_src, "r")
    content = file.read()
    file.close()
    assert "API documentation" in content
    assert "apdl/index.rst" in content
