.. _ref_source_code:

Source code generation
======================

Source code is automatically generated from the name of the commands
and the parameters defined in the documentation.

Here are the initial command and then the default Python code that
this command generates:

.. tab-set::

    .. tab-item:: Inital command

        .. code:: bash
            
            ACEL,ACEL_X,ACEL_Y,ACEL_Z


    .. tab-item:: Python code generated

        .. code:: python

            def acel(self, acel_x="", acel_y="", acel_z="", **kwargs):
                command = f"ACEL,{acel_x},{acel_y},{acel_z}"
                return self.run(command, **kwargs)


Customized functions
--------------------

The converter can handle code generation for functions that require a
customized code. To specify the folder containing these files, you must
be specified the ``-f`` or ``--func-path`` arguments in the command for
generating the code:

.. code:: bash

    python xml2rst.py -p XML_directory_path -f customized_function_directory_path


In this configuration, the provided code is used for the conversion.

Additionally, any **Returns** and **Examples** sections are taken
into account and added to the Python docstring:


.. tab-set::

    .. tab-item:: Inital command

        .. code:: bash
            
            L2ANG,NL1,NL2,ANG1,ANG2,PHIT1,PHIT2
    

    .. tab-item:: Added customized function

        .. code:: python
        
            import parse


            def l2ang(self, nl1="", nl2="", ang1="", ang2="", phit1="", phit2="", **kwargs) -> int:
                """Generates a line at an angle with two existing lines.

                APDL Command: L2ANG

                Generates a straight line (PHIT1-PHIT2) at an angle (ANG1)
                with an existing line NL1 (P1-P2) and which is also at an
                angle (ANG2) with another existing line NL2 (P3-P4).  If the
                angles are zero the generated line is tangent to the two
                lines.  The PHIT1 and PHIT2 locations on the lines are
                automatically calculated.  Line P1-P2 becomes P1-PHIT1, P3-P4
                becomes P3-PHIT2, and new lines PHIT1-P2, PHIT2-P4, and
                PHIT1-PHIT2 are generated.  Line divisions are set to zero
                (use LESIZE, etc. to modify).

                Parameters
                ----------
                nl1
                    Number of the first line to be hit (touched by the end of
                    the new line).  If negative, assume P1 (see below) is the
                    second keypoint of the line instead of the first.

                nl2
                    Number of the second line to be hit.  If negative, assume
                    P3 is the second keypoint of the line instead of the
                    first.

                ang1
                    Angle of intersection (usually zero or 180) of generated
                    line with tangent to first line.

                ang2
                    Angle of intersection (usually zero or 180) of generated
                    line with tangent to second line.

                phit1
                    Number to be assigned to keypoint generated at hit
                    location on first line (defaults to lowest available
                    keypoint number [NUMSTR]).

                phit2
                    Number to be assigned to keypoint generated at hit
                    location on second line (defaults to lowest available
                    keypoint number [NUMSTR]).

                Returns
                -------
                int
                    Line number of the generated line.

                Examples
                --------
                Create two circles and join them with a line.

                >>> k0 = mapdl.k("", 0, 0, 0)
                >>> k1 = mapdl.k("", 0, 0, 1)
                >>> k2 = mapdl.k("", 0, 0, 0.5)
                >>> carc0 = mapdl.circle(k0, 1, k1)
                >>> carc1 = mapdl.circle(k2, 1, k1)
                >>> lnum = mapdl.l2ang(carc0[0], carc1[0], 90, 90)
                >>> lnum
                9

                """
                command = f"L2ANG,{nl1},{nl2},{ang1},{ang2},{phit1},{phit2}"
                msg = self.run(command, **kwargs)
                if msg:
                    return parse.parse_line_no(msg)


    .. tab-item:: Python code generated

        .. code:: python

            import parse


            def l2ang(self, nl1="", nl2="", ang1="", ang2="", phit1="", phit2="", **kwargs):
                r"""Generates a line at an angle with two existing lines.

                Mechanical APDL Command: L2ANG <https://ansyshelp.ansys.com/Views/Secured/corp/v231/en//ans_cmd/Hlp_C_L2ANG.html>`_

                Parameters
                ----------
                nl1 : str
                    Number of the first line to be hit (touched by the end of the new line). If negative, assume ``P1`` (see below) is the second keypoint of the line instead of the first
                nl2 : str
                    Number of the second line to be hit. If negative, assume ``P3`` is the second keypoint of the line instead of the first.

                ang1 : str
                    Angle of intersection (usually zero or 180) of generated line with tangent to first line.

                ang2 : str
                    Angle of intersection (usually zero or 180) of generated line with tangent to second line.

                phit1 : str
                    Number to be assigned to keypoint generated at hit location on first line (defaults to lowest available keypoint number ( :ref:`numstr` )).

                phit2 : str
                    Number to be assigned to keypoint generated at hit location on second line (defaults to lowest available keypoint number ( :ref:`numstr` )).

                Returns
                -------
                int
                Line number of the generated line.

                Notes
                -----
                Generates a straight line ( ``PHIT1`` - ``PHIT2`` ) at an angle ( ``ANG1`` ) with an existing line ``NL1`` ( ``P1`` - ``P2`` ) and which is also at an angle ( ``ANG2`` ) with another existing line ``NL2`` ( ``P3`` - ``P4`` ). If the angles are zero the generated line is tangent to the two lines. The ``PHIT1`` and ``PHIT2`` locations on the lines are automatically calculated. Line ``P1`` - ``P2`` becomes ``P1`` - ``PHIT1``, ``P3`` - ``P4`` becomes ``P3`` - ``PHIT2``, and new lines ``PHIT1`` - ``P2``, ``PHIT2`` - ``P4``, and ``PHIT1`` - ``PHIT2`` are generated. Line divisions are set to zero (use :ref:`lesize`, etc. to modify).

                Examples
                --------
                Create two circles and join them with a line.

                >>> k0 = mapdl.k("", 0, 0, 0)
                >>> k1 = mapdl.k("", 0, 0, 1)
                >>> k2 = mapdl.k("", 0, 0, 0.5)
                >>> carc0 = mapdl.circle(k0, 1, k1)
                >>> carc1 = mapdl.circle(k2, 1, k1)
                >>> lnum = mapdl.l2ang(carc0[0], carc1[0], 90, 90)
                >>> lnum
                9
                """
                command = f"L2ANG,{nl1},{nl2},{ang1},{ang2},{phit1},{phit2}"
                msg = self.run(command, **kwargs)
                if msg:
                    return parse.parse_line_no(msg)
