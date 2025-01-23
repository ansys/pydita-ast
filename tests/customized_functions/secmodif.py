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


def secmodif(
    self,
    secid,
    keyword,
    nx="",
    ny="",
    nz="",
    kcn="",
    name="",
    name_new="",
    option="",
    dispPnltVal="",
    RotPnltVal="",
    **kwargs,
):
    """Modifies a pretension section

    APDL Command: SECMODIF

    .. warning::

        This command have specific signature depending on the values of the given
        arguments ``keyword``.

    Parameters
    ----------

    secid : int
        Unique section number. This number must already be assigned to a
        section.

    keyword : str
        * If `Keyword = NORM`:
            SECMODIF,SECID, NORM, NX, NY, NZ, KCN
        * If `Keyword = NAME`:
            SECMODIF,SECID, NAME, Name
        * If `Keyword = JOIN`:
            SECMODIF,SECID, JOIN, Option, dispPnltVal, RotPnltVal

    norm : str
        Keyword specifying that the command will modify the pretension
        section normal direction.

    nx, ny, nz : str
        Specifies the individual normal components to modify.

    kcn : str
        Coordinate system number. This can be either 0 (Global Cartesian),
        1 (Global Cylindrical) 2 (Global Spherical), 4 (Working Plane), 5
        (Global Y Axis Cylindrical) or an arbitrary reference number
        assigned to a coordinate system.

    name : str
        Change the name of the specified pretension section.

    name_new : str
        The new name to be assigned to the pretension section.

    join : str
        Set command actions to apply to joint sections only.

    option : str
        PNLT -- Modify penalty factors for the specified section.

    dispPnltVal : str
        Penalty value for displacement-based constraints:
        - `> 0` -- The number is used as a scaling factor to scale the
            internally calculated penalty values.
        - `< 0` -- The absolute value of the number is used as the penalty
            factor in calculations.

    RotPnltVal : str
        Penalty value for rotation-based constraints.
        - `> 0` -- The number is used as a scaling factor to scale the
            internally calculated penalty values.
        - `< 0` -- The absolute value of the number is used as the penalty
            factor in calculations.


    Notes
    -----
    The SECMODIF command either modifies the normal for a specified
    pretension section, or changes the name of the specified pretension
    surface.
    """
    # Sanity checks
    if keyword.upper() not in ["NORM", "NAME", "JOIN"]:
        raise ValueError(f"The given argument 'keyword' ({keyword}) is not valid.")

    if keyword == "NORM":
        cmd = f"SECMODIF, {secid}, NORM, {nx}, {ny}, {nz}, {kcn}"
    elif keyword == "NAME":
        cmd = f"SECMODIF, {secid}, NAME, {name or nx}, {name_new or ny}"
    elif keyword == "JOIN":
        cmd = f"SECMODIF, {secid}, JOIN, {option or nx},{dispPnltVal or ny},{RotPnltVal or nz}"
    else:
        raise ValueError("We couldn't map the arguments given....")

    self.run(cmd, **kwargs)
