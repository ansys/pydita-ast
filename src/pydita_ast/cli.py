# Copyright (c) 2023 ANSYS, Inc. All rights reserved.

"""Command Line Interface for PyDita-AST."""

import os

import click
from pydita_ast import __version__
from pydita_ast import writer as wr


def create_package(xml_path=None, functions_path=None, target_path=None):
    """Create Python package based on a XML documentation.

    Parameters
    ----------
    xml_path: str
        Path to the directory that contains the XML documentation to convert.

    functions_path: str, optional
        Path to the directory that contains the functions that need to be customized.
        The default value is None.

    target_path: str, optional
        Path to the directory where you want the autogenerated package to be created.
        The default value is the current working directory.

    """
    if xml_path is None:
        xml_path = os.environ.get("XML_PATH")
    if xml_path is None:
        raise RuntimeError(
            "Missing the XML documentation path. Specify this with either xml_path or set the XML_PATH environment variable"  # noqa : E501
        )
    else:
        xml_path = os.path.abspath(os.path.expanduser(xml_path))
        if not os.path.isdir(xml_path):
            raise FileExistsError(
                "Please, enter a valid directory path that contains the XML documentation to convert."  # noqa : E501
            )

    if functions_path is None:
        print(
            "No customized functions path was entered. The default code generation will be applied to all the commands.",  # noqa : E501
            "You can specify the customized functions by adding a path to the --func-path argument.",  # noqa : E501
        )

    else:
        functions_path = os.path.abspath(os.path.expanduser(functions_path))
        if not os.path.isdir(functions_path):
            raise FileExistsError(
                "Please, enter a valid directory path that contains the functions that need to be customized."  # noqa : E501
            )

    if target_path is None:
        target_path = os.getcwd()

    else:
        os.makedirs(target_path, exist_ok=True)
        print(f"The autogenerated package will be saved in {target_path}.")

    commands, cmd_map, *_ = wr.convert(xml_path)
    wr.write_source(commands, cmd_map, xml_path, target_path, functions_path)
    package_path = os.path.join(target_path, "package")
    wr.write_docs(commands, cmd_map, package_path)


@click.group()
def main():
    """A Python wrapper to convert XML documentation into Python source code
    with its related Sphinx documentation."""
    pass


@main.command()
def version():
    """Display current version."""
    print(f"pydita_ast {__version__}")


@main.command()
@click.option(
    "-x",
    "--xml-path",
    type=click.Path(exists=True),
    help="Path to the directory that contains the XML documentation to convert.",
)
@click.option(
    "-f",
    "--func-path",
    type=click.Path(exists=True),
    help="Path to the directory that contains the functions that need to be customized.",
)
@click.option(
    "-t",
    "--targ-path",
    type=click.Path(),
    help="Path to the directory where you want the autogenerated package to be created.",
)
def package(xml_path, func_path, targ_path):
    """Create a Python package from your XML documentation."""
    create_package(xml_path, func_path, targ_path)
