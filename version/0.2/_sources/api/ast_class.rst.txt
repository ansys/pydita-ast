AST (abstract syntax tree)
==========================

.. currentmodule:: pyconverter.xml2py.ast_tree

An AST (Abstract Syntax Tree) is an abstract syntactic structure of text.
Each node of the tree denotes a construct occurring in the XML file.
Every element the AST contains can be edited using properties
and functions to obtain the desired rendering.

The following classes are used to create the AST:

.. autosummary::
   :toctree: _autosummary/ast_class

   BlockQuote
   Caution
   Chapter
   Code
   Command
   ComputerOutput
   Element
   Emphasis
   Entry
   Example
   Figure
   FileName
   Function
   Graphic
   GuiLabel
   GuiMenu
   GuiMenuItem
   IndexTerm
   InformalExample
   InformalTable
   InlineEquation
   InlineGraphic
   ItemizedList
   Link
   ListItem
   Literal
   Math
   Member
   Note
   OLink
   OrderedList
   Paragraph
   Phrase
   Primary
   ProgramListing
   Quote
   Refentrytitle
   RefMeta
   Refname
   Refnamediv
   Refpurpose
   RefSection
   Replaceable
   Row
   Screen
   SimpleList
   Structname
   SubScript
   SuperScript
   Table
   TBody
   Term
   TGroup
   THead
   Title
   UserInput
   Variablelist
   VarlistEntry
   XRef