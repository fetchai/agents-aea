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
from typing import Any, Callable, Collection, Dict, Optional, cast

from packaging.specifiers import SpecifierSet
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

_AEA_ALL_PATTERN = r"(?<={package_name}\[all\]==){version}"
AEA_PATHS = {
    Path("deploy-image", "Dockerfile"): _AEA_ALL_PATTERN,
    Path("develop-image", "docker-env.sh"): "(?<=aea-develop:){version}",
    Path("docs", "quickstart.md"): "(?<=v){version}",
    Path("examples", "tac_deploy", "Dockerfile"): _AEA_ALL_PATTERN,
    Path("scripts", "install.ps1"): _AEA_ALL_PATTERN,
    Path("scripts", "install.sh"): _AEA_ALL_PATTERN,
    Path(
        "tests", "test_docs", "test_bash_yaml", "md_files", "bash-quickstart.md"
    ): "(?<=v){version}",
    Path("user-image", "docker-env.sh"): "(?<=aea-user:){version}",
}


def check_executed(func: Callable) -> Callable:
    """Check a functor has been already executed; if yes, raise error."""

    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
        if self.is_executed:
            raise ValueError("already executed")
        self._executed = True
        self._result = func(self, *args, **kwargs)

    return wrapper


class PythonPackageVersionBumper:
    """Utility class to bump Python package versions."""

    IGNORE_DIRS = (
        Path(".git"),
    )

    def __init__(
        self,
        root_dir: Path,
        python_pkg_dir: Path,
        new_version: Version,
        files_to_pattern: Dict[Path, str],
        specifier_set_patterns: Collection[str],
        package_name: Optional[str] = None,
        ignore_dirs: Collection[Path] = (),
    ):
        """
        Initialize the utility class.

        :param root_dir: the root directory from which to look for files.
        :param python_pkg_dir: the path to the Python package to upgrade.
        :param new_version: the new version.
        :param package_name: the Python package name aliases (defaults to
           dirname of python_pkg_dir).
        :param files_to_pattern: a list of pairs.
        :param specifier_set_patterns: a list of patterns for specifier sets.
        :param ignore_dirs: a list of paths to ignore during the substitution.
        """
        self.root_dir = root_dir
        self.python_pkg_dir = python_pkg_dir
        self.new_version = new_version
        self.files_to_pattern = files_to_pattern
        self.specifier_set_patterns = specifier_set_patterns
        self.package_name = package_name or self.python_pkg_dir.name
        self.ignore_dirs = ignore_dirs or self.IGNORE_DIRS

        self._current_version: Optional[str] = None

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
        return cast(bool, self._result)

    @check_executed
    def run(self) -> bool:
        """Main entrypoint."""
        new_version_string = str(self.new_version)
        current_version_str = self.update_version_for_package(new_version_string)

        # validate current version
        current_version: Version = Version(current_version_str)
        current_version_str = str(current_version)
        self._current_version = current_version_str
        self.update_version_for_files()

        return self.update_version_specifiers(current_version, self.new_version)

    def update_version_for_files(self) -> None:
        """Update the version."""
        for filepath, regex_template in self.files_to_pattern.items():
            self.update_version_for_file(
                filepath,
                cast(str, self._current_version),
                str(self.new_version),
                version_regex_template=regex_template,
            )

    def update_version_for_package(self, new_version: str) -> str:
        """
        Update version for file.

        :param new_version: the new version
        :return: the current version
        """
        current_version = ""
        path = self.python_pkg_dir / Path("__version__.py")
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

    def update_version_for_file(
        self,
        path: Path,
        current_version: str,
        new_version: str,
        version_regex_template: Optional[str] = None,
    ) -> None:
        """
        Update version for file.

        :param path: the file path
        :param current_version: the regex for the current version
        :param new_version: the new version
        :param version_regex_template: the regex template
          to replace with the current version. Defaults to exactly
          the current version.
        """
        if version_regex_template is not None:
            regex_str = version_regex_template.format(
                package_name=self.package_name, version=current_version
            )
        else:
            regex_str = current_version
        pattern = re.compile(regex_str)
        content = path.read_text()
        content = pattern.sub(new_version, content)
        path.write_text(content)

    def update_version_specifiers(
        self, old_version: Version, new_version: Version
    ) -> bool:
        """
        Update specifier set.

        :param old_version: the old version.
        :param new_version: the new version.
        :return: True if the update has been done, False otherwise.
        """
        old_specifier_set = compute_specifier_from_version(old_version)
        new_specifier_set = compute_specifier_from_version(new_version)
        print(f"Old version specifier: {old_specifier_set}")
        print(f"New version specifier: {new_specifier_set}")
        if old_specifier_set == new_specifier_set:
            print("Not updating version specifier - they haven't changed.")
            return False
        for file in filter(lambda p: not p.is_dir(), self.root_dir.rglob("*")):
            dir_root = Path(file.parts[0])
            if dir_root in self.ignore_dirs:
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
                content = self._replace_specifier_sets(
                    old_specifier_set, new_specifier_set, content
                )
                file.write_text(content)
        return True

    def _replace_specifier_sets(
        self, old_specifier_set: str, new_specifier_set: str, content: str
    ) -> str:
        old_specifier_set_regex = self.get_regex_from_specifier_set(old_specifier_set)
        for pattern_template in self.specifier_set_patterns:
            pattern = re.compile(
                pattern_template.format(
                    package_name=self.package_name,
                    specifier_set=old_specifier_set_regex,
                )
            )
            if pattern.search(content) is not None:
                content = pattern.sub(new_specifier_set, content)
        return content

    def get_regex_from_specifier_set(self, specifier_set: str) -> str:
        """
        Get the regex for specifier sets.

        This function accepts input of the form:

            ">={lower_bound_version}, <{upper_bound_version}"

        And computes a regex pattern:

            ">={lower_bound_version}, *<{upper_bound_version}|<{upper_bound_version}, *>={lower_bound_version}"

        i.e. not considering the order of the specifiers.

        :param specifier_set: The string representation of the specifier set
        :return: a regex pattern
        """
        specifiers = SpecifierSet(specifier_set)
        upper, lower = sorted(specifiers, key=lambda x: str(x))
        alternatives = list()
        alternatives.append(f"{upper} *{lower}")
        alternatives.append(f"{lower} *{upper}")
        return "|".join(alternatives)


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
        AEA_DIR.parent,
        AEA_DIR,
        new_aea_version,
        specifier_set_patterns=[
            "(?<=aea_version:) *({specifier_set})",
            "(?<={package_name})({specifier_set})",
        ],
        files_to_pattern=AEA_PATHS,
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
