#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
This script checks that all the Python files of the repository have:

- (optional) the Python shebang
- the encoding header;
- the copyright notice;

It is assumed the script is run from the repository root.
"""

import argparse
import re
import sys
from pathlib import Path


VERSION_NUMBER_PART_REGEX = r"(0|[1-9]\d*)"
VERSION_REGEX = fr"(any|latest|({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"


def update_version_for_files(current_version: str, new_version: str) -> None:
    """
    Update the version.

    :param current_version: the current version
    :param new_version: the new version
    """
    files = [
        Path("benchmark", "run_from_branch.sh"),
        Path("deploy-image", "docker-env.sh"),
        Path("deploy-image", "Dockerfile"),
        Path("develop-image", "docker-env.sh"),
        Path("docs", "quickstart.md"),
        Path("tests", "test_docs", "test_bash_yaml", "md_files", "bash-quickstart.md"),
        Path("user-image", "docker-env.sh"),
    ]
    for filepath in files:
        update_version_for_file(filepath, current_version, new_version)


def update_version_for_aea(new_version: str) -> str:
    """
    Update version for file.

    :param filepath: the file path
    :param new_version: the new version
    :return: the current version
    """
    current_version = ""
    path = Path("aea", "__version__.py")
    with open(path, "rt") as fin:
        for line in fin:
            if "__version__" not in line:
                continue
            match = re.search(VERSION_REGEX, line)
            if match is None:
                raise ValueError("Current version is not well formatted.")
            current_version = match.group(1)
    if current_version == "":
        raise ValueError("No version found!")
    update_version_for_file(path, current_version, new_version)
    return current_version


def update_version_for_file(path: Path, current_version: str, new_version: str) -> None:
    """
    Update version for file.

    :param filepath: the file path
    :param current_version: the current version
    :param new_version: the new version
    """
    content = path.read_text()
    content = content.replace(current_version, new_version)
    with path.open(mode="w") as f:
        f.write(content)


def parse_args() -> argparse.Namespace:
    """Parse arguments."""

    parser = argparse.ArgumentParser("bump_aea_version")
    parser.add_argument(
        "--new-version", type=str, required=True, help="The new version."
    )
    arguments_ = parser.parse_args()
    return arguments_


if __name__ == "__main__":
    arguments = parse_args()
    _new_version = arguments.new_version

    _current_version = update_version_for_aea(_new_version)
    update_version_for_files(_current_version, _new_version)

    print("OK")
    sys.exit(0)
