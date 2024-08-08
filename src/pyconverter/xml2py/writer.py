# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
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

import glob
import logging
import os
import shutil
import sys

from pyconverter.xml2py import ast_tree as ast
from pyconverter.xml2py import load_xml_doc as load
from pyconverter.xml2py.custom_functions import CustomFunctions
from pyconverter.xml2py.directory_format import get_paths
from pyconverter.xml2py.download import download_template
import pyconverter.xml2py.utils.regex_pattern as pat
from pyconverter.xml2py.utils.utils import (
    create_name_map,
    get_config_data_value,
    get_refentry,
    import_handler,
)
import regex as re
from tqdm import tqdm

# common statements used within the docs to avoid duplication
CONST = {
    "Dtl?": "",
    "Caret?": "",
    "Caret1?": "",
    "Caret 40?": "",
    '``"``': "``",
}

# XML commands to skip
SKIP_XML = {"*IF", "*ELSE", "*RETURN", "*DEL"}  # Equivalent to if, else, return, del


def convert(directory_path):
    """
    Convert an XML directory into an RST dictionary.

    Parameters
    ----------
    directory_path : str
        Path to the directory containing the XML files to convert.

    Returns
    -------
    dict
        Dictionary with the following format: ``{"command_name": command_object}``.

    dict
        Dictionary with the following format: ``{"initial_command_name": "python_name"}``.
    """

    graph_path, link_path, term_path, xml_path = get_paths(directory_path)
    links = load.load_links(link_path)
    fcache = load.load_fcache(graph_path)
    docu_global = load.load_docu_global(term_path)
    terms, version_variables = load.load_terms(term_path, docu_global, links, fcache)

    def load_commands(
        xml_path,
        meta_only=False,
    ):
        """Scrape the command information from the XML command reference.

        Parameters
        ----------
        xml_path : str
            Path to the directory containing the XML files to convert.

        Examples
        --------
        >>> from convert import load_commands
        >>> commands = load_commands(
        ...     '/home/user/source/xml-cmd-doc/docu_files/ans_cmd/'
        ... )

        Returns
        -------
        dict
            Dictionary with the following format: ``{"command_name": command_object}``.

        """
        if not os.path.isdir(xml_path):
            raise FileNotFoundError(f'Invalid path "{xml_path}"')

        filenames = list(glob.glob(os.path.join(xml_path, "**", "*.xml"), recursive=True))

        if meta_only:
            desc = "Loading command metadata"
        else:
            desc = "Loading commands"

        xml_commands = []
        for filename in tqdm(filenames, desc=desc):
            # If ``get_refentry`` returns an empty list, the file is not a command file
            refentry = get_refentry(filename)
            if len(refentry) > 0:
                command = ast.XMLCommand(
                    filename,
                    refentry[0],
                    terms,
                    docu_global,
                    version_variables,
                    links,
                    fcache,
                    meta_only=meta_only,
                )
                xml_commands.append(command)
                if meta_only == False:
                    refnamediv = command.get_children_by_type("Refnamediv")[0]
                    ref = str(refnamediv.get_children_by_type("Refclass")[0])
                    group = re.findall(pat.get_group, ref)
                    if len(group) > 0:
                        if group[0] == "xtycadimport":
                            logging.warning(f"CAD command - {command.name} will not be converted.")
                            continue  # CAD imports need to be handdled differently -- LOGGER here
                        command.group = terms[group[0]]
                    else:
                        classname = re.findall(pat.get_classname, ref)
                        if len(classname) > 1:
                            typename = re.findall(pat.get_typename_2opt, ref)[
                                0
                            ]  # the function is defined in the first module (example with CECYC)
                        else:
                            typename = re.findall(pat.get_typename_1opt, ref)[0]
                        command.group = [classname[0], typename]
                        command.is_archived = True

        return {cmd.name: cmd for cmd in xml_commands}

    command_map_meta = load_commands(
        os.path.expanduser(xml_path),
        meta_only=True,
    )
    meta_command = command_map_meta.keys()

    # create command mapping between the ansys command name and the pycommand method
    # remove the start and slash whenever possible, for example, /GCOLUMN can simply
    # be gcolumn since it's the only command, but VGET and *VGET must be vget and star_vget

    name_map = create_name_map(meta_command, "config.yaml")
    ast.NameMap(name_map)

    # TODO : accept conversion of a single command

    # convert a single command
    # if command is not None:
    #     if command not in command_meta:
    #         raise ValueError(f"Invalid command {command}")
    #     fname = command_meta[command].xml_filename
    #     cmd = ast.XMLCommand(os.path.expanduser(fname), )
    #     commands = {to_py_name(cmd.name): cmd}
    # else:  # convert all commands

    command_map = load_commands(xml_path)

    return command_map, name_map


