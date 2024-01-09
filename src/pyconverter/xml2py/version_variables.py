# Copyright (c) 2024 ANSYS, Inc. All rights reserved.

class Autogenerateddirectory:
    """Contains the version variables of the XML documentation."""

    def __init__(self, terms) -> None:
        """Class initialization."""
        self.autogenerated_directory_name = "pyconverter.generatedcommands"
        self.version = terms["ansys_internal_version"]
        self.base_url = f"https://ansyshelp.ansys.com/Views/Secured/corp/v{self._version}/en/"
        self.cmd_base_url = f"{self.base_url}/ans_cmd/"

    @property
    def autogenerated_directory_name(self):
        """Autogenerated directory name."""
        return self._autogenerated_directory_name

    @property
    def version(self):
        """Version of the XML documentation."""
        return self._version

    @property
    def base_url(self):
        """Base URL of the HTML documentation."""
        return self._base_url

    @property
    def cmd_base_url(self):
        """Command base URL."""
        return self._cmd_base_url

    @autogenerated_directory_name.setter
    def autogenerated_directory_name(self, directory_name):
        """Autogenerated directory name."""
        self._autogenerated_directory_name = directory_name

    @version.setter
    def version(self, version_value):
        """Version value."""
        self._version = version_value
        self._base_url = f"https://ansyshelp.ansys.com/Views/Secured/corp/v{self._version}/en/"

    @base_url.setter
    def base_url(self, url):
        """Base URL."""
        self._base_url = url
        self._cmd_base_url = f"{self._base_url}/ans_cmd/"

    @cmd_base_url.setter
    def cmd_base_url(self, base_url):
        """Command base URL."""
        self._cmd_base_url = base_url
