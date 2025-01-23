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

import logging
from pathlib import Path
import textwrap
from typing import List

from inflect import engine
from lxml.etree import tostring
from lxml.html import fromstring
from pyconverter.xml2py.custom_functions import CustomFunctions
import pyconverter.xml2py.utils.regex_pattern as regp
from pyconverter.xml2py.utils.utils import is_numeric, split_trail_alpha
import regex as re

CONV_EQN = False

if CONV_EQN:
    from py_asciimath.translator.translator import MathML2Tex
    from pylatexenc.latex2text import LatexNodes2Text
else:
    pass

logger = logging.getLogger("py_asciimath.utils")
logger.setLevel(logging.INFO)


# common statements used within the docs to avoid duplication
CONST = {
    # "&thetas;": "θ",  # consider replacing with :math:`\theta`
    "Dtl?": "",
    "Caret?": "",
    "Caret1?": "",
    "Caret 40?": "",
    '``"``': "``",
}

superlatif = ["st", "nd", "rd", "th"]


CLEANUP = {
    ",, ": ", ",
    ", , ": ", ",
    ",. ": ". ",
    " , ": ", ",
    ", )": ")",
    ",)": ")",
    "% ``": "``%",  # Ansys variable names should be pulled inside literals
    "`` %": "%``",  # same
    "\xa0": " ",
    "’": "``",
    "∗": "*",
    "−": "-",
    "…": "...",
}

PY_ARG_CLEANUP = {
    "(": "_",
    ")": "_",
    "+": "plus",
    "blank": "",
    "-": "_",
    "'": "",
    "caret1?": "",
}

# Map XML command to pycommand function
NAME_MAP_GLOB = {}

NO_RESIZE_LIST = ["Variablelist", "Caution", "XMLWarning", "ProgramListing", "Example"]

MISSING_ARGUMENT_DESCRIPTION = """The description of the argument is missing in the Python function.
Please, refer to the `command documentation <url>`_ for further information."""

ADDITIONAL_ARGUMENT_DESCRIPTION = """Additional arguments can be passed to the initial command.
Please, refer to the `command documentation <url>`_ for further information."""


class NameMap:
    def __init__(self, name_map):
        self.name_map = name_map
        global NAME_MAP_GLOB
        NAME_MAP_GLOB = name_map


def to_py_name(name, name_map=None):
    """
    Return a Python-compatible name for a command using the global name map.

    Parameters
    ----------
    name : str
        Name of the command.

    name_map : dict
        Dictionary containing the name map.

    Returns
    -------
    str
        Python-compatible command name.
    """
    if name_map is not None:
        global NAME_MAP_GLOB
        NAME_MAP_GLOB = name_map
    if name in NAME_MAP_GLOB:
        return NAME_MAP_GLOB[name]
    else:
        return name


def get_iter_values(name: str):
    """
    Get the values of an iterator.

    Parameters
    ----------
    name : str
        Name of the parameter containing the iterator.

    Returns
    -------
    tuple(str, int)
        Tuple containing the name of the iterator and the iteration value.
    """
    output = re.search(r"([a-zA-Z_]*)(\d*)", name.strip())
    groups = output.groups()
    name = groups[0]
    iter = groups[1]
    if iter == "":
        iter = 0
    return name, int(iter)


def get_quant_iter_pos(name: str) -> tuple:
    """
    Get the values of a quantity iterator.

    Parameters
    ----------
    name: str
        Name of the parameter containing the iterator.

    Returns
    -------
    tuple
        Tuple containing the iteration value and the position of the iterator.
    """
    output = re.search(r"(?<=\+)\d*", name.strip())  # find the number after the '+'
    iter = output.group()
    position = output.span()
    return int(iter), position


def to_py_arg_name(name: str) -> str:
    """
    Return a Python-compatible name for an argument.

    Parameters
    ----------
    name : str
        Name of the argument.

    Returns
    -------
    str
        Python-compatible argument name.
    """
    initial_arg = str(name).lower().strip()
    arg = initial_arg
    if arg in ["--", "–", ""]:
        return ""
    elif "--" in arg:
        arg = arg.replace("--", "")
        return arg
    elif arg.isdigit():
        return ""
    if arg[0].isdigit():
        p = engine()
        if arg[1].isdigit():
            raise ValueError(f"The code needs to be expanded to handle numbers")
        elif arg[1:3] not in superlatif:
            num_value = p.number_to_words(arg[0])
            arg = f"{num_value}{arg[1:]}"
        else:
            num_value = p.number_to_words(arg[:3])
            arg = f"{num_value}{arg[3:]}"

    for key, value in PY_ARG_CLEANUP.items():
        arg = arg.replace(key, value)
    arg = arg.strip()

    while len(arg) > 0 and arg[-1] == "_":
        arg = arg[:-1]

    if arg in ["type", "class", "property", "format", "dir", "set", "iter"]:
        arg = f"{arg}_"

    return f"{arg}"


def get_complete_args_from_initial_arg(
    initial_args: List[str], elipsis_args: List[str]
) -> List[str]:
    """
    Get the complete argument list from a list with elipsis.

    Parameters
    ----------
    initial_args : list
        List of initial arguments.

    elipsis_args : list
        List of containing the elipsed arguments.

    Returns
    -------
    list
        List of complete pythonnic arguments.

    Examples
    --------
    >>> initial_args = ['energytype', 'cname1', 'cname2', 'cname3', 'cname4', 'cname5', 'cname6']
    >>> elipsis_args = ['Cname1', ' Cname2',' …']
    >>> get_complete_args_from_initial_arg(initial_args, elipsis_args)
    ['cname1', 'cname2', 'cname3', 'cname4', 'cname5', 'cname6']
    """

    first_arg_name = to_py_arg_name(elipsis_args[0])
    name_without_iter, first_num = get_iter_values(first_arg_name)

    complete_args = []
    for i, arg in enumerate(initial_args):
        if name_without_iter in arg:
            complete_args.append(arg)

    return complete_args


def is_elipsis(name: str) -> bool:
    """
    Check if a name is an elipsis.

    Returns
    -------
    bool
        True if the argument is an elipsis, False otherwise.
    """
    if any(elips in name for elips in [". . .", "...", "…"]):
        return True
    return False


def str_types(types, join_str: str) -> str:
    """
    String representation of the parameter types.

    Parameters
    ----------
    types : list
        List of types.

    join_str : str
        String to join the types.

    Returns
    -------
    str
        String representation of the parameter types.

    Examples
    --------
    >>> types = [str, int, float]
    >>> str_types(types, " | ")
    'str | int | float'

    >>> types = [str, int]
    >>> str_types(types, " or ")
    'str or int'
    """
    ptype_str = join_str.join([parm_type.__name__ for parm_type in types])
    return ptype_str


def to_py_signature(py_arg_name, types) -> str:
    """
    Return the Python signature of the argument.

    Parameters
    ----------
    py_arg_name : str
        Python-compatible argument name.

    types : list
        List of types.

    Returns
    -------
    str
        Python signature of the argument.

    Examples
    --------
    >>> py_arg_name = 'energytype'
    >>> types = [str, int, float]
    >>> to_py_signature(py_arg_name, types)
    'energytype: str | int | float = ""'
    """
    if py_arg_name != "":
        kwarg = f'{py_arg_name}: {str_types(types, " | ")} = ""'
    else:
        kwarg = None
    return kwarg


def resize_length(text, max_length=100, initial_indent="", subsequent_indent="", list=False):
    """
    Resize the length of a text.

    Parameters
    ----------
    text : str
        Text to resize.

    max_length : int
        Maximum length of the text to be resized.

    initial_indent : str
        Initial indentation of the text.

    subsequent_indent : str
        Subsequent indentation of the text.

    return_list : bool
        If set to True, the function returns a list of strings.
        Default is False.

    Returns
    -------
    str or list
        Resized text.
    """

    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    # Remove extra whitespace before period
    text = ponctuaction_whitespace(text, ".")
    # Remove extra whitespace before comma
    text = ponctuaction_whitespace(text, ",")

    wrapper = textwrap.TextWrapper(
        width=max_length,
        break_long_words=False,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
    )

    if "\n\n" in text:
        text = text.split("\n\n")
    else:
        text = [text]

    for i, paragraph in enumerate(text):
        text[i] = wrapper.fill(text=paragraph)

    if len(text) > 1:
        output = "\n\n".join(text)
    else:
        output = text[0]

    if list is True:
        output = output.splitlines()

    return output


def get_fragment_code(initial_text, pattern):
    """
    Split the text around a pattern.

    Parameters
    ----------
    initial_text : str
        Initial text to split.

    pattern : str
        Pattern to split the text.

    Returns
    -------
    list
        List of fragments.
    """

    # Split the text around code blocks
    fragments = re.split(pattern, initial_text)
    return fragments


def replace_asterisks_without_code(initial_text):

    # Replace all * with \*
    text = re.sub(
        regp.GET_STAR_COMMANDS, regp.REPLACE_STAR_COMMANDS, initial_text
    )  # Replace ``*DIM`` configurations into ``\*DIM``
    text = re.sub(
        regp.GET_STAR_FUNCTIONS, regp.REPLACE_STAR_FUNCTIONS, text
    )  # Replace ``fac1*fac2`` configurations into ``fac1\*fac2``
    text = re.sub(
        regp.GET_BOLD_COMMANDS, regp.REPLACE_BOLD_COMMANDS, text
    )  # Replace ``***DIM**`` configurations into ``**\*DIM**``
    # text = re.sub(
    #     regp.GET_ITALIC_COMMANDS, regp.REPLACE_ITALIC_COMMANDS, text
    # )  # TODO: Replace ``**DIM*`` configurations into ``*\*DIM*``

    return text


def replace_asterisks(initial_text):

    if ".. code::" in initial_text:
        # Regex pattern that matches RST code blocks
        fragments = get_fragment_code(initial_text, regp.GET_CODE_BLOCK)

        # Process non-code fragments
        for i in range(len(fragments)):
            if not ".. code::" in fragments[i]:
                fragments[i] = replace_asterisks_without_code(fragments[i])

        # Join the fragments and return the result
        output = "".join(fragments).strip()

    else:
        output = replace_asterisks_without_code(initial_text)

    return output


def replace_terms(text, terms):
    """
    Replace terms with their definitions.

    Parameters
    ----------
    text : str
        Text to replace terms.

    terms : dict
        Dictionary containing the terms and their definitions.

    Returns
    -------
    str
        Text with the terms replaced.
    """
    iter = 0
    special_terms = re.findall(r"\&([^\-\;]+)\;", text)
    stop = False
    while len(special_terms) > 0 and not stop:
        iter_special_terms = re.findall(r"\&([^\-\;]+)\;", text)
        for term in special_terms:
            if term in terms:
                text = text.replace(f"&{term};", terms[term])
        # Check if there are still special terms that can be replaced
        if iter_special_terms == re.findall(r"\&([^\-\;]+)\;", text):
            stop = True
        else:
            special_terms = iter_special_terms
        iter += 1

    return text