def copy_template_package(template_path, new_package_path, clean=False):
    """
    Add files and directory from a template directory path to a new path.

    Parameters
    ----------
    template_path : str
        Path containing the directory to copy.

    new_package_path : str
        Path containing the directory where the new files and directorys are to be added.

    clean : bool, optional
        Whether the directories in the path for the new package must be cleared before adding
        new files. The default is ``False``.

    Returns
    -------
    str
        Path containing the source files of the created
        ``xml-commands`` package.

    """
    # .vale.ini and .gitignore are hidden files.
    if sys.version_info.major == 3 and sys.version_info.minor >= 11:
        filename_list = glob.glob(
            os.path.join(template_path, "*"), recursive=True, include_hidden=True
        )
    else:
        filename_list = glob.glob(os.path.join(template_path, "*"), recursive=True)
        # Manually copying .vale.ini and .gitignore
        styles_path = os.path.join(new_package_path, "doc", "styles")
        if not os.path.isdir(styles_path):
            os.makedirs(styles_path, exist_ok=True)
        vale_path = ["doc", ".vale.ini"]
        gitignore_path = ["doc", "styles", ".gitignore"]
        hidden_path = [vale_path, gitignore_path]
        for hpath in hidden_path:
            hidden_template = os.path.join(template_path, *hpath)
            hidden_new_path = os.path.join(new_package_path, *hpath)
            if os.path.isfile(hidden_template) and not os.path.isfile(hidden_new_path):
                shutil.copy(hidden_template, hidden_new_path)

    for filename in filename_list:
        split_name_dir = filename.split(os.path.sep)
        new_path_dir = os.path.join(new_package_path, split_name_dir[-1])

        if os.path.isdir(filename):
            if not os.path.isdir(new_path_dir):
                os.makedirs(new_path_dir, exist_ok=True)
            elif os.path.isdir(new_path_dir) and clean:
                shutil.rmtree(new_path_dir)
                os.makedirs(new_path_dir)
            copy_template_package(filename, new_path_dir, clean)

        else:
            shutil.copy(filename, new_package_path)


def write_global__init__file(library_path):
    """
    Write the __init__.py file for the package generated.

    Parameters
    ----------
    library_path : str
        Path to the directory containing the generated package.

    name_map : dict
        Dictionary with the following format: ``{"initial_command_name": "python_name"}``.

    command_map : dict
        Dictionary with the following format: ``{"initial_command_name": command_object}``.

    structure_map : dict, optional
        Dictionary with the following format:
        ``{'module_name': [{'class_name': python_names_list}]}``.
        The default value is ``None``.
    """
    mod_file = os.path.join(library_path, "__init__.py")

    with open(mod_file, "w") as fid:
        fid.write(f"from . import (\n")
        for dir in os.listdir(library_path):
            if os.path.isdir(os.path.join(library_path, dir)):
                fid.write(f"    {dir},\n")
        fid.write(")\n\n")
        fid.write("try:\n")
        fid.write("    import importlib.metadata as importlib_metadata\n")
        fid.write("except ModuleNotFoundError:\n")
        fid.write("    import importlib_metadata\n\n")
        fid.write("__version__ = importlib_metadata.version(__name__.replace('.', '-'))\n")
        fid.write('"""PyConverter-GeneratedCommands version."""\n')
    fid.close()


def write__init__file(library_path):
    """ "
    Write the __init__.py file within each module directory.

    Parameters
    ----------
    library_path : str
        Path to the directory containing the generated package.
    """

    for dir in os.listdir(library_path):
        if os.path.isdir(os.path.join(library_path, dir)):
            listdir = os.listdir(os.path.join(library_path, dir))
            if len(listdir) > 0:
                with open(os.path.join(library_path, dir, "__init__.py"), "w") as fid:
                    fid.write(f"from . import (\n")
                    for file in listdir:
                        if file.endswith(".py"):
                            fid.write(f"    {file[:-3]},\n")
                    fid.write(")\n")
                    fid.close()


def get_library_path(new_package_path, config_path):
    """
    Return the desired library path with the following format:
    ``new_package_path/library_structure``.

    For instance, if ``library_name_structured`` in the ``config.yaml`` file is
    ``["pyconverter", "generatedcommands"]``, the function will return
    ``new_package_path/pyconverter/generatedcommands``.

    Parameters
    ----------
    new_package_path : str
        Path to the new package directory.
    config_path : str
        Path to the configuration file.

    Returns
    -------
    str
        Path to the desired library structure.
    """
    library_name = get_config_data_value(config_path, "library_name_structured")
    if not "src" in library_name:
        library_name.insert(0, "src")
    return os.path.join(new_package_path, *library_name)


