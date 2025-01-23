# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
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

from typing import Any, Dict, Literal


def cmlist(
    self,
    name: str = "",
    key: str = "",
    entity: Literal["VOLU", "AREA", "LINE", "KP", "ELEM", "NODE", ""] = "",
    **kwargs: Dict[Any, Any],
) -> None:
    """Lists the contents of a component or assembly.

    APDL Command: CMLIST

    Parameters
    ----------
    name
        Name of the component or assembly to be listed (if blank, list all
        selected components and assemblies). If Name is specified, then
        Entity  is ignored.

    key
        Expansion key:

        0
            Do not list individual entities in the component.

        1 or EXPA
            List individual entities in the component.

    entity
        If Name is blank, then the following entity types can be specified:

        VOLU
            List the volume components only.

        AREA
            List the area components only.

        LINE
            List the line components only.

        KP
            List the keypoint components only

        ELEM
            List the element components only.

        NODE
            List the node components only.

    Notes
    -----
    This command is valid in any processor.  For components, it lists the
    type of geometric entity. For assemblies, it lists the components
    and/or assemblies that make up the assembly.

    Examples of possible usage:
    """
    command = f"CMLIST,{name},{key},{entity}"
    return self.run(command, **kwargs)
