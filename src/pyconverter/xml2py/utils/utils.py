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
from typing import Tuple, Union

from lxml.html import fromstring
import yaml

logger = logging.getLogger("py_asciimath.utils")
logger.setLevel(logging.INFO)


def parse_yaml(yaml_path: Path) -> dict:
    """
    Parse a YAML file.

    Parameters
    ----------
    yaml_path: Path
        Path object of the YAML file.

    Returns
    -------
    dict
        Dictionary with the content of the YAML file.
    """
    if yaml_path.is_file():
        with open(yaml_path, "r") as file:
            data = yaml.safe_load(file)
        return data
    else:
        raise FileNotFoundError(f"File {yaml_path} not found.")


def get_config_data_value(yaml_path: Path, value: str) -> Union[str, dict, list, None]:
    """
    Return the value of a specific key in the YAML file.

    Parameters
    ----------
    yaml_path: Path
        Path object of the YAML file.
    value: str
        Key to search for in the YAML file.
    """
    config_data = parse_yaml(yaml_path)
    return config_data.get(value)


def get_warning_command_dict(yaml_path: Path) -> dict:
    """
    Get the list of commands that will raise a warning.

    Parameters
    ----------
    yaml_path: Path
        Path object of the YAML file.
    """
    warnings_ = get_config_data_value(yaml_path, "warnings")
    if warnings_ is None:
        logger.info("No warning commands found in the YAML file.")
        return {}
    warning_command_dict = {}
    for warning_ in warnings_:
        message = warning_["msg"]
        commands = warning_["commands"]
        for command in commands:
            try:
                warning_command_dict[command].append(message)
            except KeyError:
                warning_command_dict[command] = [message]

    if warning_command_dict == {}:
        logger.info("No warning commands found in the YAML file.")

    else:
        logger.info("Warning commands found in the YAML file.")

    return warning_command_dict


def create_name_map(meta_command: list[str], yaml_file_path: Path) -> dict:
    """
    Create a mapping between the initial command name and the Python function name.

    Parameters
    ----------
    meta_command: list[str]
        List of command names.
    yaml_file_path: Path
        Path object of the YAML file.

    Returns
    -------
    dict
        Dictionary with the following format: ``{"initial_command_name": "python_name"}``.
    """
    # convert all to flat and determine number of occurances
    naive_names = []
    rules = get_config_data_value(yaml_file_path, "rules")
    specific_command_mapping = get_config_data_value(yaml_file_path, "specific_command_mapping")
    ignored_commands = get_config_data_value(yaml_file_path, "ignored_commands")
    for ans_name in meta_command:
        ans_name = ans_name.lower()
        if not ans_name[0].isalnum():
            ans_name = ans_name[1:]
        naive_names.append(ans_name)

    # map command to pycommand function
    name_map = {}

    # second pass for each name
    for ans_name in meta_command:
        if ans_name in ignored_commands:
            continue
        elif ans_name in specific_command_mapping:
            py_name = specific_command_mapping[ans_name]
        else:
            lower_name = ans_name.lower()
            if not lower_name[0].isalnum():
                alpha_name = lower_name[1:]
            else:
                alpha_name = lower_name

            if naive_names.count(alpha_name) > 1:
                if rules:
                    py_name = lower_name
                    for rule_name, rule in rules.items():
                        py_name = py_name.replace(rule_name, rule)
                    if py_name == lower_name and not py_name[0].isalnum():
                        raise ValueError(
                            f"""
                            Additional rules need to be defined.
                            The {ans_name} function name is in conflict with another function.
                            """
                        )
                else:
                    raise ValueError(
                        f"""Function '{ans_name}' has identical name to another function.
                        You need to provide additional rules within the ``config.yaml`` file
                        to differentiate them."""
                    )

            else:
                py_name = alpha_name

        name_map[ans_name] = py_name

    return name_map


def import_handler(
    filename: Path,
    additional_content: str,
    str_before_def: str,
) -> None:
    """
    Handle the imports in the Python file.

    Parameters
    ----------
    filename: Path
        Path object of the Python file.
    additional_content: str
        Additional content to add to the Python file.
    str_before_def: str
        String before the function definition.
    """

    content = open(filename, "r").read()
    list_imports = list(filter(None, str_before_def.split("\n")))
    for import_line in list_imports:
        if import_line in content:
            list_imports.remove(import_line)
        additional_content = additional_content.replace(import_line, "")

    if len(list_imports) > 0:
        str_before_def = "\n".join(list_imports) + "\n\n"
        with open(filename, "r+") as f:
            f.seek(0, 0)
            f.write(str_before_def + content + additional_content)
    else:
        with open(filename, "a") as f:
            f.write(additional_content)


# ############################################################################
# AST functions
# ############################################################################


def split_trail_alpha(text: str) -> Tuple[str, str]:
    """
    Split a string based on the last tailing non-alphanumeric character.

    Parameters
    ----------
    text: str
        String to split.
    """
    for ii, char in enumerate(text):
        if not char.isalnum():
            break

    ii += 1

    return text[:ii], text[ii:]


def is_numeric(text: str) -> bool:
    """
    Return ``True`` when a string is numeric.

    Parameters
    ----------
    text: str
        String to check.

    Returns
    -------
    bool
        ``True`` if the string is numeric.
    """
    try:
        float(text)
        return True
    except ValueError:
        return False


def get_refentry(filename: Path) -> list:
    """
    Get the reference entry from an XML file.

    Parameters
    ----------
    filename: Path
        Path object of an XML file.
    """
    root = fromstring(open(filename, "rb").read())
    return list(root.iterfind(".//refentry"))
