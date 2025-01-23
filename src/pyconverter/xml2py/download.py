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

"""Functions to download template datasets from the pyconverter-xml2py repository.
"""

from pathlib import Path

from github import ContentFile, Github, Repository
import requests


def download(c: ContentFile, out: Path) -> None:
    """
    This function initially comes from the following GitHub repository:
    https://github.com/Nordgaren/Github-Folder-Downloader

    """
    r = requests.get(c.download_url)
    output_path = out / c.path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        print(f"downloading {c.path} to {out}")
        f.write(r.content)


def download_folder(repo: Repository, folder: str, out: str, recursive: bool) -> None:
    """
    This function initially comes from the following GitHub repository:
    https://github.com/Nordgaren/Github-Folder-Downloader

    """
    contents = repo.get_contents(folder)
    for c in contents:
        if c.download_url is None:
            if recursive:
                download_folder(repo, c.path, out, recursive)
            continue
        download(c, out)


def download_template() -> None:
    """Download the templage package provided by default."""

    g = Github()
    repo = g.get_repo("ansys/pyconverter-xml2py")
    download_folder(repo, "_package", ".", True)
