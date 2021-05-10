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

"""Bump the AEA version throughout the code base."""

import argparse
import inspect
import os
import re
import sys
from functools import wraps
from pathlib import Path
from typing import Optional

from packaging.version import Version

from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.helpers.base import compute_specifier_from_version
from scripts.generate_ipfs_hashes import update_hashes


VERSION_NUMBER_PART_REGEX = r"(0|[1-9]\d*)"
VERSION_REGEX = fr"(any|latest|({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"

PACKAGES_DIR = Path("packages")
TESTS_DIR = Path("tests")
AEA_DIR = Path("aea")
CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
CONFIGURATION_FILENAME_REGEX = re.compile(
    "|".join(
        [
            DEFAULT_AEA_CONFIG_FILE,
            DEFAULT_SKILL_CONFIG_FILE,
            DEFAULT_CONNECTION_CONFIG_FILE,
            DEFAULT_CONTRACT_CONFIG_FILE,
            DEFAULT_PROTOCOL_CONFIG_FILE,
        ]
    )
)

IGNORE_DIRS = [Path(".git")]


def check_executed(func):
    """Check a functor has been already executed; if yes, raise error."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.is_executed:
            raise ValueError("already executed")
        self._executed = True
        self._result = func(self, *args, **kwargs)

    return wrapper


class PythonPackageVersionBumper:
    """Utility class to bump Python package versions."""

    def __init__(self, root_dir: Path, python_pkg_dir: Path, new_version: Version):
        """
        Initialize the utility class.

        :param root_dir: the root directory from which to look for files.
        :param python_pkg_dir: the path to the Python package to upgrade.
        :param new_version: the new version.
        """
        self.root_dir = root_dir
        self.python_pkg_dir = python_pkg_dir
        self.new_version = new_version

        self._current_version = None

        # functor pattern
        self._executed: bool = False
        self._result: Optional[bool] = None

    @property
    def is_executed(self) -> bool:
        """
        Return true if the functor has been executed; false otherwise.

        :return: True if it has been executed, False otherwise.
        """
        return self._executed

    @property
    def result(self) -> bool:
        """Get the result."""
        if not self.is_executed:
            raise ValueError("not executed yet")
        return self._result

    @check_executed
    def run(self) -> bool:
        """Main entrypoint."""
        new_version_string = str(self.new_version)
        current_version_str = self.update_version_for_aea(new_version_string)

        # validate current version
        current_version: Version = Version(current_version_str)
        current_version_str = str(current_version)
        self._current_version = current_version_str
        self.update_version_for_files()

        return update_aea_version_specifiers(current_version, self.new_version)

    def update_version_for_files(self) -> None:
        """Update the version."""
        files = [
            Path("benchmark", "run_from_branch.sh"),
            Path("deploy-image", "Dockerfile"),
            Path("develop-image", "docker-env.sh"),
            Path("docs", "quickstart.md"),
            Path("examples", "tac_deploy", "Dockerfile"),
            Path("scripts", "install.ps1"),
            Path("scripts", "install.sh"),
            Path(
                "tests", "test_docs", "test_bash_yaml", "md_files", "bash-quickstart.md"
            ),
            Path("user-image", "docker-env.sh"),
        ]
        for filepath in files:
            self.update_version_for_file(
                filepath, self._current_version, str(self.new_version)
            )

    def update_version_for_aea(self, new_version: str) -> str:
        """
        Update version for file.

        :param new_version: the new version
        :return: the current version
        """
        current_version = ""
        path = Path("aea", "__version__.py")
        with open(path, "rt") as fin:
            for line in fin:
                if "__version__" not in line:
                    continue
                match = re.search('__version__ = "(.*)"', line)
                if match is None:
                    raise ValueError("Current version is not well formatted.")
                current_version = match.group(1)
        if current_version == "":
            raise ValueError("No version found!")
        self.update_version_for_file(path, current_version, new_version)
        return current_version

    @classmethod
    def update_version_for_file(
        cls, path: Path, current_version: str, new_version: str
    ) -> None:
        """
        Update version for file.

        :param path: the file path
        :param current_version: the current version
        :param new_version: the new version
        """
        content = path.read_text()
        content = content.replace(current_version, new_version)
        path.write_text(content)


def update_aea_version_specifiers(old_version: Version, new_version: Version) -> bool:
    """
    Update aea_version specifier set in docs.

    :param old_version: the old version.
    :param new_version: the new version.
    :return: True if the update has been done, False otherwise.
    """
    old_specifier_set = compute_specifier_from_version(old_version)
    new_specifier_set = compute_specifier_from_version(new_version)
    print(f"Old version specifier: {old_specifier_set}")
    print(f"New version specifier: {new_specifier_set}")
    old_specifier_set_regex = re.compile(str(old_specifier_set).replace(" ", " *"))
    if old_specifier_set == new_specifier_set:
        print("Not updating version specifier - they haven't changed.")
        return False
    for file in filter(lambda p: not p.is_dir(), Path(".").rglob("*")):
        dir_root = Path(file.parts[0])
        if dir_root in IGNORE_DIRS:
            print(f"Skipping '{file}'...")
            continue
        print(
            f"Replacing '{old_specifier_set}' with '{new_specifier_set}' in '{file}'... ",
            end="",
        )
        try:
            content = file.read_text()
        except UnicodeDecodeError as e:
            print(f"Cannot read {file}: {str(e)}. Continue...")
        else:
            if old_specifier_set_regex.search(content) is not None:
                content = old_specifier_set_regex.sub(new_specifier_set, content)
                file.write_text(content)
    return True


def parse_args() -> argparse.Namespace:
    """Parse arguments."""

    parser = argparse.ArgumentParser("bump_aea_version")
    parser.add_argument(
        "--new-version", type=str, required=True, help="The new AEA version."
    )
    parser.add_argument("--no-fingerprint", action="store_true")
    arguments_ = parser.parse_args()
    return arguments_


if __name__ == "__main__":
    arguments = parse_args()
    new_aea_version = Version(arguments.new_version)

    aea_version_bumper = PythonPackageVersionBumper(
        AEA_DIR.parent, AEA_DIR, new_aea_version
    )
    have_updated_specifier_set = aea_version_bumper.run()

    print("OK")
    return_code = 0
    if arguments.no_fingerprint:
        print("Not updating fingerprints, since --no-fingerprint was specified.")
    elif not have_updated_specifier_set:
        print("Not updating fingerprints, since no specifier set has been updated.")
    else:
        print("Updating hashes and fingerprints.")
        return_code = update_hashes()
    sys.exit(return_code)
