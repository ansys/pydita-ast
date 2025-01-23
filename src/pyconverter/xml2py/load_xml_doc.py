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

from pathlib import Path
import re
from typing import Tuple
import unicodedata

from lxml.etree import ParserError
from lxml.html import fromstring
import pyconverter.xml2py.ast_tree as ast
import pyconverter.xml2py.version_variables as var
from tqdm import tqdm


def link_replacer(file, terms, docu_global, links, base_url, fcache):
    with open(file, "r") as fid:
        text = fid.read()
        matches = re.findall(r"ENTITY([\S\s]*?)(?=\n)", text)
        for match in matches:
            item = ast.Element(fromstring(match)).to_rst(
                links=links, base_url=base_url, fcache=fcache
            )
            key = item.split()[0]
            text = (item.replace(key, "")).strip()
            if not text.startswith("'"):
                continue

            text = text[1:-2].strip()

            def term_replacer(match):
                term = match.group()[1:-1]
                if term in docu_global:
                    _, key, cite_title = docu_global[term]
                    if key in links:
                        root_name, root_title, href, text = links[key]
                        link = f"{base_url}{root_name}/{href}"
                        link_text = terms.get(cite_title, root_title)
                        return f"`{link_text} <{link}>`_"
                else:
                    if term not in terms:
                        return match.group()
                    return terms[term]

            text = re.sub(r"&[\S]*;", term_replacer, text)

            if key not in terms:
                terms[key] = text

    return terms


def load_links(link_path: Path) -> dict:
    """Load all links.

    Parameters
    ----------
    link_path: Path
        Path to the links directory.

    Returns
    -------
    dict
        Dictionary containing the link names and the needed information to render the links.
    """

    linkmap_fnames = list(link_path.glob("*.db"))
    links = {}

    for filename in tqdm(linkmap_fnames, desc="Loading links"):
        try:
            linkmap = ast.Element(fromstring(open(filename, "rb").read()))
        except ParserError:
            continue

        # toplevel
        root_name = Path(filename).with_suffix("").name
        root_title = str(linkmap[0])

        def grab_links(linkmap):
            for item in linkmap:
                if not isinstance(item, ast.Element):
                    continue

                if item.has_children():
                    grab_links(item)

                href = item.get("href")
                targetptr = linkmap.get("targetptr")
                if targetptr is not None and href is not None:
                    text = ""
                    if linkmap[0].tag == "ttl":
                        text = str(linkmap[0]).strip()
                    links[f"{targetptr}"] = (root_name, root_title, href, text)

        grab_links(linkmap)

    return links


def load_fcache(graph_path: Path) -> dict:
    """Load all graphics and cache the base name without the extension.

    Parameters
    ----------
    graph_path: Path
        Path object of the graphic directory.

    Returns
    -------
    dict
        Dictionary containing the base names of the graphics and their path.
    """

    fcache = {}
    for filename in list(graph_path.glob("*")):
        basename = Path(filename).with_suffix("").name
        if not filename.is_file():
            raise FileNotFoundError(f"Unable to locate {basename}")
        fcache[basename] = filename.name

    return fcache


def load_docu_global(term_path: Path) -> dict:
    """Load all global documents.

    Parameters
    ----------
    term_path: Path
        Path object of the terms directory.

    Returns
    -------
    dict
        Dictionary containing the entity names from the documentation and their path.
    """

    docu_ent = term_path / "glb" / "docu_global.ent"

    docu_global = {}
    with open(docu_ent, "r") as fid:
        lines = fid.read().splitlines()

        # have to write our own interperter here since this is non-standard lxml
        for line in lines:
            entity_names = re.findall(r"!ENTITY (\S*) ", line)
            if len(entity_names):
                entity_name = entity_names[0]

                targetdocs = re.findall(r'targetdoc="(\S*)"', line)
                targetdoc = targetdocs[0] if len(targetdocs) else None

                targetptrs = re.findall(r'targetptr="(\S*)"', line)
                targetptr = targetptrs[0] if len(targetptrs) else None

                citetitles = re.findall(r"<citetitle>&(\S*);<\/citetitle>", line)
                citetitle = citetitles[0] if len(citetitles) else None

                docu_global[entity_name] = (targetdoc, targetptr, citetitle)

    return docu_global