def get_module_info(library_path, command):
    """
    Get the module name, class name, and module path from the command group.

    Parameters
    ----------
    library_path : str
        Path to the library directory.

    command : ast.XMLCommand
        Command object.
    """
    initial_module_name, initial_class_name = command.group
    initial_module_name = initial_module_name.replace("/", "")
    module_name = initial_module_name.replace(" ", "_").lower()
    module_path = os.path.join(library_path, module_name)
    return module_name, initial_class_name, module_path


def get_class_info(initial_class_name, module_path):
    """
    Return the class name, file name, and file path from the initial class name.

    Parameters
    ----------
    initial_class_name : str
        Initial class name.

    module_path : str
        Path to the module directory.

    Returns
    -------
    str
        Class name.

    str
        File name.

    str
        File path.
    """
    class_name = initial_class_name.title().replace(" ", "").replace("/", "")
    file_name = initial_class_name.replace(" ", "_").replace("/", "_").lower()
    file_path = os.path.join(module_path, f"{file_name}.py")
    return class_name, file_name, file_path


def write_source(
    command_map,
    name_map,
    xml_doc_path,
    target_path,
    path_custom_functions=None,
    template_path=None,
    config_path="config.yaml",
    clean=True,
    structured=True,
    check_structure_map=False,
    check_files=True,
):
    """Write out XML commands as Python source files.

    Parameters
    ----------
    command_map : dict
        Dictionary with the following format: ``{"initial_command_name": command_obj}``.

    name_map : dict
        Dictionary with the following format: ``{"initial_command_name": "python_name"}``.

    xml_doc_path : str
        Path containing the XML directory to convert.

    target_path : str
        Path to generate the new package to.

    path_custom_functions : str, optional
        Path containing the customized functions. The default is ``None``.

    template_path : str, optional
        Path for the template to use. If no path is provided, the default template is used.

    config_path : str, optional
        Path to the configuration file. The default is ``config.yaml``.`.

    clean : bool, optional
        Whether the directories in the new package path must be cleared before adding
        new files. The default value is ``True``.

    structured : bool, optional
        Whether the package should be structured. The default value is ``True``.

    check_structure_map : bool, optional
        Whether the structure map must be checked. The default value is ``False``.

    check_files : bool, optional
        Whether the files must be checked. The default value is ``False``.

    Returns
    -------
    list
        List of module names created.

    dict
        Dictionary with the following format:
        ``{'python_module_name': [{'python_class_name': python_names_list}]}``.
    """

    if path_custom_functions is not None:
        custom_functions = CustomFunctions(path_custom_functions)
    else:
        custom_functions = None

    if template_path is None:
        logging.info("The default template will be used to create the new package.")
        template_path = os.path.join(os.getcwd(), "_package")
        if not os.path.isdir(template_path):
            download_template()

    new_package_name = get_config_data_value(config_path, "new_package_name")
    logging.info(f"Creating package {new_package_name}...")
    new_package_path = os.path.join(target_path, new_package_name)

    if clean:
        if os.path.isdir(new_package_path):
            shutil.rmtree(new_package_path)

    library_path = get_library_path(new_package_path, config_path)

    if not os.path.isdir(library_path):
        os.makedirs(library_path)

    if structured == False:
        package_structure = None
        for initial_command_name, command_obj in tqdm(command_map.items(), desc="Writing commands"):
            if initial_command_name in SKIP_XML:
                continue
            python_name = name_map[initial_command_name]
            path = os.path.join(library_path, f"{python_name}.py")
            python_method = command_obj.to_python(custom_functions)
            try:
                exec(python_method)
                with open(path, "w", encoding="utf-8") as fid:
                    fid.write(f"{python_method}\n")
            except Exception as e:
                raise RuntimeError(f"Failed to execute {python_name}.py") from e

    else:
        import subprocess

        package_structure = {}
        all_commands = []
        specific_classes = get_config_data_value(config_path, "specific_classes")
        for command in tqdm(command_map.values(), desc="Writing commands"):
            if command.name in SKIP_XML or command.group is None:
                continue

            module_name, initial_class_name, module_path = get_module_info(library_path, command)

            # Create the module folder and structure if it doesn't exist yet
            if not os.path.isdir(module_path):
                os.makedirs(module_path)
                package_structure[module_name] = {}

            # Check whether the class name needs to follow a specific rule
            if initial_class_name in specific_classes.keys():
                initial_class_name = specific_classes[initial_class_name]

            class_name, file_name, file_path = get_class_info(initial_class_name, module_path)

            # Create the class file and structure if it doesn't exist yet
            if not os.path.isfile(file_path):
                class_structure = []
                with open(file_path, "w", encoding="utf-8") as fid:
                    fid.write(f"class {class_name}:\n")
            else:
                # Get the class structure
                class_structure = package_structure[module_name][file_name][1]
            class_structure.append(command.py_name)

            package_structure[module_name][file_name] = [class_name, class_structure]

            # Write the Python method to the class file
            with open(file_path, "a", encoding="utf-8") as fid:
                python_method = command.to_python(custom_functions, indent="    ")

                # Check if there are any imports to be added before the function definition.
                str_before_def = re.findall(pat.before_def, python_method)[0]
                output = re.findall(pat.get_imports, str_before_def)
                if len(output) == 0:
                    fid.write(f"{python_method}\n")
                    fid.close()
                else:
                    fid.close()
                    import_handler(file_path, python_method, output)

            all_commands.append(command.name)

    if check_structure_map:
        for command_name in name_map.keys():
            if command_name not in all_commands:
                raise Exception(f"{command_name} is not in the structure map")

    if check_files:
        for module_name in package_structure.keys():
            for class_name, _ in package_structure[module_name].items():
                file_path = os.path.join(library_path, module_name, f"{class_name}.py")
                try:
                    subprocess.run(["python", str(file_path)])
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to execute '{python_method}' from '{file_path}'."
                    ) from e

    write_global__init__file(library_path)
    write__init__file(library_path)

    logging.info(f"Commands written to {library_path}")

    # copy package files to the package directory
    copy_template_package(template_path, new_package_path, clean)
    graph_path = get_paths(xml_doc_path)[0]
    shutil.copytree(graph_path, os.path.join(new_package_path, "doc", "source", "images"))
    return package_structure


