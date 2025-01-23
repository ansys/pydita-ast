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

# Predefined directory format

# XML_directory/
# │
# ├── graphics/
# │   ├── .gifs files
# │   └── images files
# |
# ├── links/
# │   └── .db files
# |
# ├── terms/
# │   ├── glb/
# │   │   ├── variable_file         #default value is build_variables.ent
# │   │   ├── global_terms_file     #default value is terms_global.ent
# │   │   └── manual_file           #default value is manuals.ent
# │   └── character_directory/         #default value is ent/
# │       └── .ent files
# └── xml/
#     ├── subdirectorys/
#     │   ├── .xml files
#     │   └── mathgraphics_directory/   #this is a defalut value
#     │       └── .svg files
#     ├── .xml files
#     └── .ent files

from pathlib import Path
from typing import Tuple, Union


def get_paths(
    path: Path,
    graph_path: Union[Path, None] = None,
    link_path: Union[Path, None] = None,
    term_path: Union[Path, None] = None,
    xml_path: Union[Path, None] = None,
) -> Tuple[Path, Path, Path, Path]:
    """Get the paths to the directories needed for the conversion.

    Parameters
    ----------
    path: Path
        Path object of the directory with the predefined format.
    graph_path: Path, optional
        Path object of the directory containing the graphics. The default is ``None``,
        in which case the XML predefined directory format is used.
    link_path: Path, optional
        Path object of the directory containing the links. The default is ``None``,
        in which case the XML predefined directory format is used.
    term_path: Path, optional
        Path object of the directory containing the terms. The default is ``None``,
        in which case the XML predefined directory format is used.
    xml_path: Path, optional
        Path object of the directory containing the XML files. The default is ``None``,
        in which case the XML predefined directory format is used.

    Returns
    -------
    Path
        Path object of the directory containing the graphics.
    Path
        Path object of the directory containing the links.
    Path
        Path object of the directory containing the terms.
    Path
        Path object of the directory containing the XML files.
    """

    if graph_path is None:
        graph_path = path / "graphics"
        if not graph_path.is_dir():
            print(
                f"WARNING: the path {graph_path} does not exist.",
                "Follow the predefined format or enter the graphic",
                "path manually.",  # noqa : E501
            )

    if link_path is None:
        link_path = path / "links"
        if not link_path.is_dir():
            print(
                f"WARNING: the path {link_path} does not exist. Follow the predefined format or enter the link path manually."  # noqa : E501
            )

    if term_path is None:
        term_path = path / "terms"
        if not term_path.is_dir():
            print(
                f"WARNING: the path {term_path} does not exist. Follow the predefined format or enter the term path manually."  # noqa : E501
            )

    if xml_path is None:
        xml_path = path / "xml"
        if not xml_path.is_dir():
            print(
                f"WARNING: the path {xml_path} does not exist. Follow the predefined format or enter the XML path manually."  # noqa : E501
            )

    return graph_path, link_path, term_path, xml_path
