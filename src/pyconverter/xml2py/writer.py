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
import shutil
from typing import Tuple, Union

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
    get_warning_command_dict,
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


def convert(directory_path):
    """
    Convert an XML directory into an RST dictionary.

    Parameters
    ----------
    directory_path: Path
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
        xml_path: Path
            Path object of the directory containing the XML files to convert.

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
        if not xml_path.is_dir():
            raise FileNotFoundError(f'Invalid path "{xml_path}"')

        filenames = list(xml_path.glob("**/*.xml"))
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
                    group = re.findall(pat.GET_GROUP, ref)
                    if len(group) > 0:
                        if group[0] == "xtycadimport":
                            logging.warning(f"CAD command - {command.name} will not be converted.")
                            continue  # CAD imports need to be handdled differently -- LOGGER here
                        command.group = terms[group[0]]
                    else:
                        classname = re.findall(pat.GET_CLASSNAME, ref)
                        if len(classname) > 1:
                            typename = re.findall(pat.GET_TYPENAME_2OPT, ref)[
                                0
                            ]  # the function is defined in the first module (example with CECYC)
                        else:
                            typename = re.findall(pat.GET_TYPENAME_1OPT, ref)[0]
                        command.group = [classname[0], typename]
                        command.is_archived = True

        return {cmd.name: cmd for cmd in xml_commands}

    command_map_meta = load_commands(
        xml_path.expanduser(),
        meta_only=True,
    )
    meta_command = list(command_map_meta.keys())

    # create command mapping between the ansys command name and the pycommand method
    # remove the start and slash whenever possible, for example, /GCOLUMN can simply
    # be gcolumn since it's the only command, but VGET and *VGET must be vget and star_vget

    name_map = create_name_map(meta_command, Path("config.yaml"))
    ast.NameMap(name_map)

    # TODO: accept conversion of a single command

    # convert a single command
    # if command is not None:
    #     if command not in command_meta:
    #         raise ValueError(f"Invalid command {command}")
    #     fname = Path(command_meta[command].xml_filename)
    #     cmd = ast.XMLCommand(fname.expanduser())
    #     commands = {to_py_name(cmd.name): cmd}
    # else:  # convert all commands

    command_map = load_commands(xml_path)

    return command_map, name_map


def copy_template_package(template_path: Path, new_package_path: Path, clean: bool = False) -> Path:
    """
    Add files and directory from a template directory path to a new path.

    Parameters
    ----------
    template_path: Path
        Path object containing the directory to copy.

    new_package_path: Path
        Path object containing the directory where the new files and directorys are to be added.

    clean: bool, optional
        Whether the directories in the path for the new package must be cleared before adding
        new files. The default value is ``False``.

    Returns
    -------
    Path
        Path object containing the source files of the created
        ``xml-commands`` package.

    """
    filename_list = list(template_path.glob("*"))

    for filename in filename_list:
        new_path_dir = new_package_path / filename.name
        if filename.is_dir():
            if not new_path_dir.is_dir():
                new_path_dir.mkdir(parents=True, exist_ok=True)
            elif new_path_dir.is_dir() and clean:
                shutil.rmtree(new_path_dir)
                new_path_dir.mkdir(parents=True)
            copy_template_package(filename, new_path_dir, clean)
        else:
            shutil.copy(filename, new_package_path)


def write_global__init__file(library_path: Path, config_path: Path) -> None:
    """
    Write the ``__init__.py`` file for the package generated.

    Parameters
    ----------
    library_path: Path
        Path object of the directory containing the generated package.
    """

    project_name = get_config_data_value(config_path, "project_name")
    subfolder_values = get_config_data_value(config_path, "subfolders")

    if subfolder_values:
        init_folder = library_path
        for subfolder in subfolder_values:
            init_folder = init_folder.parent
        initial_imports = ".".join(subfolder_values)
    else:
        init_folder = library_path
        initial_imports = ""

    init_path = init_folder / "__init__.py"

    with open(init_path, "w") as fid:
        fid.write(f"from .{initial_imports} import (\n")
        for dir in library_path.iterdir():
            if dir.is_dir():
                fid.write(f"    {dir.stem},\n")
        fid.write(")\n\n")
        fid.write("try:\n")
        fid.write("    import importlib.metadata as importlib_metadata\n")
        fid.write("except ModuleNotFoundError:\n")
        fid.write("    import importlib_metadata\n\n")
        fid.write("__version__ = importlib_metadata.version(__name__.replace('.', '-'))\n")
        fid.write(f'"""{project_name} version."""\n')
    fid.close()


def write__init__file(library_path: Path) -> None:
    """ "
    Write the ``__init__.py`` file within each module directory.

    Parameters
    ----------
    library_path: Path
        Path object of the directory containing the generated package.
    """

    for dir in library_path.iterdir():
        if dir.is_dir():
            listdir = list(dir.iterdir())
            if len(listdir) > 0:
                with open(dir / "__init__.py", "w") as fid:
                    fid.write(f"from . import (\n")
                    for file in listdir:
                        if file.name.endswith(".py"):
                            fid.write(f"    {file.stem},\n")
                    fid.write(")\n")
                    fid.close()


def get_library_path(new_package_path: Path, config_path: Path, subfolder: bool = True) -> Path:
    """
    Get the desired library path with the following format:
    ``new_package_path/library_structure``.

    For instance, if ``library_name_structured`` in the ``config.yaml`` file is
    ``["pyconverter", "generatedcommands"]``, the function returns
    ``new_package_path/pyconverter/generatedcommands``.

    Parameters
    ----------
    new_package_path: Path
        Path objecy of the new package directory.
    config_path: str
        Path to the configuration file.

    Returns
    -------
    Path
        Path object of the new library structure.
    """
    library_name = get_config_data_value(config_path, "library_name_structured")
    if not "src" in library_name:
        library_name.insert(0, "src")
    if subfolder:
        subfolder_values = get_config_data_value(config_path, "subfolders")
        if subfolder_values:
            library_name.extend(subfolder_values)
    return new_package_path.joinpath(*library_name)


def get_module_info(library_path: Path, command: ast.XMLCommand) -> Tuple[str, str, Path]:
    """
    Get the module name, class name, and module path from command
    information.

    Parameters
    ----------
    library_path: Path
        Path object to the library directory.
    command: ast.XMLCommand
        Command object.

    Returns
    -------
    str
        Module where the command is stored.
    str
        Class where the command is stored.
    Path
        Path object of the module directory
    """
    initial_module_name, initial_class_name = command.group
    initial_module_name = initial_module_name.replace("/", "")
    module_name = initial_module_name.replace(" ", "_").lower()
    module_path = library_path / module_name
    return module_name, initial_class_name, module_path


def get_class_info(initial_class_name: str, module_path: Path) -> Tuple[str, str, Path]:
    """
    Get the class name, file name, and file path from the initial class name.

    Parameters
    ----------
    initial_class_name: str
        Initial class name.
    module_path: Path
        Path object of the module directory.

    Returns
    -------
    str
        Class name.
    str
        File name.
    Path
        File path.
    """
    class_name = initial_class_name.title().replace(" ", "").replace("/", "")
    file_name = initial_class_name.replace(" ", "_").replace("/", "_").lower()
    file_path = module_path / f"{file_name}.py"
    return class_name, file_name, file_path


def write_source(
    command_map: dict,
    name_map: dict,
    xml_doc_path: Path,
    target_path: Path,
    path_custom_functions: Union[Path, None] = None,
    template_path: Union[Path, None] = None,
    config_path: Path = Path("config.yaml"),
    clean: bool = True,
    structured: bool = True,
    check_structure_map: bool = False,
    check_files: bool = True,
) -> Tuple[list, dict]:
    """Write out XML commands as Python source files.

    Parameters
    ----------
    command_map: dict
        Dictionary with the following format: ``{"initial_command_name": command_obj}``.
    name_map: dict
        Dictionary with the following format: ``{"initial_command_name": "python_name"}``.
    xml_doc_path: Path
        Path object containing the XML directory to convert.
    target_path: Path
        Path object to generate the new package to.
    path_custom_functions: Path, optional
        Path object containing the customized functions. The default value is ``None``.
    template_path: Path, optional
        Path object of the template to use. If no path is provided, the default template is used.
    config_path: Path, optional
        Path object of the configuration file. The default value is ``Path(config.yaml)``.`.
    clean: bool, optional
        Whether the directories in the new package path must be cleared before adding
        new files. The default value is ``True``.
    structured: bool, optional
        Whether the package should be structured. The default value is ``True``.
    check_structure_map: bool, optional
        Whether the structure map must be checked. The default value is ``False``.
    check_files: bool, optional
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
        logging.info("The default template are used to create the package.")
        template_path = Path.cwd() / "_package"
        if not template_path.is_dir:
            download_template()

    new_package_name = get_config_data_value(config_path, "new_package_name")
    logging.info(f"Creating package {new_package_name}...")
    new_package_path = target_path / new_package_name

    ignored_commands = set(get_config_data_value(config_path, "ignored_commands"))

    if clean:
        if new_package_path.is_dir():
            shutil.rmtree(new_package_path)

    library_path = Path(get_library_path(new_package_path, config_path))

    warning_command_dict = get_warning_command_dict(config_path)

    if not library_path.is_dir():
        library_path.mkdir(parents=True, exist_ok=True)

    if structured == False:
        package_structure = None
        for initial_command_name, command_obj in tqdm(command_map.items(), desc="Writing commands"):
            if initial_command_name in ignored_commands:
                continue
            python_name = name_map[initial_command_name]
            path = library_path / f"{python_name}.py"
            python_method = command_obj.to_python(custom_functions, warning_command_dict, indent="")
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
            if command.name in ignored_commands or command.group is None:
                continue

            module_name, initial_class_name, module_path = get_module_info(library_path, command)

            # Create the module folder and structure if it doesn't exist yet
            if not module_path.is_dir():
                module_path.mkdir(parents=True, exist_ok=True)
                package_structure[module_name] = {}

            # Check whether the class name needs to follow a specific rule
            if initial_class_name in specific_classes.keys():
                initial_class_name = specific_classes[initial_class_name]

            class_name, file_name, file_path = get_class_info(initial_class_name, module_path)

            # Create the class file and structure if it doesn't exist yet
            if not file_path.is_file():
                class_structure = []
                with open(file_path, "w", encoding="utf-8") as fid:
                    fid.write(f"class {class_name}:\n")
            else:
                # Get the class structure
                class_structure = package_structure[module_name][file_name][1]
            class_structure.append(command.py_name)

            package_structure[module_name][file_name] = [class_name, class_structure]
            python_method = command.to_python(
                custom_functions, warning_command_dict, indent=4 * " "
            )

            # Check if there are any imports to be added before the function definition.
            reg_before_def = pat.BEFORE_DEF + f"{command.py_name})"
            # Needs to be ``re.search`` and not ``re.findall`` for performance reasons
            str_before_def = re.search(reg_before_def, python_method).group()
            str_before_def = str_before_def.replace("\n    ", "")

            # Write the Python method to the class file
            if str_before_def != "":
                import_handler(file_path, python_method, str_before_def)
            else:
                with open(file_path, "a", encoding="utf-8") as fid:
                    fid.write(f"{python_method}\n")
                    fid.close()
            all_commands.append(command.name)

    if check_structure_map:
        for command_name in name_map.keys():
            if command_name not in all_commands:
                raise Exception(f"{command_name} is not in the structure map.")

    if check_files:
        for module_name in package_structure.keys():
            for class_name, _ in package_structure[module_name].items():
                file_path = library_path / module_name / f"{class_name}.py"
                try:
                    subprocess.run(["python", str(file_path)])
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to execute '{python_method}' from '{file_path}'."
                    ) from e

    write_global__init__file(library_path, config_path)
    write__init__file(library_path)

    logging.info(f"Commands written to {library_path}")

    # Copy package files to the package directory
    copy_template_package(template_path, new_package_path, clean)
    graph_path = get_paths(xml_doc_path)[0]
    shutil.copytree(graph_path, new_package_path / "doc" / "source" / "images")
    return package_structure


def write_docs(
    package_path: Path, package_structure: dict = None, config_path: Path = Path("config.yaml")
) -> Path:
    """Output to the autogenerated ``package`` directory.

    Parameters
    ----------
    package_path: Path
        Path object of the new package folder.
    package_structure: dict, optional
        Dictionary with the following format:
        ``{'python_module_name': [{'python_class_name': python_names_list}]}``.
    config_path: Path, optional
        Path object of the configuration file. The default value is ``Path(config.yaml)``.

    Returns
    -------
    Path
        Path to the new document page.
    """
    library_name = get_config_data_value(config_path, "library_name_structured")
    if library_name[0] == "src":
        library_name.pop(0)
    subfolder_values = get_config_data_value(config_path, "subfolders")
    if subfolder_values:
        library_name.extend(subfolder_values)
    library_name = ".".join(library_name)

    doc_package_path = package_path / "doc" / "source"
    if not doc_package_path.is_dir():
        doc_package_path.mkdir(parents=True, exist_ok=True)

    doc_src_content = """
API documentation
==================

.. toctree::
   :maxdepth: 1

"""
    for module_name in package_structure.keys():
        doc_src_content += f"   {module_name}/index.rst\n"

    # Write the main doc file
    doc_src = doc_package_path / "docs.rst"
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
            module_folder = doc_package_path / module_folder_name
            module_folder.mkdir(parents=True, exist_ok=True)
            module_file = module_folder / "index.rst"
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
                for python_command_name in sorted(method_list):
                    class_content += f"   {class_name}.{python_command_name}\n"

                # Write the class file
                class_file = module_folder / f"{class_file_name}.rst"
                with open(class_file, "w") as fid:
                    fid.write(class_content)

    return doc_src