def write_docs(package_path, package_structure=None, config_path="config.yaml"):
    """Output to the autogenerated ``package`` directory.

    Parameters
    ----------
    package_path : str
        Path to the new package folder.

    package_structure :
        Dictionary with the following format:
        ``{'python_module_name': [{'python_class_name': python_names_list}]}``.

    config_path : str, optional
        Path to the configuration file. The default is ``config.yaml``.

    Returns
    -------
    str
        Path to the new document page.

    """
    library_name = get_config_data_value(config_path, "library_name_structured")
    if library_name[0] == "src":
        library_name.pop(0)
    library_name = ".".join(library_name)

    doc_package_path = os.path.join(package_path, "doc/source")
    if not os.path.isdir(doc_package_path):
        os.makedirs(doc_package_path)

    doc_src_content = """
API documentation
==================

.. toctree::
   :maxdepth: 1

"""
    for module_name in package_structure.keys():
        doc_src_content += f"   {module_name}/index.rst\n"

    # Write the main doc file
    doc_src = os.path.join(doc_package_path, "docs.rst")
    with open(doc_src, "w") as fid:
        fid.write(doc_src_content)

    if package_structure is not None:
        for module_folder_name, class_map in tqdm(
            package_structure.items(), desc="Writing docs..."
        ):
            module_title = module_folder_name.replace("_", " ").capitalize()

            module_content = f"""
.. _ref_{module_folder_name}:

{module_title}
{"="*len(module_title)}

.. list-table::

"""
            for class_file_name in class_map.keys():
                module_content += f"   * - :ref:`ref_{class_file_name}`\n"

            module_content += f"""

.. toctree::
   :maxdepth: 1
   :hidden:

"""
            for class_file_name in class_map.keys():
                module_content += f"   {class_file_name}\n"

            # Write the module index file
            module_folder = os.path.join(doc_package_path, f"{module_folder_name}")
            os.makedirs(module_folder, exist_ok=True)
            module_file = os.path.join(module_folder, f"index.rst")
            with open(module_file, "w") as fid:
                fid.write(module_content)

            for class_file_name, (class_name, method_list) in class_map.items():

                class_content = f"""
.. _ref_{class_file_name}:


{class_name}
{"=" * len(class_name)}


.. currentmodule:: {library_name}.{module_folder_name}.{class_file_name}

.. autoclass:: {library_name}.{module_folder_name}.{class_file_name}.{class_name}

.. autosummary::
   :template: base.rst
   :toctree: _autosummary


"""
                for python_command_name in method_list:
                    class_content += f"   {class_name}.{python_command_name}\n"

                # Write the class file
                class_file = os.path.join(module_folder, f"{class_file_name}.rst")
                with open(class_file, "w") as fid:
                    fid.write(class_content)

    return doc_src