def load_terms(
    term_path: Path,
    docu_global: dict,
    links: dict,
    fcache: dict,
    variable_file: str = "build_variables.ent",
    global_terms_file: str = "terms_global.ent",
    manual_file: str = "manuals.ent",
    group_code_file: str = "../xml/ansys.groupcodes.commands.ent",
    character_directory: str = "ent",
) -> Tuple[dict, var.Autogenerateddirectory]:

    """Load all needed terms.

    Parameters
    ----------
    term_path: Path
        Path object of the terms directory.
    docu_global: dict
        Dictionary containing the entity names from the documentation and their path.
    links: dict
        Dictionary containing the link names and the needed information to render the links.
    fcache: dict
        Dictionary containing the base names of the graphics and their path.
    variable_file: str, optional
        Name of the file containing the variable terms to import.
        The default value is ``"build_variables.ent"``.
    global_terms_file: str, optional
        Name of the file containing the global terms to import.
        The default is ``"terms_global.ent"``.
    manual_file: str, optional
        Name of the file containing the manual entities to import.
        The default is ``"manuals.ent"``.
    character_directory: str, optional
        Name of the directory containg the entities for the special characters.
        The default is ``"ent"``.

    Returns
    -------
    dict
        Dictionary containing the entity names and their values.
    Autogenerateddirectory
        Object containing the version variables of the XML documentation.
    """

    terms = {}

    variable_path = term_path / "glb" / variable_file
    if variable_path.is_file():
        with open(variable_path, "r") as fid:
            lines = fid.read().splitlines()

        # have to write our own interperter here since this is non-standard lxml
        for line in lines:
            entity_names = re.findall(r"!ENTITY (\S*) ", line)
            if len(entity_names):
                matches = re.findall(r"'(\S*)'", line)
                if len(matches):
                    terms[entity_names[0]] = matches[0]

    else:
        print("WARNING: No file found for defining variable terms.")
        # This is done manually. To be improved.
        terms["ansys_internal_version"] = "23.2"

    version_variables = var.Autogenerateddirectory(terms)
    base_url = version_variables.base_url

    global_terms_path = term_path / "glb" / global_terms_file
    if global_terms_path.is_file():
        with open(global_terms_path, "r") as fid:
            lines = fid.read().splitlines()

            for line in lines:
                entity_names = re.findall(r"!ENTITY (\S*) ", line)
                if len(entity_names):
                    entity_name = entity_names[0]

                    text = re.findall(r"'(.*)'", line)
                    if len(text):
                        terms[entity_name] = text[0]
    else:
        print("WARNING: No file found for defining global terms.")

    # TODO: use another file for this.
    # Manually adding terms value from warnings.
    terms["sgr"] = r":math:`\sigma`"
    terms["gt"] = r":math:`\sigma`"
    terms["thgr"] = ":math:`<`"
    terms["phgr"] = ":math:`<`"
    terms["ngr"] = r":math:`\phi`"
    terms["agr"] = r":math:`\alpha`"
    terms["OHgr"] = r":math:`\Omega`"
    terms["phis"] = r":math:`\phi`"
    terms["thetas"] = r":math:`\theta`"

    # These are supposed to be uploaded automatically from the `character.ent` file
    terms["#13"] = "#13"
    terms["#160"] = "nbsp"
    terms["#215"] = "times"
    terms["#934"] = r":math:`\Phi`"

    # load manuals
    manual_path = term_path / "glb" / manual_file
    if manual_path.is_file():
        terms = link_replacer(manual_path, terms, docu_global, links, base_url, fcache)
    else:
        print("WARNING: No file found for defining terms.")

    # load docu_global
    docu_ent = term_path / "glb" / "docu_global.ent"
    if docu_ent.is_file():
        terms = link_replacer(docu_ent, terms, docu_global, links, base_url, fcache)
    else:
        print("WARNING: No file found for defining terms.")

    # load special characters
    ent_dir = term_path / character_directory
    if ent_dir.is_dir():
        isoams_dat = list(ent_dir.glob("*.ent"))
        for filename in isoams_dat:
            with open(filename, "r") as fid:
                lines = fid.read().splitlines()
                # have to write our own interperter here since this is non-standard lxml
                for line in lines:
                    entity_names = re.findall(r"!ENTITY (\S*) ", line)
                    if len(entity_names):
                        matches = re.findall(r"<!--(.*)-->", line)
                        if len(matches):
                            char_name = matches[0].strip()
                            try:
                                terms[entity_names[0]] = unicodedata.lookup(char_name)
                            except KeyError:
                                continue

    # load group code
    group_code_terms_path = term_path / group_code_file
    if group_code_terms_path.is_file():
        with open(group_code_terms_path, "r") as fid:
            lines = fid.read().splitlines()

        for line in lines:
            entity_names = re.findall(r"!ENTITY (\S*) ", line)
            if len(entity_names):
                entity_name = entity_names[0]
                classname = re.findall(r"(?<=<classname>)(.*?)(?=<\/classname>)", line)[0]
                typename = re.findall(r"(?<=<type>)(.*?)(?=<\/type>)", line)[0]
                terms[entity_name] = [classname, typename]

    else:
        print("WARNING: No entitiy directory.")

    # This is not working for now
    # TODO

    # filename = doc_path / "DITA-Open-Toolkit/lib/xerces-2_11_0.AnsysCustom/docs/dtd/" / "characters.ent"  # noqa : E501
    # with open(filename, "r") as fid:
    #     lines = fid.read().splitlines()
    #     # have to write our own interperter here since this is non-standard lxml
    #     for line in lines:
    #         entity_names = re.findall(r"!ENTITY (\S*)", line)
    #         if len(entity_names):
    #             matches = re.findall(r"#\d\d\d", line)
    #             if len(matches):
    #                 char_name = matches[0]
    #                 try:
    #                     terms[entity_names[0]] = char_name
    #                 except KeyError:
    #                     continue

    return terms, version_variables
