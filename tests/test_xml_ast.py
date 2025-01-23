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

from lxml.html import fromstring
import pyconverter.xml2py.ast_tree as ast
import pytest


@pytest.mark.parametrize(
    "initial_name,expected_output",
    [("/PREP7", "prep7"), ("*DMAT", "dmat"), ("SORT", "sort"), ("*VPLOT", "starvplot")],
)
def test_py_name(initial_name, expected_output, name_map):
    assert ast.to_py_name(initial_name, name_map) == expected_output


@pytest.fixture
def alpha_text():
    return "This is a test."


def test_trail_alpha(alpha_text):
    split_alpha = ast.split_trail_alpha(alpha_text)
    assert split_alpha == ("This ", "is a test.")


@pytest.mark.parametrize(
    "numeric_string,expected_output", [("2804", True), ("28.04", True), ("TEA", False)]
)
def test_is_numeric(numeric_string, expected_output):
    assert ast.is_numeric(numeric_string) == expected_output


@pytest.fixture
def str_element():
    return "<element extra_value='0000'>element test</element>"


@pytest.fixture
def element(str_element):
    element = fromstring(str_element)
    return element


def test_init_element(element):
    elem = ast.Element(element)
    assert elem._element == element
    assert elem._content == ["element test"]


def test_parse_element(element):
    element_parser = ast.parse_element(element)
    ast_element = ast.Element(element)
    assert len(element_parser) == len(ast_element)
    assert type(element_parser) == type(ast_element)
    assert element_parser._element == ast_element._element
    assert element_parser._content == ast_element._content


@pytest.fixture
def str_element_with_children():
    return '<element extra_value="0000">element test with children <child>child 1</child> <child>child 2</child> <child>child 3</child></element>'  # noqa : E501


@pytest.fixture
def element_with_children(str_element_with_children):
    return fromstring(str_element_with_children)


@pytest.fixture
def Element_with_children(element_with_children):
    return ast.Element(element_with_children)


def test_parse_children(element_with_children):
    children_fromparse = ast.parse_children(element_with_children)
    children_fromget = element_with_children.getchildren()
    assert children_fromparse == children_fromget


def test_init_element_with_children(element_with_children, Element_with_children):
    assert Element_with_children._element == element_with_children
    assert len(Element_with_children._content) == 4


def test_element_text_content(Element_with_children):
    content = Element_with_children.text_content
    assert content == "element test with children child 1 child 2 child 3"


def test_element_raw(str_element_with_children, Element_with_children):
    raw = Element_with_children.raw
    assert raw == str_element_with_children