# ############################################################################
# Element class
# ############################################################################


class Element:
    """Provides the base element."""

    def __init__(self, element, parse_children=True):
        self._element = element
        self._content = []

        if element.text is not None:
            content = " ".join(element.text.split())
            if content:
                self._content.append(content)
        if parse_children:
            for child in element.getchildren():
                self._content.append(parse_element(child))
        if element.tail is not None:
            text = " ".join(element.tail.split())
            if text:
                self._content.append(text)

    @property
    def text_content(self):
        """Text content."""
        return self._element.text_content()

    @property
    def raw(self):
        """Raw string of the element."""
        return tostring(self._element).decode()

    @property
    def tostring(self):
        """Attributes of the element as a dictionary."""
        return tostring(self._element)

    def has_children(self):
        """Return wether the element has children."""
        return bool(len(self._element.getchildren()))

    def get(self, entry):
        """Get an item from an element."""
        return self._element.get(entry)

    @property
    def added(self):
        """Has the revision flag ``added``."""
        return self.get("revisionflag") == "added"

    @property
    def any_isalnum(self):
        """Returns ``True`` if any characters are alphanumeric."""
        return any([char.isalnum() for char in str(self)])

    @property
    def tail(self):
        """Tail of the element as a string."""
        return " ".join([str(item) for item in self._content[1:]])

    def print_tree(self):
        """Print the tree."""
        print(self.types_repr())

    def types_repr(self):
        """Return the string types."""
        return "\n".join([str(type(item)) for item in self])

    def __getitem__(self, index):
        return self._content[index]

    def __len__(self):
        return len(self._content)

    @property
    def children(self):
        """Children of the tree."""
        return self._content

    @property
    def children_types(self):
        """Types of the children."""
        return [type(child).__name__ for child in self.children]

    def get_children_by_type(self, type_name):
        """Get children of a specific type."""
        specific_children = []
        for child in self.children:
            if type(child).__name__ == type_name:
                specific_children.append(child)
        return specific_children

    def get_titles_in_element_list(list_element):
        """Get the titles of the elements in a list of elements."""
        return [element.title for element in list_element]

    @property
    def title(self):
        """Element title."""
        return self.find("Title")

    @property
    def content(self):
        """Text content."""
        return self._content

    def __repr__(self):
        return "".join([str(item) for item in self._content])

    @property
    def id(self):
        """ID of the element."""
        return self._element.get("id")

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    items.append(
                        item.to_rst(
                            indent,
                            max_length=max_length,
                            links=links,
                            base_url=base_url,
                            fcache=fcache,
                        )
                    )
                elif item.tag in item_needing_links_base_url:
                    items.append(
                        item.to_rst(indent, max_length=max_length, links=links, base_url=base_url)
                    )
                elif item.tag in item_needing_fcache:
                    items.append(item.to_rst(indent=indent, max_length=max_length, fcache=fcache))
                else:
                    items.append(item.to_rst(indent=indent, max_length=max_length))
            else:
                items.append(
                    resize_length(
                        str(item),
                        max_length=max_length,
                        initial_indent=indent,
                        subsequent_indent=indent,
                    )
                )
        return " ".join(items)

    def rec_find(self, _type, terms=None):
        """Find the first type matching a given type string recursively."""
        for item in self:
            if type(item).__name__ == _type:
                if _type == "Refname" or _type == "Refnamediv":
                    item.terms = terms
                return item
            if isinstance(item, Element):
                subitem = item.rec_find(_type)
                if subitem is not None:
                    return subitem
        return None

    def find(self, _type, terms=None):
        """Find the first type matching a given type string."""
        for item in self:
            if type(item).__name__ == _type:
                if _type == "Refname" or _type == "Refnamediv":
                    if terms == None:
                        logging.error("ERROR: terms are not defined for a 'Refname' class.")
                    item.terms = terms
                return item
        return None

    def find_all(self, _type, recursive=False, terms=None):
        """Find all types matching a given type string."""
        items = []
        for item in self:
            if type(item).__name__ == _type:
                if _type == "Refname" or _type == "Refnamediv":
                    item.terms = terms
                items.append(item)
            elif recursive and isinstance(item, Element):
                items.extend(item.find_all(_type))

        return items

    @property
    def next_elem(self):
        """Next element."""
        elem = self._element.getnext()
        return parse_element(elem) if elem is not None else elem

    @property
    def prev_elem(self):
        """Previous element."""
        elem = self._element.getprevious()
        return parse_element(elem) if elem is not None else elem

    @property
    def tag(self):
        """Element tag."""
        return self._element.tag


class ItemizedList(Element):
    """Provides the itemized list element."""

    def __repr__(self):
        return "\n".join([f"* {str(item).strip()}" for item in self])

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        lines = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    item_lines = item.to_rst(
                        indent, links=links, base_url=base_url, fcache=fcache
                    ).splitlines()
                elif item.tag in item_needing_links_base_url:
                    item_lines = item.to_rst(indent, links=links, base_url=base_url).splitlines()
                elif item.tag in item_needing_fcache:
                    item_lines = item.to_rst(indent=indent, fcache=fcache).splitlines()
                else:
                    item_lines = item.to_rst(indent).splitlines()
            else:
                item_lines = str(item).splitlines()

            rst_list = []
            if item_lines and isinstance(item, Member):
                line = (
                    item_lines[0].to_rst()
                    if isinstance(item_lines, Element)
                    else str(item_lines[0])
                )
                rst_list.append(line)
                for line in item_lines[1:]:
                    text = line.to_rst(indent) if isinstance(line, Element) else str(line)
                    rst_list.append(textwrap.indent(text, prefix=indent))

            else:
                rst_list = item_lines

            new_rst_list = []

            if ".. code::" in "\n".join(rst_list):
                lines.extend(rst_list)

            else:
                for line in rst_list:
                    new_rst_list.extend(
                        resize_length(
                            line,
                            max_length=max_length,
                            initial_indent=indent,
                            subsequent_indent=indent,
                            list=True,
                        )
                    )

                lines.extend(new_rst_list)

        # lists must have at least one line proceeding
        lines = ["", ""] + lines + [""]

        return "\n".join(lines)


class SimpleList(ItemizedList):
    """Provides the simple itemized list element."""

    def __repr__(self):
        return "\n".join([f"* {str(item).strip()}" for item in self])


class Member(Element):
    """Provides the member element for a simple itemized list."""

    pass


def ponctuaction_whitespace(text, ponctuation):
    pattern = r"\S\h+\{ponctuation}".format(ponctuation=ponctuation)
    extra_space = re.findall(pattern, text)
    if extra_space:
        for character in list(set(extra_space)):  # remove duplicates in extra_space list
            assigned_character = character[0]
            if assigned_character in ["*", ")", "?"]:
                pattern = r"\{assigned_character}\h+\{ponctuation}".format(
                    assigned_character=assigned_character, ponctuation=ponctuation
                )
            else:
                pattern = r"{assigned_character}\h+\{ponctuation}".format(
                    assigned_character=assigned_character, ponctuation=ponctuation
                )
            repl = r"{assigned_character}{ponctuation}".format(
                assigned_character=assigned_character, ponctuation=ponctuation
            )
            text = re.sub(pattern, repl, text)
    return text


