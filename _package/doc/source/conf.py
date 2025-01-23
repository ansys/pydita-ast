from datetime import datetime

from pyconverter.generatedcommands import __version__

# Project information
project = "pyconverter-generatedcommands"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = __version__

REPOSITORY_NAME = "pyconverter-generatedcommands"
USERNAME = "pyansys"
BRANCH = "main"

# Options for HTML output
html_short_title = html_title = "PyConverter-GeneratedCommands"
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "show_prev_next": False,
}

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": f"{USERNAME}",
    "github_repo": f"{REPOSITORY_NAME}",
    "github_version": f"{BRANCH}",
}

# General configuration

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = "en"

exclude_patterns = [
    "_build",
    "links.rst",
]
pygments_style = "sphinx"

extensions = [
    "notfound.extension",
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.mathjax",
    "linuxdoc.rstFlatTable",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/dev", None),
    #     "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    #     "numpy": ("https://numpy.org/devdocs", None),
    #     "matplotlib": ("https://matplotlib.org/stable", None),
    #     "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    #     "pyvista": ("https://docs.pyvista.org/", None),
    #     "grpc": ("https://grpc.github.io/grpc/python/", None),
}

suppress_warnings = [
    "misc.highlighting_failure",  # Suppress highlighting failures
]

# Copy button customization ---------------------------------------------------
# exclude traditional Python prompts from the copied code
copybutton_prompt_text = r">>> ?|\.\.\. "
copybutton_prompt_is_regexp = True

# numpydoc configuration ------------------------------------------------------
numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        f"{project}-Documentation-{__version__}.tex",
        f"{project} Documentation",
        author,
        "manual",
    ),
]
