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

import re


def k(self, npt="", x="", y="", z="", **kwargs) -> int:
    """Define a keypoint.

    APDL Command: K

    Defines a keypoint in the active coordinate system [CSYS] for
    line, area, and volume descriptions.  A previously defined
    keypoint of the same number will be redefined.  Keypoints may
    be redefined only if it is not yet attached to a line or is
    not yet meshed.  Solid modeling in a toroidal system is not
    recommended.

    Parameters
    ----------
    npt
        Reference number for keypoint.  If zero, the lowest
        available number is assigned [NUMSTR].

    x, y, z
        Keypoint location in the active coordinate system (may be
        R, θ, Z or R, θ, Φ).

    Returns
    -------
    int
        The keypoint number of the generated keypoint.

    Examples
    --------
    Create keypoint at ``(0, 1, 2)``

    >>> knum = mapdl.k('', 0, 1, 2)
    >>> knum
    1

    Create keypoint at ``(10, 11, 12)`` while specifying the
    keypoint number.

    >>> knum = mapdl.k(5, 10, 11, 12)
    >>> knum
    5

    """
    command = f"K,{npt},{x},{y},{z}"
    msg = self.run(command, **kwargs)

    if msg:
        if not re.search(r"KEYPOINT NUMBER", msg):
            res = re.search(r"(KEYPOINT\s*)([0-9]+)", msg)
        else:
            res = re.search(r"(KEYPOINT NUMBER =\s*)([0-9]+)", msg)

        if res:
            return int(res.group(2))