class OrderedList(Element):
    """Provides the ordered list element."""

    def to_rst(self, indent="", max_length=100, links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        ordered_list = []
        for item in self:
            if item.tag in item_needing_links_base_url:
                rst_item = item.to_rst(indent, links=links, base_url=base_url)
            else:
                rst_item = item.to_rst(indent)
            rst_item = re.sub(r"\s+", " ", rst_item.lstrip())  # Remove extra whitespaces

            resized_item = resize_length(
                rst_item, max_length=max_length, initial_indent="", subsequent_indent=""
            )
            ordered_list.append(resized_item)
        return "\n\n".join(ordered_list)


class ListItem(Element):
    """Provides the list item element."""

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    rst_item = item.to_rst(
                        indent,
                        links=links,
                        base_url=base_url,
                        fcache=fcache,
                    )
                elif item.tag in item_needing_links_base_url:
                    rst_item = item.to_rst(
                        indent=indent, max_length=max_length, links=links, base_url=base_url
                    )
                elif item.tag in item_needing_fcache:
                    rst_item = item.to_rst(indent=indent, max_length=max_length, fcache=fcache)
                else:
                    rst_item = item.to_rst(indent=indent, max_length=max_length)
            else:
                rst_item = str(item)

            items.append(rst_item)

        rst_list_item = "\n".join(items)
        return rst_list_item


class FileName(Element):
    """Provides the filename element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        content = self[0]
        if "*" in content:
            content = content.replace("*", r"\*")
        return f":file:`{content}` {self.tail}"


class OLink(Element):
    """Provides the external link element."""

    def __init__(self, element):
        super().__init__(element)

    @property
    def targetptr(self):
        """Value for the ``targetptr`` contained in the OLink element."""
        return self.get("targetptr")

    @property
    def targetdoc(self):
        """Value for the ``targetdoc`` parameter contained in the OLink element."""
        return self.get("targetdoc")

    def to_rst(self, indent="", max_length=100, links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        key = f"{self.targetptr}"
        if (links or base_url) is None:
            logger.error("ERROR in the links or the base_url definitions - OLink class.")
        if key in links:
            root_name, root_title, href, text = links[key]
            link = f"{base_url}{root_name}/{href}"
            content = self.text_content
            content = content.replace("\n", "")
            content = content.replace("\r", "")
            while "  " in content:
                content = content.replace("  ", " ")
            if len(content) > 1 and content[0] == "":
                content = content[1:]
            content = text if content == "" else content
            content = content.strip()
            tail = self.tail
            tail = tail.replace("\n", "")
            tail = tail.replace("\r", "")

            rst_link = f"`{content} <{link}>`_ {self.tail}"

        else:
            rst_link = super().to_rst(indent)

        return rst_link


class Paragraph(Element):
    """Provides the paragraph element."""

    def __repr__(self):
        lines = [""]
        lines.append(" ".join([str(item) for item in self._content]))
        lines.append("\n")
        return "".join(lines)

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        items = []
        for item in self:
            if isinstance(item, Element):
                if isinstance(item, Variablelist):
                    items.append(
                        "\n\n"
                        + item.to_rst(
                            indent=indent,
                            max_length=max_length,
                            links=links,
                            base_url=base_url,
                            fcache=fcache,
                        )
                    )
                else:
                    if item.tag in item_needing_all:
                        items.append(
                            item.to_rst(
                                indent=indent,
                                max_length=max_length,
                                links=links,
                                base_url=base_url,
                                fcache=fcache,
                            )
                        )
                    elif item.tag in item_needing_links_base_url:
                        items.append(
                            item.to_rst(
                                indent=indent, max_length=max_length, links=links, base_url=base_url
                            )
                        )
                    elif item.tag in item_needing_fcache:
                        items.append(
                            item.to_rst(indent=indent, max_length=max_length, fcache=fcache)
                        )
                    else:
                        items.append(item.to_rst(indent=indent, max_length=max_length))
            else:
                items.append(
                    resize_length(
                        str(item),
                        max_length=max_length,
                        initial_indent=indent,
                        subsequent_indent=indent,
                    )
                )

        rst_item = " ".join(items) + "\n\n"

        intersection_types = set(NO_RESIZE_LIST).intersection(set(self.children_types))
        if len(intersection_types) == 0 and "* " not in rst_item:
            rst_item = resize_length(
                rst_item,
                max_length=max_length,
                initial_indent=indent,
                subsequent_indent=indent,
            )

        return rst_item


class Phrase(Paragraph):
    """Provides the phrase element."""

    def __repr__(self):
        return " ".join([str(item) for item in self._content])


class Structname(Element):
    """Provides the structure name element."""

    pass


class Title(Element):
    """Provides the title element."""

    def __repr__(self):
        return " ".join([str(item) for item in self._content]) + "\n"


class Emphasis(Element):
    """Provides the emphasis element."""

    @property
    def role(self):
        """Return the role parameter value contained in the Emphasis element."""
        return self._element.get("role")

    def to_rst(self, indent="", max_length=100, links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        content = str(self[0])
        if self.role == "bold":
            content = f"**{content}** "
        # elif self.role == "italic":
        #     # TODO: this isn't the correct way of making text itallic
        #     content = f"{content} "
        # elif self.role == 'var':
        # content = f"``{self[0]}`` "
        else:
            content = f"{content} "

        items = []
        for item in self[1:]:
            if isinstance(item, Element):
                if item.tag in item_needing_links_base_url:
                    items.append(item.to_rst(indent, links=links, base_url=base_url))
                else:
                    items.append(item.to_rst(indent))
            else:
                items.append(
                    resize_length(
                        str(item),
                        max_length=max_length,
                        initial_indent=indent,
                        subsequent_indent=indent,
                    )
                )

        return content + " ".join(items)


class Example(Element):
    """Provides the example element."""

    def to_rst(self, indent="", max_length=100):
        rst_example = []
        for item in self:
            if isinstance(item, Title):
                title = item.to_rst(indent=indent, max_length=max_length)
                if not "Command" in item.children_types:
                    rst_item = f"**{title}**\n"
                else:
                    rst_item = f"{title}"
            elif isinstance(item, Element):
                rst_item = item.to_rst(indent=indent, max_length=max_length)
            else:
                rst_item = str(item)
            rst_example.append(rst_item)

        return "\n".join(rst_example)


class InformalExample(Element):
    """Provides the informal example element."""

    def __repr__(self):
        lines = ["\n"]
        if self.title:
            lines.append(f"Example:\n")
        else:
            lines.append(f"Example: {self.title}\n")
        lines.extend([f"{line}" for line in self._content])  # self._content.splitlines()
        return "\n".join(lines)


class GuiMenu(Element):
    """Provides the GUI menu element."""

    pass


class Replaceable(Element):
    """Provides the replaceable element."""

    @property
    def is_equals(self):
        """Replaceable equals something."""
        # return self.tail.startswith("=")
        return False

    @property
    def content_equals(self):
        """Content of the element after handling the '=' sign."""
        words = self.tail.split("=")[1].split()
        if not words:
            # probably a literal
            next_elem = self.next_elem
            parm = next_elem[0]
            next_elem.content[0] = ""
        else:
            parm = words[0]

        if len(words) > 1:
            tail = " ".join(words[1:])
        else:
            tail = ""
        if parm.startswith('"'):
            # quoted parm
            ii = parm[1:].find('"') + 2
            parm, extra = parm[:ii], parm[ii:]
        else:
            parm, extra = split_trail_alpha(parm)
        tail = f"{extra} {tail}"

        if not is_numeric(parm) and not parm.startswith('"'):
            parm = f'"{parm}"'

        return f"``{self.content[0].lower()}={parm}`` {tail}"

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        tail = self.tail
        if tail and "*" in tail:
            tail = self.tail.replace("*", r"\*")
        rst_replaceable = f"``{self.content[0]}`` {tail}"
        if isinstance(self.prev_elem, Command):
            if any([self.content[0] in arg for arg in self.prev_elem.args]):
                rst_replaceable = f"{self.tail}"
        if self.is_equals:
            rst_replaceable = self.content_equals
        return rst_replaceable


class ProgramListing(Element):
    """Provides the program listing element."""

    @property
    def source(self):
        """Return the source value."""
        text = self._element.text
        if "Replaceable" in self.children_types:
            text = " ".join([str(item) for item in self])
        elif text is None:
            text = "\n".join(str(item) for item in self.content)
        return text

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        header = f"\n\n{indent}.. code:: apdl\n\n"
        source_code = header + textwrap.indent(self.source, prefix=indent + " " * 3) + "\n\n"
        items = []

        for item in self:
            # Replaceable elements are handled in source code
            if isinstance(item, Replaceable):
                pass
            elif isinstance(item, Element):
                items += item.to_rst(indent=indent, max_length=max_length)
            else:  # if isinstance(item, str):
                item_in_source = re.search(r"\S+", item).group()
                if item_in_source and item_in_source in source_code:
                    items += source_code
                else:
                    items += item

        rst_item = "".join(items)
        return rst_item


def resize_element_list(text, max_length=100, initial_indent="", subsequent_indent=""):
    element_list = re.finditer(r"^\* ", text)
    element_list = resize_length(
        text, max_length, initial_indent=initial_indent, subsequent_indent=subsequent_indent
    )
    return element_list


class Variablelist(Element):
    """Provides the variable list."""

    def __init__(self, element):
        super().__init__(element)

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        active_items = []
        for item in self:
            if isinstance(item, VarlistEntry) and not item.active:
                continue
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    rst_item = item.to_rst(
                        indent,
                        links=links,
                        base_url=base_url,
                        fcache=fcache,
                    )
                elif item.tag in item_needing_links_base_url:
                    rst_item = item.to_rst(indent=indent, links=links, base_url=base_url)
                elif item.tag in item_needing_fcache:
                    rst_item = item.to_rst(indent=indent, fcache=fcache)
                else:
                    rst_item = item.to_rst(indent=indent)
            else:
                rst_item = str(item)

            if type(item) != str and len(item.children) > 1 and type(item[1]) != str:
                intersection_types = set(NO_RESIZE_LIST).intersection(set(item[1].children_types))
                if len(intersection_types) == 0 and "* " not in rst_item:
                    initial_indent = indent
                    subsequent_indent = initial_indent + " " * 2
                    rst_item = resize_element_list(
                        rst_item,
                        max_length,
                        initial_indent=initial_indent,
                        subsequent_indent=subsequent_indent,
                    )
                else:
                    rst_item = textwrap.indent(rst_item, prefix=indent * 2)
            else:
                initial_indent = indent + " "
                subsequent_indent = indent + " " * 2
                rst_item = resize_element_list(
                    rst_item,
                    max_length,
                    initial_indent=initial_indent,
                    subsequent_indent=subsequent_indent,
                )
            active_items.append(rst_item)

        rst_varlist = "\n".join(active_items) + "\n"
        return rst_varlist

    @property
    def terms(self):
        """List containing the terms of the element."""
        return [str(item.term) for item in self if isinstance(item, VarlistEntry)]


class RefSection(Element):
    """Provides the reference section element."""

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        items = []
        for item in self[1:]:
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    items.append(
                        item.to_rst(
                            indent=indent,
                            links=links,
                            base_url=base_url,
                            fcache=fcache,
                        )
                    )
                elif item.tag in item_needing_links_base_url:
                    items.append(item.to_rst(indent=indent, links=links, base_url=base_url))
                elif item.tag in item_needing_fcache:
                    items.append(item.to_rst(indent=indent, fcache=fcache))
                else:
                    items.append(item.to_rst(indent=indent))
            else:
                items.append(str(item))
        rst_refsection = "\n".join(items)
        return rst_refsection


class VarlistEntry(Element):
    """Provides the variable list entry element."""

    @property
    def parm_types(self):
        """One or more parameter types.

        This is guessed from any subvarlists. If unavailable, then it's guessed
        from the description of the variable.

        This is either a string, float, or integer (or some combination thereof).

        """
        varlist = self.rec_find("Variablelist")

        parm_types = [str]
        if varlist is not None:
            terms = varlist.terms
            if terms:
                terms_numeric = [is_numeric(term) for term in terms]
                if all(terms_numeric):
                    parm_types = [int]
                elif any(terms_numeric):
                    parm_types = [int, str]
                else:
                    parm_types = [str]

                # consider checking for bool
                # terms_numeric = set(terms) == set(['1', '0'])

        return parm_types

    @property
    def term(self):
        """Term of the element."""
        return self.content[0]

    @property
    def text(self):
        """Text of the element."""
        return self.content[1]

    def py_term(self, links=None, base_url=None):
        """Python-compatible term."""
        if self.is_arg:
            arg = str(self.term).lower()

            if arg == "type":
                arg = "type_"

            if self.parm_types is not None:
                ptype_str = " or ".join([parm_type.__name__ for parm_type in self.parm_types])

                return f"{arg} : {ptype_str}"
            return f"{arg}"

        if self.term.tag in item_needing_links_base_url:
            arg = self.term.to_rst(links=links, base_url=base_url).replace("--", "").strip()
        else:
            arg = self.term.to_rst().replace("--", "").strip()

        # sanity check
        if arg.lower() == "blank":
            arg = ""

        if not is_numeric(arg):
            return f"{arg}"

        return arg

    def __repr__(self):
        return f"{self.term}\n{self.content[1]}"

    @property
    def active(self):
        """Return if this argument is active."""
        if not self.is_arg:
            return True

        # Otherwise, simply check for any alphanumeric characters in the
        # term. Normally these terms are just '--' or '--,--'
        return self.term.any_isalnum

    @property
    def is_arg(self):
        """Return ``True`` when this variable list is for an argument."""
        anc = list(self._element.iterancestors())
        if not anc:
            return False
        val = anc[0].tag == "variablelist" and anc[1].tag == "refsynopsisdiv"
        if not val:
            # miscoded?
            elem_id = anc[1].get("id")
            if elem_id:
                val = "argdescript" in elem_id
        return val

    def py_text(self, links=None, base_url=None, fcache=None):
        """Remove mention of graphical interaction."""
        if self.text.tag in item_needing_all:
            rst = self.text.to_rst(links=links, base_url=base_url, fcache=fcache)
        elif self.text.tag in item_needing_links_base_url:
            rst = self.text.to_rst(links=links, base_url=base_url)
        elif self.text.tag in item_needing_fcache:
            rst = self.text.to_rst(links=links, fcache=fcache)
        else:
            rst = self.text.to_rst()
        if "graphical" in rst:
            valid = []
            for sentence in rst.split(". "):
                if "GUI" not in sentence:
                    valid.append(sentence)
            rst = ". ".join(valid)

        return rst

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        py_term = self.py_term(links=links, base_url=base_url)
        py_text = self.py_text(links=links, base_url=base_url, fcache=fcache)

        if "``" in py_term:
            py_term = py_term.replace("``", "")

        if re.search(r"`.+`_", py_term) is None:
            py_term = f"``{py_term}``"

        intersection_types = set(NO_RESIZE_LIST).intersection(self.text.children_types)
        if len(intersection_types) == 0 and "* " not in py_text:
            py_text = resize_length(
                py_text, max_length=max_length, initial_indent=indent, subsequent_indent=indent
            )

        split_py_text = py_text.splitlines()

        if len(split_py_text) > 1:

            first_line = split_py_text[0]
            rest_lines = split_py_text[1:]

            rest_lines = textwrap.indent("\n".join(rest_lines), prefix=" " * 2)

            py_text = f"{first_line}\n{rest_lines}"

        lines = [f"* {py_term} - {py_text}"]
        output = "\n".join(lines)

        return output


class Term(Element):
    """Provides the term element."""

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""

        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_links_base_url:
                    items.append(item.to_rst(links=links, base_url=base_url))
                elif item.tag in item_needing_fcache:
                    items.append(item.to_rst(fcache=fcache))
                else:
                    items.append(item.to_rst())
            else:
                items.append(str(item))

        text = ", ".join(items)
        if text.endswith("–"):
            text = text[:-1]
        return text

    def __repr__(self):
        out = super().__repr__()
        return ", ".join(out.split(","))


class GuiLabel(Element):
    """Provides the GUI label element."""

    pass


class GuiMenuItem(Element):
    """Provides the GUI menu item element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        gui_rst = f"``{self[0]}`` {self.tail}"
        return gui_rst


class SuperScript(Element):
    """Provides the superscript element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        return f":sup:`{self.content[0]}` {self.tail}"


class Code(Element):
    """Provides the code element."""

    pass


class _Math(Element):
    def __init__(self, element):
        self._element = element
        self._content = []
        self._parse_equation(element)

    def _parse_equation(self, eqn):
        if eqn is not None:
            raw = tostring(eqn).decode().replace("xmlns:m", "xmlns")
            raw = raw.replace('display="block"', "")
            raw = raw.replace("<mtext>&#8202;</mtext>\n", "")
            raw = raw.replace("<mtext>&#8201;</mtext>\n", "")
        try:
            parsed = MathML2Tex().translate(raw, network=False, from_file=False)
            parsed = parsed.replace("\\hspace", "").strip()
            self._content = [parsed]
        except NameError:
            self._content = [""]

    def __repr__(self):
        try:
            return LatexNodes2Text().latex_to_text(self.equation)
        except NameError:
            return "<Equation>"

    @property
    def equation(self):
        """Return the equation related to the math element."""
        return self.content[0][1:-1]


class Math(_Math):
    """Provides the math element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        lines = ["", "", f"{indent}.. math::\n"]
        lines.append(textwrap.indent(self.equation, prefix=indent + " " * 4))
        lines.append("")
        return "\n".join(lines)


class InlineEquation(_Math):
    """Provides the inline equation element."""

    def __init__(self, element):
        self._element = element
        self._content = []
        self._parse_equation(element.find("math"))

    @property
    def tail(self):
        """Return the tail of the element as a string."""
        return self.raw.split("</inlineequation>")[-1].replace("\n", "")

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        return f":math:`{self.equation.strip()}` {self.tail}"


class SubScript(Element):
    """Provides the subscript element."""

    def __init__(self, element):
        super().__init__(element)


class InlineGraphic(Element):
    """Provides the inline graphic element."""

    def fileref(self):
        """File reference."""
        return self._element.get("fileref")


class Quote(Element):
    """Provides the quote element."""

    def __init__(self, element):
        super().__init__(element)
        # self._content[0] = f"{self._content[0]}"

    @property
    def quote(self):
        """Quote value."""
        return self[0]

    def __repr__(self):
        return f'"{self.quote}" {self.tail}'


class Link(Element):
    """Provides the link element."""

    def __init__(self, element):
        super().__init__(element)
        self._linkend = element.get("linkend")

    @property
    def linkend(self):
        """Link."""
        return self._linkend

    def __repr__(self):
        return str(self.linkend)

    def to_rst(self, indent="", max_length=100, links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        if (links or base_url) is None:
            logger.error(
                "ERROR exists in the links or the 'base_url' definitions in the 'Link' class."
            )
        tail = " ".join([str(item) for item in self])
        tail = self.tail.replace("\n", "")
        if self.linkend in links:
            root_name, root_title, href, text = links[self._linkend]
            text = text.replace("\n", "")
            link = f"{base_url}{root_name}/{href}"
            return f"`{text} <{link}>`_ {tail}"

        # missing link...
        return tail


class XRef(Link):
    """Provides the cross reference element."""

    @property
    def tail(self):
        """Tail of the element as a string."""
        return " ".join([str(item) for item in self._content])

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        # disabled at the moment
        # return f':ref:`{self.linkend}`{self.tail}'
        return self.tail


class UserInput(ProgramListing):
    """Provides the user input element."""

    pass


class Screen(Element):
    """Provides the screen element."""

    pass


class Literal(Element):
    """Provides the literal output element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        return f"``{self.content[0]}`` {self.tail}"


class Caution(Element):
    """Provides the caution element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        lines = ["", "", ".. warning::", ""]
        indent = indent + " " * 4
        lines.append(
            resize_length(
                str(self), max_length=max_length, initial_indent=indent, subsequent_indent=indent
            )
        )
        lines.append("")
        return "\n".join(lines)


class Graphic(Element):
    """Provides the graphic element."""

    @property
    def entityref(self):
        """Value of the ``entityref`` parameter contained in the graphic element."""
        entityref = self.get("entityref")
        if entityref is not None:
            entityref = entityref.strip()
        return entityref

    def to_rst(self, indent="", max_length=100, fcache=None):
        """Return a string to enable converting the element to an RST format."""

        if self.entityref is None:
            # probably a math graphics
            fileref = self.get("fileref")
            if fileref is not None and "mathgraphics" in fileref:
                return ""

        if self.entityref == "Linebrk":
            return f"\n\n"

        if self.entityref in fcache:
            filename = fcache[self.entityref]
            text = f"\n\n{indent}.. figure:: ../../images/{filename}\n"
            return text

        return ""


class Function(Element):
    """Provides the function element."""

    pass


class Note(Element):
    """Provides the note element."""

    pass


class BlockQuote(Element):
    """Provides the block quote element."""

    def to_rst(self, indent="", max_length=100, links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_all:
                    items.append(
                        item.to_rst(
                            indent,
                            max_length=max_length,
                            links=links,
                            base_url=base_url,
                            fcache=fcache,
                        )
                    )
                elif item.tag in item_needing_links_base_url:
                    items.append(
                        item.to_rst(indent, max_length=max_length, links=links, base_url=base_url)
                    )
                elif item.tag in item_needing_fcache:
                    items.append(item.to_rst(indent=indent, max_length=max_length, fcache=fcache))
                else:
                    items.append(item.to_rst(indent, max_length=max_length))
            else:
                if "* " not in str(item):
                    items.append(
                        resize_length(
                            str(item),
                            max_length=max_length,
                            initial_indent=indent,
                            subsequent_indent=indent,
                        )
                    )
                else:
                    items.append(str(item))
        return "\n\n" + "".join(items) + "\n\n"


class RefMeta(Element):
    """Provides the reference metadata element."""

    @property
    def refentry_title(self):
        """Title of the referency entry."""
        title = self.rec_find("Refentrytitle")
        if title is not None:
            title = str(title).strip()
        else:
            title = ""
        return title


class IndexTerm(Element):
    """Provides the index term element."""

    pass


class Primary(Element):
    """Provides the primary element."""

    pass


def parse_element(element):
    """Parse a single element."""
    if element.tag not in parsers:
        if "cython_function" in str(type(element.tag)):
            return Element(element)

        # warnings.warn(f"Unsupported element tag '{element.tag}'")
        return Element(element)

    return parsers[element.tag](element)


def parse_children(element):
    """
    Parse the children of an element.

    Returns
    -------
    list
        List of the children of the element.
    """

    children = []
    for child in element.getchildren():
        if child.tag in parsers:
            children.append(parsers[child.tag](child))
        else:
            children.append(child)
    return children


def parse_text(element):
    """Parse a paragraph element."""
    if element is not None:
        return " ".join(element.text_content().split())
    return ""


class TGroup(Element):
    """Provides the tgroup element, which contains the header and body rows of a table."""

    @property
    def n_col(self):
        """Number of columns."""
        return self._element.get("cols")

    @property
    def thead(self):
        """THead."""
        return self.find("THead")

    @property
    def tbody(self):
        """TBody."""
        return self.find("TBody")

    @property
    def row_in_tbody(self):
        """List of the rows in the TBody."""
        return self.find("TBody").find_all("Row")

    def to_rst(self, indent="", links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        l_head = 0

        if self.thead is not None:
            rows, l_head = self.thead.to_rst(links=links, base_url=base_url)
        else:
            rows = [".. flat-table::"]
            rows.append("")

        if self.row_in_tbody is not None:

            rst_tbody = self.tbody.to_rst(l_head, links=links, base_url=base_url)
            if len(rst_tbody) > 0:
                rows += rst_tbody

        rst_tgroup = "\n".join(rows)
        return rst_tgroup


class Table(Element):
    """Provides the table element"""

    @property
    def title(self):
        """Table title."""
        return self.find("Title")

    @property
    def tgroup(self):
        """TGroup."""
        return self.find("TGroup")

    def to_rst(self, indent="", max_length=100, links=None, base_url=None):
        """Return a string to enable converting the element to an RST format."""
        # For now, Tables don't support ``max_length``
        lines = []
        if self.title is not None:
            title = f"{self.title}".strip()
            lines.append(f"**{title}**\n")
            lines.append("")

        if self.tgroup is not None:
            rst_tgroup = self.tgroup.to_rst(indent=indent, links=links, base_url=base_url)
            lines.append(rst_tgroup)

        return "\n".join(lines)

    def __repr__(self):
        # This method is limited as the links and the base_url are skiped.
        return self.to_rst(links={}, base_url=f"pass")


class Refentrytitle(Element):
    """Provides the title of the reference entry."""

    def __repr__(self):
        items = []
        for item in self._content:
            item = str(item)
            for key, value in CONST.items():
                item = item.replace(key, value)
            items.append(item)
        return "".join(items)


class Refnamediv(Element):
    """Provides the refnamediv element, which contains the name,
    purpose, and classification of a reference."""

    def __init__(self, element, terms=None):
        self._element = element
        self._terms = terms
        super().__init__(element)

    @property
    def terms(self):
        """Terms of the element."""
        return self._terms

    @terms.setter
    def terms(self, terms):
        """Set the terms of the element."""
        self._terms = terms

    @property
    def refname(self):
        """Refname of the element."""
        return self.find("Refname", self._terms)

    @property
    def purpose(self):
        "Refpurpose of the element."
        return self.find("Refpurpose")


class Refname(Element):
    """Provides the refname element which contains
    the name of a reference."""

    def __init__(self, element, terms=None):
        self._element = element
        self._terms = terms
        super().__init__(element)

    @property
    def terms(self):
        """Terms of the element."""
        return self._terms

    @terms.setter
    def terms(self, terms):
        """Set the terms of the element."""
        self._terms = terms

    @property
    def raw_args(self):
        """Raws containing the command arguments."""
        cmd = str(self)
        for term in self._terms.keys():
            if type(self._terms[term]) == str:
                cmd = cmd.replace(f"&{term};", self._terms[term])
        cmd = cmd.replace("``", "")
        split_args = cmd.split(",")[1:]
        return split_args

    @property
    def args(self):
        """Command arguments."""
        args = []
        for item in self.raw_args:
            arg = to_py_arg_name(str(item))

            # simply check if we can use this as a valid Python kwarg
            try:
                exec(f"{arg} = 1.0")
            except SyntaxError:
                arg = ""

            if "blank" in arg:
                arg = ""

            args.append(arg)

        # rename duplicate arguments
        if len(args) != len(set(args)):
            for arg in args:
                if arg != "":
                    i = 0
                    if args.count(arg) > 1:
                        for j in range(len(args)):
                            if args[j] == arg:
                                args[j] = f"{arg}{i:d}"
                                i += 1

        return args


class Refpurpose(Element):
    """Provides the refpurpose element, which contains
    a short synopsis of a reference."""

    def __repr__(self):
        return " ".join([str(item) for item in self._content])


class Refclass(Element):

    pass


class Application(Element):

    pass


class Refsect1(Element):

    pass


class Command(Element):
    """Provides the command element."""

    @property
    def command(self):
        """Name of the command."""
        return self[0]

    @property
    def tail_no_args(self):
        """Tail of the element after removing all its arguments."""
        tail = self.tail
        for arg in self.args:
            tail = tail.replace(arg, "")
        return tail

    def __repr__(self):
        return f"{self.command} {self.tail}"

    @property
    def has_args(self):
        """Return whether the element has arguments."""
        # return self.tail.startswith(",")
        return False  # TODO: This is to be modified

    @property
    def args(self):
        """Any terms immediately following the command."""
        if self.has_args:
            words = self.tail.split()
            cmd_args = words[0]

            # Remove trailing non-alphanumeric. These can't be part of the command.
            while cmd_args and not (cmd_args[-1].isalnum() or cmd_args[-1].isdigit()):
                cmd_args = cmd_args[:-1]

            # possible that next element is a replaceable and not part of the tail
            if isinstance(self.next_elem, Replaceable):
                cmd_args += str(self.next_elem[0])  # no tail
            elif len(self.tail) > 1 and self.tail[1] == " ":
                # possible not coded as replaceable
                for word in words[1:]:
                    if word.upper() == word or is_numeric(word):
                        if not (word[-1].isalnum() or word[-1].isdigit()):
                            parm, _ = split_trail_alpha(word)
                        else:
                            parm = word

                        if parm:
                            cmd_args += f",{parm}"
                    else:
                        # break at first failing match
                        break

            return cmd_args.split(",")[1:]
        return [""]

    @property
    def py_args(self):
        """String containing the arguments of the element."""
        args = []
        for arg in self.args:
            if is_numeric(arg):
                args.append(f"{arg}")
            else:
                args.append(f'"{arg}"')
        py_args = ", ".join(args)
        if py_args == '""':
            return ""
        return py_args

    @property
    def py_cmd(self):
        """Pythonic name of the command."""
        return to_py_name(self.command)

    @property
    def sphinx_cmd(self):
        """String to refer to the Python command with Sphinx."""
        if self.py_cmd == self.command:
            ref = f"``{self.py_cmd}``"
        else:
            if self.py_cmd in NAME_MAP_GLOB.values():
                ref = f":ref:`{self.py_cmd}`"
            else:
                ref = f"``{self.py_cmd}``"
        return ref

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        if self.args and self.args[0] != "":
            return f"{self.sphinx_cmd} {self.tail_no_args}"
        else:
            return f"{self.sphinx_cmd} {self.tail}"


class ComputerOutput(Element):
    """Provides the computer output element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        return f"``{self[0]}`` {self[1]}"


class Figure(Element):
    """Provides the figure element."""

    @property
    def title(self):
        """First title element found in the figure element."""
        return self.rec_find("Title")

    @property
    def graphic(self):
        """First graphic element found in the figure element."""
        return self.rec_find("Graphic")

    def to_rst(self, indent="", max_length=100, fcache=None):
        """Return a string to enable converting the element to an RST format."""
        graphic = self.graphic
        if graphic is not None and graphic.entityref is not None:
            lines = []
            lines.append(graphic.to_rst(indent=indent, fcache=fcache))
            if self.title is not None:
                lines.append(f"   {self.title}")

            return "\n" + "\n".join(lines) + "\n"

        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_fcache:
                    items.append(item.to_rst(indent=indent, fcache=fcache))
                else:
                    items.append(item.to_rst(indent))
            else:
                items.append(indent + str(item))
        return "\n" + "".join(items)


class Footnote(Element):

    pass


class Footnoteref(Element):

    pass


class Formalpara(Element):

    pass


class Glossterm(Element):

    pass


class GuiButton(Element):

    pass


class GuiIcon(Element):

    pass


class Highlights(Element):

    pass


class Important(Element):

    pass


class InformalEquation(Element):

    pass


class Interface(Element):

    pass


class Markup(Element):

    pass


class Mediaobject(Element):

    pass


class Option(Element):

    pass


class Refsect3(Element):

    pass


class Refsynopsisdiv(Element):

    pass


class Sidebar(Element):

    pass


class XMLType(Element):

    pass


class XMLWarning(Caution):
    """XML Warning element are handled the same as Caution elements."""

    pass


class ClassName(Element):

    pass


class Imageobject(Element):

    pass


class InformalFigure(Element):

    pass


class Envar(Element):

    pass


class ImageData(Element):

    pass


class ColSpec(Element):

    pass


class TBody(Element):
    """Provides the tbody element."""

    @property
    def rows(self):
        """Return all the row elements found in the TBody element."""
        return self.find_all("Row")

    def to_rst(self, l_head, indent="", links=None, base_url=None):
        """Return a list to enable converting the element to an RST format."""
        rst_rows = []
        for i, row_i in enumerate(self.rows):
            row = row_i.find_all("Entry")
            if len(row[0]) > 0:
                if type(row[0][0]) == Command:
                    command = f"   * - :ref:`{row[0][0].py_cmd}`"
                    rst_rows.append(command)
                    strg = f"     - {row[1][0]}"
                    rst_rows.append(strg)
                    if l_head == 0 and i == 0:
                        l_head = 2
                else:
                    if l_head == 0 and i == 0:
                        row_rst_list = row_i.to_rst_list(links=links, base_url=base_url)
                        l_head = len(row_rst_list)

                    else:
                        row_rst_list = row_i.to_rst_list(links=links, base_url=base_url)
                    row_rst = "\n     - ".join(row_rst_list)
                    rst_rows.append(f"   * - {row_rst}")
            elif len(row[1]) > 0:
                if type(row[1][0]) == Command:
                    command = f"   * - :ref:`{row[1][0].py_cmd}`"
                    rst_rows.append(command)
                    row_content = str(row[2][0])
                    strg = f"     - {row_content}"
                    rst_rows.append(strg)

        return rst_rows


class Entry(Element):
    """Provides the entry element."""

    @property
    def morerows(self):
        """Value for the ``morerows`` parameter contained in the entry element."""
        return self._element.get("morerows")

    def to_rst(self, indent="", links=None, base_url=None, fcache=None):
        """Return a string to enable converting the element to an RST format."""

        if self.morerows is not None:
            content = self.morerows

        items = []
        for item in self:
            if isinstance(item, Element):
                if item.tag in item_needing_links_base_url:
                    entry_item = item.to_rst(indent, links=links, base_url=base_url)
                else:
                    entry_item = item.to_rst(indent)
            else:
                entry_item = str(item)

            items.append(entry_item)

        if self.morerows is not None:
            entry = f":rspan:`{content}` " + " ".join(items)

        else:
            entry = " ".join(items)

        return entry


class Row(Element):
    """Provides the row element."""

    @property
    def entry(self):
        """Return all entry elements found in the row element."""
        return self.find_all("Entry")

    def to_rst_list(self, indent="", links=None, base_url=None):
        """Return a list to enable converting the element to an RST format."""
        row = []
        for entry in self.entry:
            content = entry.to_rst(links=links, base_url=base_url, indent="")
            content = content.replace("\n", "")
            content = content.replace("\r", "")
            row.append(content)
        return row


class THead(Element):
    """Provides the thead element."""

    @property
    def rows(self):
        """Return all row elements found in the THead element."""
        return self.find_all("Row")

    def to_rst(self, indent="", links=None, base_url=None):
        """Return a list and the length of the list for converting the element
        to an RST format."""

        l_rst_list = 0

        if self.rows is not None:
            row = []

            if len(self.rows) > 1:
                row.append(
                    f".. flat-table:: {''.join(self.rows[0].to_rst_list(links=links, base_url=base_url))}"  # noqa : E501
                )
                row.append(f"   :header-rows: {len(self.rows)-1}")
                ini = 1

            elif len(self.rows[0]) == 1:
                row.append(self.rows[0].to_rst_list(links=links, base_url=base_url)[0])
                row.append("")
                row.append(f".. flat-table::")
                ini = len(self.rows)

            else:
                row.append(f".. flat-table::")
                row.append(f"   :header-rows: 1")
                ini = 0

            row.append("")
            for i in range(ini, len(self.rows)):
                rst_list = self.rows[i].to_rst_list(links=links, base_url=base_url)
                l_rst_list = len(rst_list)
                row_rst = "\n     - ".join(rst_list)
                row.append(f"   * - {row_rst}")

            return row, l_rst_list


class Remark(Element):

    pass


class LiteralLayout(Element):

    pass


class CiteTitle(Element):

    pass


class ULink(Element):

    pass


class SegTitle(Element):

    pass


class Chapter(Element):
    """Provides the chapter element."""

    @property
    def helpstring(self):
        """Value for the ``helpstring`` parameter contained in the chapter element."""
        return self[1]._element.get("helpstring")

    def __repr__(self):
        items = [f"Chapter {self.helpstring}\n\n"]
        items.extend([str(item) for item in self._content])
        return "".join(items)


class Section1(Element):

    pass


class ProductName(Element):

    pass


class Argument:
    """Argument object."""

    def __init__(
        self,
        terms,
        element: str | Element,
        initial_arguments: List,
        description: Element | str | None = None,
    ) -> None:
        if description is None:
            if isinstance(element[0], Term):
                name = element[0]
                description = element[1]

            else:
                i = 0
                while not isinstance(element[i], Term) and i < len(element):
                    i += 1
                    name = element[i]
                    description = element[i + 1]

        else:
            name = element
        self._name = name
        self._terms = terms
        self._description = description
        self._initial_arguments = initial_arguments

    @property
    def py_arg_name(self) -> str:
        """Python-compatible term."""
        return to_py_arg_name(self._name)

    @property
    def is_arg_elipsis(self):
        """
        Check if the argument is an elipsis.

        Returns
        -------
        bool
            True if the argument is an elipsis, False otherwise.
        """
        return is_elipsis(str(self._name))

    @property
    def multiple_args(self):
        additional_args = []
        if "," in str(self._name):
            split_name = str(self._name).split(",")
            if not self.is_arg_elipsis:
                for item_name in split_name:
                    arg_name = item_name.strip()
                    new_arg = Argument(
                        self._terms, arg_name, self._initial_arguments, self._description
                    )
                    additional_args.append(new_arg)
            else:

                complete_args = get_complete_args_from_initial_arg(
                    elipsis_args=split_name, initial_args=self._initial_arguments
                )

                if len(complete_args) > 0:
                    for item in complete_args:
                        new_arg = Argument(
                            self._terms, item, self._initial_arguments, self._description
                        )
                        additional_args.append(new_arg)

                else:

                    for i, item_name in enumerate(split_name):
                        item_name = item_name.strip()
                        if item_name == "":
                            new_arg = Argument(
                                self._terms, arg_name, self._initial_arguments, self._description
                            )
                            additional_args.append(new_arg)
                        elif is_elipsis(item_name):

                            if "+" in split_name[i + 1]:
                                number_final_iter, (
                                    initial_pos_final,
                                    end_pos_final,
                                ) = get_quant_iter_pos(split_name[i + 1])
                                if "+" in split_name[i - 1]:
                                    number_prev_iter, (
                                        initial_pos_prev,
                                        end_pos_prev,
                                    ) = get_quant_iter_pos(split_name[i - 1])
                                else:
                                    number_prev_iter = 0

                                for j in range(number_prev_iter + 1, number_final_iter):
                                    arg_name = split_name[i + 1].strip()
                                    arg_name = f"{arg_name[:initial_pos_final]}{j}{arg_name[end_pos_final:]}"  # noqa : E501
                                    new_arg = Argument(
                                        self._terms,
                                        arg_name,
                                        self._initial_arguments,
                                        self._description,
                                    )
                                    if new_arg.py_arg_name != "":
                                        additional_args.append(new_arg)
                            else:
                                k = i
                                while split_name[k - 1].strip() == "" and k - 1 >= 0:
                                    k -= 1
                                if split_name[k - 1].strip() == "":
                                    raise ValueError("The argument name is not consistent.")
                                name_iter_prev, number_iter_prev = get_iter_values(
                                    split_name[k - 1]
                                )
                                name_iter_next, number_iter_next = get_iter_values(
                                    split_name[k + 1]
                                )
                                if name_iter_prev != name_iter_next:
                                    logger.warning(
                                        f"The argument name is not consistent: {name_iter_prev} != {name_iter_next}"  # noqa : E501
                                    )
                                    logger.info(
                                        "Applying the longest name for the argument list as it's probably coming from a typography."  # noqa : E501
                                    )
                                    if len(name_iter_prev) > len(name_iter_next):
                                        name_iter_next = name_iter_prev
                                    else:
                                        name_iter_prev = name_iter_next
                                else:
                                    if number_iter_next > 0:
                                        for j in range(number_iter_prev + 1, number_iter_next):
                                            arg_name = f"{name_iter_prev}{j}"
                                            new_arg = Argument(
                                                self._terms,
                                                arg_name,
                                                self._initial_arguments,
                                                self._description,
                                            )
                                            additional_args.append(new_arg)
                                    else:
                                        additional_args.append(
                                            Argument(
                                                self._terms,
                                                name_iter_next,
                                                self._initial_arguments,
                                                self._description,
                                            )
                                        )

        return additional_args

    @property
    def types(self) -> List[type]:
        """One or more parameter types.

        This is guessed from any subvarlists. If unavailable, then it's guessed
        from the description of the variable.

        This is either a string, float, or integer (or some combination thereof).

        """
        parm_types = [str]
        if isinstance(self._description, Element):
            varlist = self._description.rec_find("Variablelist")

            if varlist is not None:
                terms = varlist.terms
                if terms:
                    terms_numeric = [is_numeric(term) for term in terms]
                    if any(terms_numeric):
                        parm_types = [int, str]
                    else:
                        parm_types = [str]

                    # consider checking for bool
                    # terms_numeric = set(terms) == set(['1', '0'])

        return parm_types

    def resized_description(
        self, description: str | None = None, max_length: int = 100, indent: str = ""
    ) -> List[str]:
        """Resize the description to a maximum length."""
        if description is None:
            description = self._description

        if "* " not in description:
            output = resize_length(
                description, max_length, initial_indent=indent, subsequent_indent=indent, list=True
            )
        else:
            output = textwrap.indent(description, indent)
            output = output.split("\n")

        return output

    def to_py_docstring(self, max_length=100, links=None, base_url=None, fcache=None) -> List[str]:
        """Return a list of string to enable converting the element to an RST format."""
        if self.py_arg_name != "":
            if isinstance(self._description, str):
                rst_description = self._description
            else:
                rst_description = self._description.to_rst(
                    max_length=max_length,
                    links=links,
                    base_url=base_url,
                    fcache=fcache,
                )
            rst_description = replace_terms(rst_description, self._terms)

            description_indent = " " * 4

            if isinstance(self._description, Element):
                intersection_types = set(NO_RESIZE_LIST).intersection(
                    set(self._description.children_types)
                )
                if len(intersection_types) == 0 and "* " not in rst_description:
                    list_description = self.resized_description(
                        rst_description, max_length, description_indent
                    )
                else:
                    rst_description = textwrap.indent(rst_description, description_indent)
                    list_description = rst_description.split("\n")
            elif " * " not in rst_description:
                list_description = self.resized_description(
                    rst_description, max_length, description_indent
                )
            else:
                list_description = rst_description.split("\n")

            docstring = [f'{self.py_arg_name} : {str_types(self.types, " or ")}']
            docstring.extend(list_description)

        else:
            docstring = []

        return docstring


class ArgumentList:
    def __init__(
        self, py_name: str, url: str, terms: dict, list_entry: VarlistEntry, args: List
    ) -> None:

        self._py_name = py_name
        self._url = url
        self._terms = terms
        self._list_entry = list_entry
        self._arguments = []
        self._additional_args = []
        self._initial_args = args
        self._parse_list_entry()

    def _parse_list_entry(self):
        "Parse the list entry to get the main arguments and the additional ones."
        temp_args = {}
        for item in self._list_entry:
            if isinstance(item, VarlistEntry):
                argument_obj = Argument(self._terms, item, self._initial_args)
                additional_args = argument_obj.multiple_args
                if len(additional_args) > 0:
                    for arg in additional_args:
                        arg_name = arg.py_arg_name
                        if (arg_name in self._initial_args) and (
                            arg_name == "" or arg_name not in self.py_arg_names
                        ):
                            temp_args[arg_name] = arg

                else:
                    temp_args[argument_obj.py_arg_name] = argument_obj

        for initial_arg in self._initial_args:
            if initial_arg in temp_args.keys():
                self._arguments.append(temp_args[initial_arg])
            else:
                self._arguments.append(
                    Argument(
                        self._terms,
                        initial_arg,
                        self._initial_args,
                        MISSING_ARGUMENT_DESCRIPTION.replace("url", f"{self._url}"),
                    )
                )  # description is missing

        is_additional_arg = False
        if len(temp_args) != len(self._initial_args):
            for arg in temp_args:
                if arg not in self.py_arg_names:
                    self._additional_args.append(temp_args[arg])
                    is_additional_arg = True

        if is_additional_arg and "addional_command_arg" not in self.py_arg_names:
            self._arguments.append(
                Argument(
                    self._terms,
                    "addional_command_arg",
                    self._initial_args,
                    ADDITIONAL_ARGUMENT_DESCRIPTION.replace("url", f"{self._url}"),
                )
            )

    def __iadd__(self, argument_list):
        temp_args = {}
        for arg in argument_list.arguments:
            arg_name = arg.py_arg_name
            if (arg_name in self._initial_args) and (
                arg_name == "" or arg_name not in self.py_arg_names
            ):
                temp_args[arg_name] = arg

        for initial_arg in self._initial_args:
            if initial_arg in temp_args.keys():
                if initial_arg not in self.py_arg_names:
                    self._arguments.append(temp_args[initial_arg])
                else:
                    self._arguments[self.py_arg_names.index(initial_arg)] = temp_args[initial_arg]
            else:
                if initial_arg not in self.py_arg_names:
                    self._arguments.append(
                        Argument(
                            self._terms,
                            initial_arg,
                            self._initial_args,
                            MISSING_ARGUMENT_DESCRIPTION.replace("url", f"{self._url}"),
                        )
                    )

        is_additional_arg = False
        if len(temp_args) != len(self._initial_args):
            for arg in temp_args:
                if arg not in self.py_arg_names:
                    self._additional_args.append(temp_args[arg])
                    is_additional_arg = True

        if is_additional_arg and "addional_command_arg" not in self.py_arg_names:
            self._arguments.append(
                Argument(
                    self._terms,
                    "addional_command_arg",
                    self._initial_args,
                    ADDITIONAL_ARGUMENT_DESCRIPTION.replace("url", f"{self._url}"),
                )
            )

        return self

    @property
    def arguments(self) -> List[Argument]:
        "Return a list of Argument objects."
        return self._arguments

    @arguments.setter
    def arguments(self, argument):
        self._arguments.append(argument)

    @property
    def py_name(self):
        return self._py_name

    @property
    def initial_args(self):
        return self._initial_args

    @property
    def py_arg_names(self):
        return [arg.py_arg_name for arg in self._arguments]

    @property
    def additional_args(self):
        return self._additional_args

    def remove_last_arg(self):
        self._arguments.pop()


class XMLCommand(Element):
    """Provides the XML command from the documentation."""

    def __init__(
        self,
        filename,
        refentry,
        terms,
        docu_global,
        version_variables,
        links,
        fcache,
        meta_only=False,
    ):
        """Parse command from XML file."""
        self._xml_filename = filename
        self._terms = terms
        self._docu_global = docu_global
        self._autogenerated_directory_name = version_variables.autogenerated_directory_name
        self._links = links
        self._base_url = version_variables.base_url
        self._fcache = fcache
        self._group = None
        self._is_archived = False
        self._refentry = refentry
        self._max_length = 100

        # parse the command
        super().__init__(self._refentry, parse_children=not meta_only)

    @property
    def xml_filename(self):
        """Source filename of the command."""
        return self._xml_filename

    @property
    def args(self):
        """Command arguments."""
        return self._refname_div.refname.args

    @property
    def default(self):
        """Command default."""
        if self._refsynopsis:
            for item in self._refsynopsis:
                if str(item.title).strip() == "Command Default":
                    return item

    @property
    def arg_desc(self) -> List[Argument]:
        """Argument object list of the command."""
        refsyn = self.rec_find("Refsynopsisdiv")
        # search by ID
        arguments = None
        if refsyn is None:
            refsections = self.find_all("RefSection")
            for elem in refsections:
                for child in elem:
                    if isinstance(child, Variablelist):
                        if arguments is None:
                            arguments = ArgumentList(
                                self.py_name, self.url, self._terms, child, self.args
                            )
                        else:
                            arguments += ArgumentList(
                                self.py_name, self.url, self._terms, child, self.args
                            )

        else:
            for elem in refsyn:
                if isinstance(elem, Variablelist):
                    if arguments is None:
                        arguments = ArgumentList(
                            self.py_name, self.url, self._terms, elem, self.args
                        )
                    else:
                        arguments += ArgumentList(
                            self.py_name, self.url, self._terms, elem, self.args
                        )

        arg_file = Path("args.txt")

        if arguments is not None:
            # Remove last argument if it's empty
            while arguments.py_arg_names[-1] == "":
                arguments.remove_last_arg()

            if len(arguments.py_arg_names) != len(arguments.initial_args):
                # This function needs a special treatment
                if arg_file.exists():
                    with open(arg_file, "r") as f:
                        for line in f:
                            pass
                        last_line = line
                else:
                    last_line = ""
                with open(arg_file, "a") as f:
                    if last_line != f"py_arg_name : {arguments.py_arg_names}\n":
                        f.write("--------------------------------------------------\n")
                        f.write(f"{self.py_name}: {self.group}\n")
                        f.write("initial_args : ")
                        f.write(f"{arguments.initial_args}\n")
                        f.write("py_arg_name : ")
                        f.write(f"{arguments.py_arg_names}\n")

            return arguments.arguments

        else:
            return []

    @property
    def short_desc(self):
        """Short description of the command."""
        short_desc = ""
        if self._refname_div is not None:
            short_desc = self._refname_div.purpose.to_rst(
                links=self._links, base_url=self._base_url
            )
            short_desc = resize_length(short_desc, self._max_length)
        return short_desc

    @property
    def _metadata(self):
        if self.rec_find("RefMeta") is None:
            for item in self._refentry.getchildren():
                if item.tag == "refmeta":
                    return parse_element(item)
        return self.rec_find("RefMeta")

    @property
    def name(self):
        """Name of the XML command."""
        return self._metadata.refentry_title

    @property
    def py_name(self):
        """Python-compatible name."""
        return to_py_name(self.name)

    @property
    def py_args(self):
        return [arg.lower() for arg in self.args]

    @property
    def is_archived(self):
        """Flag indicating if the command is archived."""
        return self._is_archived

    @is_archived.setter
    def is_archived(self, is_archived):
        """Set whether the command is archived."""
        self._is_archived = is_archived

    @property
    def group(self):
        """Group of the command."""
        return self._group

    @group.setter
    def group(self, group):
        """Set the group of the command."""
        self._group = group

    def py_signature(self, custom_functions: CustomFunctions, indent="") -> str:
        """Beginning of the Python command's definition."""
        args = ["self"]
        arg_desc = self.arg_desc
        if custom_functions is not None and (
            self.py_name in custom_functions.py_names and self.py_name in custom_functions.py_args
        ):
            for argument in custom_functions.py_args[self.py_name]:
                new_arg = to_py_signature(
                    argument, [str]
                )  # checks are not done for custom functions
                if new_arg is not None:
                    args.append(new_arg)
        else:
            if len(arg_desc) > 0:
                for argument in arg_desc:
                    new_arg = to_py_signature(argument.py_arg_name, argument.types)
                    if new_arg is not None:
                        args.append(new_arg)

        arg_sig = ", ".join(args)
        return f"{indent}def {self.py_name}({arg_sig}, **kwargs):"

    def py_docstring(self, custom_functions: CustomFunctions, warning_command_dict: None) -> str:
        """
        Python docstring of the command.

        Parameters
        ----------

        custom_functions : CustomFunctions
            Custom functions object.

        warning_command_dict: dict, optional
            Dictionary of commands associated to a list of warnings.
            The default is ``None``.


        """
        xml_cmd = f"{self._terms['pn006p']} Command: `{self.name} <{self.url}>`_"

        items = [self.short_desc, "", xml_cmd]

        if self.name in warning_command_dict.keys():
            warnings_ = warning_command_dict[self.name]
            for warning_ in warnings_:
                warning_ = textwrap.indent(warning_, " " * 4)
                items.extend([f"\n.. warning::\n\n{warning_}\n"])

        if self.default is not None:
            if self.default.tag in item_needing_links_base_url:
                items += [""] + textwrap.wrap(
                    "Default: " + self.default.to_rst(links=self._links, base_url=self._base_url)
                )
            else:
                items += [""] + textwrap.wrap("Default: " + self.default.to_rst())
        if self.args is not None:
            items += [""] + self.py_parm(
                custom_functions, links=self._links, base_url=self._base_url, fcache=self._fcache
            )
        if custom_functions is not None and (
            self.py_name in custom_functions.py_names
            and self.py_name in custom_functions.py_returns
        ):
            items += [""] + custom_functions.py_returns[self.py_name]
        if self.notes is not None:
            items += [""]
            items.extend(self.py_notes(custom_functions))
        if custom_functions is not None and (
            self.py_name in custom_functions.py_names
            and self.py_name in custom_functions.py_examples
        ):
            items += [""] + custom_functions.py_examples[self.py_name]
        docstr = "\n".join(items)

        for key, value in CONST.items():
            docstr = docstr.replace(key, value)
        for key, value in CLEANUP.items():
            docstr = docstr.replace(key, value)

        # delete trailing whitespace for each line
        docstr = "\n".join(line.rstrip() for line in docstr.splitlines())

        # sub XML command args
        def arg_replacer(match):
            text = match.group().replace("`", "")
            func = re.findall(r"<CMD>(.*)</CMD>", text)[0]
            arg_str = text.split("</CMD>")[1].strip()[1:]
            if arg_str.endswith(","):
                arg_str = arg_str[:-1]
            if arg_str.startswith(","):
                arg_str = arg_str[1:]

            split_args = [arg.strip() for arg in arg_str.split(",")]

            tail = ""
            py_args = []
            if split_args[-1] == "or":
                # these are options and not args. Use the first and ignore the rest
                tail = text.split(split_args[0])[-1]
                split_args = [split_args[0]]

                for arg in split_args:
                    if is_numeric(arg):
                        py_args.append(f"{arg}")
                    else:
                        py_args.append(f'"{arg}"')
            py_args = ", ".join(py_args)

            return f":func:`{func}({py_args}) <{self._autogenerated_directory_name}.{func}>` {tail}"

        def cmd_replacer(match):
            func = match.group().replace("<CMD>", "").replace("</CMD>", "")
            return f":func:`{func}() <{self._autogenerated_directory_name}.{func}>`"

        # command replacement without args
        docstr = re.sub(r"<CMD>[a-z0-9]*</CMD>", cmd_replacer, docstr)

        def pipe_replacer(match):
            return match.group().replace("|", r"\|")

        docstr = re.sub(r"\|(.*)\|", pipe_replacer, docstr)

        def trail_replacer(match):
            return match.group().replace("_", "")

        docstr = re.sub(r"([^_|^`][A-Za-z0-9]*)_\s[^:]", trail_replacer, docstr)

        # final line by line cleanup
        lines = []
        for line in docstr.splitlines():
            if "cannot be accessed from a menu" in line:
                continue
            if "Graphical picking is available only" in line:
                continue
            lines.append(line)

        # ensure that lists begin with list-table
        i = 2
        while i < len(lines):
            header = lines[i - 2].lstrip().startswith(":header-rows:") or lines[
                i - 2
            ].lstrip().startswith(".. flat-table")
            corp = lines[i - 1].lstrip().startswith("* -") or lines[i - 1].lstrip().startswith("-")
            if (lines[i].lstrip().startswith("* -")) and not (corp or header):
                lines.insert(i, ".. flat-table ::")
                lines.insert(i + 1, "")
            i += 1

        # ensure that two similar links are not in a similar file.
        i = 0
        link = []
        flat_table = False
        while i < len(lines):
            n_quotes = lines[i].count("`")
            if ".. flat-table::" in lines[i]:
                flat_table = True
            if flat_table is True:
                if n_quotes > 0:
                    j = 0
                    quote = 0
                    begin = False
                    while quote < n_quotes and j < len(lines[i]):
                        if lines[i][j] == "`":
                            if begin == False:
                                begin = True
                                link_i = []
                                quote += 1
                            else:
                                link.append(link_i)
                                begin = False
                                quote += 1
                        else:
                            if begin == True:
                                link_i.append(lines[i][j])
                        j += 1
            i += 1

        link_list = []
        for l in link:
            if "<" in "".join(l):
                link_list.append("".join(l))

        if len(link_list) > 1:
            diff_links = set(link_list)
            if len(diff_links) != len(link_list):
                for l in diff_links:
                    name_link = l[: l.index("<") - 1]
                    nb_l = link_list.count(l)
                    if nb_l > 1:
                        first = 0
                        flat_table = False
                        for i in range(len(lines)):
                            if ".. flat-table::" in lines[i]:
                                flat_table = True
                            if flat_table is True:
                                if lines[i].count(l) > 0:
                                    if first == 0:
                                        first = 1
                                    else:
                                        lines[i] = lines[i].replace(l, name_link)

        docstr = "\n".join(lines)

        # remove repeated line breaks
        while "\n\n\n" in docstr:
            docstr = docstr.replace("\n\n\n", "\n\n")

        lines = docstr.splitlines()

        # ensure that lists end with a blank line
        i = 0
        while i < len(lines):
            j = 1
            if lines[i].lstrip().startswith("* -"):
                while i + j < len(lines) - 1 and lines[i + j].lstrip().startswith("-"):
                    j += 1
                if not lines[i + j].lstrip().startswith("* -"):
                    if i + j == len(lines) - 1:
                        j += 1
                    lines.insert(i + j, "")
            i += j
        docstr = "\n".join(lines)

        docstr = re.sub(r"bgcolor=\S\S\S\S\S\S\S\S\S\S? ", "", docstr)
        docstr = re.sub(r"bgcolor=\S\S\S\S\S\S\S\S\S\S?", "", docstr)
        docstr = re.sub(r"_cellfont Shading=\S\S\S\S\S\S\S\S", "", docstr)
        docstr = re.sub(r"Caret.*\?", "", docstr)
        docstr = docstr.replace("–", "-")
        docstr = docstr.replace(". . .", "...")
        docstr = replace_asterisks(docstr)
        docstr = ponctuaction_whitespace(docstr, ".")  # Remove extra whitespace before period
        docstr = ponctuaction_whitespace(docstr, ",")  # Remove extra whitespace before comma

        if self.is_archived == True:
            logger.info(f"{self.name} is an archived command.")
            docstr = (
                docstr
                + "\n\n.. warning::\n\n"
                + "    This command is archived in the latest version of the software.\n"
            )

        # Final cleanup
        docstr = replace_terms(docstr, self._terms)
        return docstr

    def py_notes(self, custom_functions: CustomFunctions = None):
        """Python-formatted notes string."""
        lines = ["Notes", "-" * 5]
        if self.notes.tag in item_needing_all:
            notes = self.notes.to_rst(
                max_length=self._max_length,
                links=self._links,
                base_url=self._base_url,
                fcache=self._fcache,
            )
        elif self.notes.tag in item_needing_links_base_url:
            notes = self.notes.to_rst(
                max_length=self._max_length, links=self._links, base_url=self._base_url
            )
        elif self.notes.tag in item_needing_fcache:
            notes = self.notes.to_rst(
                max_length=self._max_length, links=self._links, fcache=self._fcache
            )
        else:
            notes = self.notes.to_rst()

        notes = replace_terms(notes, self._terms)
        to_be_resized = re.findall(r"^[^\.\s].+(?=\n)|(?<=\n)[^\.\s].+(?=\n)", notes)

        for item in to_be_resized:
            resized_item = resize_length(item, self._max_length)
            notes = notes.replace(item, resized_item)
        lines.extend(notes.split("\n"))

        if custom_functions is not None and (
            self.py_name in custom_functions.py_names and self.py_name in custom_functions.py_notes
        ):
            if len("\n".join(lines)) < len("\n".join(custom_functions.py_notes[self.py_name])):
                lines = custom_functions.py_notes[self.py_name]

        return lines

    @property
    def url(self):
        """URL to the Ansys command documentation."""
        cmd_base_url = f"{self._base_url}/ans_cmd/"
        return f"{cmd_base_url}{self.filename}"

    @property
    def filename(self):
        """Command filename"""
        return self[0]._element.get("filename")

    @property
    def _refname_div(self):
        return self.rec_find("Refnamediv", self._terms)

    @property
    def _refsynopsis(self):
        return self.find("Refsynopsisdiv")

    @property
    def notes(self):
        """Notes of the command."""
        for item in self:
            if str(item.title).strip() == "Notes":
                return item

    def __repr__(self):
        lines = [f"Original command: {self.name}"]
        lines.append("")
        lines.append("Short Description:")
        lines.append(f"{self.short_desc}")
        lines.append("")
        lines.append("Function signature:")
        lines.append(", ".join([f"{self.name}"] + self.args))
        lines.append("")
        lines.append(str(self.arg_desc))  # TO DO: modify this
        lines.append("")
        lines.append(str(self.notes))

        return "\n".join(lines)

    def py_parm(self, custom_functions=None, links=None, base_url=None, fcache=None):
        """Python parameter's string."""
        lines = []
        arg_desc = self.arg_desc

        if len(arg_desc) > 0:
            lines.append("Parameters")

        if custom_functions is not None and (
            self.py_name in custom_functions.py_names and self.py_name in custom_functions.py_args
        ):
            initial_py_arg_list = [argument.py_arg_name for argument in arg_desc]
            if set(custom_functions.py_args[self.py_name]) == set(initial_py_arg_list):
                if len(arg_desc) > 0:
                    lines.append("-" * 10)
                    for argument in arg_desc:
                        lines.extend(
                            argument.to_py_docstring(
                                self._max_length, links=links, base_url=base_url, fcache=fcache
                            )
                        )
                        lines.append("")
            else:
                lines.extend(custom_functions.py_params[self.py_name])

        elif len(arg_desc) > 0:
            lines.append("-" * 10)
            for argument in arg_desc:
                lines.extend(
                    argument.to_py_docstring(
                        self._max_length, links=links, base_url=base_url, fcache=fcache
                    )
                )
                lines.append("")
        return lines

    def py_source(self, custom_functions=None, indent=""):
        """
        Return the Python source.

        Parameters
        ----------
        custom_functions: CustomFunctions, optional
            Custom functions to add to the command. The default is ``None``.
        """
        if custom_functions is None or self.py_name not in custom_functions.py_names:

            if len(self.arg_desc) > 0:
                command = 'command = f"' + self.name
                for arg in self.arg_desc:
                    name = arg.py_arg_name
                    if name == "":
                        command += ","
                    else:
                        command += ",{"
                        command += arg.py_arg_name
                        command += "}"
                command += '"\n'
            else:
                command = f'command = "{self.name}"\n'
            return_command = "return self.run(command, **kwargs)\n"
            source = textwrap.indent("".join([command, return_command]), prefix=" " * 4 + indent)

        else:
            source = textwrap.indent("".join(custom_functions.py_code[self.py_name]), prefix=indent)
        return source

    def to_python(self, custom_functions=None, warning_command_dict=None, indent=""):
        """
        Return the complete Python definition of the command.

        Parameters
        ----------
        custom_functions: CustomFunctions, optional
            Custom functions to add to the command.
            The default is ``None``.

        warning_command_dict: dict, optional
            Dictionary of commands associated to a list of warnings.
            The default is ``None``.

        indent: str, optional
            Indentation of the Python function. The default is ``""``.

        Returns
        -------
        str
            Python function of the command including the converted docstring.
        """

        docstr = textwrap.indent(
            f'r"""{self.py_docstring(custom_functions, warning_command_dict)}\n"""',
            prefix=indent + " " * 4,
        )
        if custom_functions is not None and self.py_name in custom_functions.lib_import:
            imports = "\n".join(custom_functions.lib_import[self.py_name])
            out = f"""
{imports}
{self.py_signature(custom_functions, indent)}
{docstr}
{self.py_source(custom_functions, indent)}
"""
        else:
            out = f"""
{self.py_signature(custom_functions, indent)}
{docstr}
{self.py_source(custom_functions, indent)}
"""
        return out


class InformalTable(Element):
    """Provides the informal table element."""

    def to_rst(self, indent="", max_length=100):
        """Return a string to enable converting the element to an RST format."""
        return "InformalTables need to be added."


parsers = {
    "sect1": Section1,
    "chapter": Chapter,
    "productname": ProductName,
    "ulink": ULink,
    "segtitle": SegTitle,
    "citetitle": CiteTitle,
    "literallayout": LiteralLayout,
    "remark": Remark,
    "tbody": TBody,
    "entry": Entry,
    "row": Row,
    "thead": THead,
    "colspec": ColSpec,
    "tgroup": TGroup,
    "envar": Envar,
    "term": Term,
    "varlistentry": VarlistEntry,
    "imagedata": ImageData,
    "imageobject": Imageobject,
    "informalfigure": InformalFigure,
    "classname": ClassName,
    "computeroutput": ComputerOutput,
    "figure": Figure,
    "footnote": Footnote,
    "footnoteref": Footnoteref,
    "formalpara": Formalpara,
    "glossterm": Glossterm,
    "guibutton": GuiButton,
    "guiicon": GuiIcon,
    "highlights": Highlights,
    "important": Important,
    "informalequation": InformalEquation,
    "interface": Interface,
    "markup": Markup,
    "mediaobject": Mediaobject,
    "option": Option,
    "refsect3": RefSection,
    "refsynopsisdiv": Refsynopsisdiv,
    "sidebar": Sidebar,
    "type": XMLType,
    "warning": XMLWarning,
    "refsect1": RefSection,
    "application": Application,
    "refclass": Refclass,
    "refpurpose": Refpurpose,
    "refname": Refname,
    "refnamediv": Refnamediv,
    "refentrytitle": Refentrytitle,
    "primary": Primary,
    "indexterm": IndexTerm,
    "refmeta": RefMeta,
    "function": Function,
    "refsect2": RefSection,
    "informalexample": InformalExample,
    "graphic": Graphic,
    "caution": Caution,
    "literal": Literal,
    "userinput": UserInput,
    "screen": Screen,
    "xref": XRef,
    "subscript": SubScript,
    "inlinegraphic": InlineGraphic,
    "math": Math,
    "inlineequation": InlineEquation,
    "member": Member,
    "simplelist": SimpleList,
    "link": Link,
    "quote": Quote,
    "guimenuitem": GuiMenuItem,
    "itemizedlist": ItemizedList,
    "listitem": ListItem,
    "olink": OLink,
    "replaceable": Replaceable,
    "emphasis": Emphasis,
    "example": Example,
    "command": Command,
    "title": Title,
    "ttl": Title,
    "para": Paragraph,
    "table": Table,
    "orderedlist": OrderedList,
    "variablelist": Variablelist,
    "bridgehead": parse_text,
    "informaltable": InformalTable,
    "blockquote": BlockQuote,
    "note": Note,
    "programlisting": ProgramListing,
    "guimenu": GuiMenu,
    "phrase": Phrase,
    "structname": Structname,
    "filename": FileName,
    "superscript": SuperScript,
    "guilabel": GuiLabel,
    "code": Code,
}

item_needing_links_base_url = {
    "table": Table,
    "simplelist": SimpleList,
    "variablelist": Variablelist,
    "varlistentry": VarlistEntry,
    "refsect2": RefSection,
    "refsect3": RefSection,
    "link": Link,
    "itemizedlist": ItemizedList,
    "olink": OLink,
    "phrase": Phrase,
    "listitem": ListItem,
    "emphasis": Emphasis,
    "formalpara": Formalpara,
    "orderedlist": OrderedList,
    "note": Note,
    "sidebar": Sidebar,
    "title": Title,
    "blockquote": BlockQuote,
    "term": Term,
    "para": Paragraph,
    "refsect1": RefSection,
    "member": Member,
    "highlights": Highlights,
    "important": Important,
    "footnote": Footnote,
}

item_needing_fcache = {
    "graphic": Graphic,
    "figure": Figure,
    "term": Term,
    "para": Paragraph,
    "refsect1": RefSection,
    "refsect2": RefSection,
    "refsect3": RefSection,
    "simplelist": SimpleList,
    "itemizedlist": ItemizedList,
    "listitem": ListItem,
    "informalfigure": InformalFigure,
    "variablelist": Variablelist,
    "blockquote": BlockQuote,
    "informalequation": InformalEquation,
}

item_needing_all = {
    "itemizedlist": ItemizedList,
    "variablelist": Variablelist,
    "simplelist": SimpleList,
    "term": Term,
    "para": Paragraph,
    "refsect1": RefSection,
    "refsect2": RefSection,
    "refsect3": RefSection,
    "listitem": ListItem,
    "varlistentry": VarlistEntry,
    "blockquote": BlockQuote,
}


def get_parser():
    return parsers


class OxygenXmlTree(Element):
    """Provides for loading an XML file as an AST (abstract syntax tree)."""

    def __init__(self, filename, meta_only=False):
        """Parse command from XML file."""
        self._xml_filename = filename
        root = fromstring(open(filename, "rb").read())

        # parse the file
        super().__init__(root, parse_children=not meta_only)

    @property
    def xml_filename(self):
        """Source filename of the command."""
        return self._xml_filename
