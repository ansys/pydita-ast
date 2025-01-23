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

from typing import Optional, Union


def enorm(self, enum: Union[str, int] = "", **kwargs) -> Optional[str]:
    """Reorients shell element normals or line element node connectivity.

    APDL Command: ENORM

    Parameters
    ----------
    enum: str, int
        Element number having the normal direction that the
        reoriented elements are to match.

    Notes
    -----
    Reorients shell elements so that their outward normals are
    consistent with that of a specified element. ENORM can also be
    used to reorder nodal connectivity of line elements so that
    their nodal ordering is consistent with that of a specified
    element.

    For shell elements, the operation reorients the element by
    reversing and shifting the node connectivity pattern. For
    example, for a 4-node shell element, the nodes in positions I,
    J, K and L of the original element are placed in positions J,
    I, L and K of the reoriented element. All 3-D shell elements
    in the selected set are considered for reorientation, and no
    element is reoriented more than once during the
    operation. Only shell elements adjacent to the lateral (side)
    faces are considered.

    The command reorients the shell element normals on the same
    panel as the specified shell element. A panel is the geometry
    defined by a subset of shell elements bounded by free edges or
    T-junctions (anywhere three or more shell edges share common
    nodes).

    Reorientation progresses within the selected set until either
    of the following conditions is true:

    - The edge of the model is reached.

    - More than two elements (whether selected or unselected) are
        adjacent to a lateral face.

    In situations where unselected elements might undesirably
    cause case b to control, consider using ENSYM,0,,0,ALL instead
    of ENORM.  It is recommended that reoriented elements be
    displayed and graphically reviewed.

    You cannot use the ENORM command to change the normal
    direction of any element that has a body or surface load. We
    recommend that you apply all of your loads only after ensuring
    that the element normal directions are acceptable.

    Real constant values are not reoriented and may be invalidated
    by an element reversal.

    Examples
    --------
    >>> mapdl.enorm(1)

    """
    return self.run(f"ENORM,{enum}", **kwargs)
