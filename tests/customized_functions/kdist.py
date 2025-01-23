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

import parse


def kdist(self, kp1="", kp2="", **kwargs) -> list:
    """Calculates and lists the distance between two keypoints.

    APDL Command: KDIST

    Parameters
    ----------
    kp1
        First keypoint in distance calculation.
    kp2
        Second keypoint in distance calculation.

    Returns
    -------
    list
        ``[DIST, X, Y, Z]`` distance between two keypoints.

    Notes
    -----
    KDIST lists the distance between keypoints KP1 and KP2, as
    well as the current coordinate system offsets from KP1 to KP2,
    where the X, Y, and Z locations of KP1 are subtracted from the
    X, Y, and Z locations of KP2 (respectively) to determine the
    offsets.  KDIST is valid in any coordinate system except
    toroidal [CSYS,3].
    This command is valid in any processor.

    Examples
    --------
    Compute the distance between two keypoints.

    >>> kp0 = (0, 10, -3)
    >>> kp1 = (1, 5, 10)
    >>> knum0 = mapdl.k("", *kp0)
    >>> knum1 = mapdl.k("", *kp1)
    >>> dist = mapdl.kdist(knum0, knum1)
    >>> dist
    [13.96424004376894, 1.0, -5.0, 13.0]

    """
    return parse.parse_kdist(self.run(f"KDIST,{kp1},{kp2}", **kwargs))
