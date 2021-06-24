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
Bump the AEA version throughout the code base.

usage: bump_aea_version [-h] [--new-version NEW_VERSION]
                        [-p KEY=VALUE [KEY=VALUE ...]] [--no-fingerprints]
                        [--only-check]

optional arguments:
  -h, --help            show this help message and exit
  --new-version NEW_VERSION
                        The new AEA version.
  -p KEY=VALUE [KEY=VALUE ...], --plugin-new-version KEY=VALUE [KEY=VALUE ...]
                        Set a number of key-value pairs plugin-name=new-
                        plugin-version
  --no-fingerprints     Skip the computation of fingerprints.
  --only-check          Only check the need of upgrade.


Example of usage:

python scripts/bump_aea_version.py --new-version 1.1.0 -p aea-ledger-fetchai=2.0.0 -p aea-ledger-ethereum=3.0.0
python scripts/bump_aea_version.py --only-check
"""

import argparse
import inspect
import logging
import operator
import os
import re
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, cast

from git import Repo
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from aea.helpers.base import compute_specifier_from_version
from scripts.generate_ipfs_hashes import update_hashes


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
)

# if the key is a file, just process it
# if the key is a directory, process all files below it
PatternByPath = Dict[Path, str]

AEA_DIR = Path("aea")
CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = Path(os.path.join(CUR_PATH, ".."))

PLUGINS_DIR = Path("plugins")
ALL_PLUGINS = tuple(PLUGINS_DIR.iterdir())

"""
This pattern captures a specifier set in the dependencies section
of an AEA package configuration file, e.g.:

dependencies:
    ...
    aea-ledger-fetchai:
        version: >=1.0.0,<2.0.0
"""
YAML_DEPENDENCY_SPECIFIER_SET_PATTERN = (
    "(?<={package_name}:\n    version: )({specifier_set})"
)

"""
This pattern captures a specifier set for PyPI dependencies
in JSON format.

e.g.:
"aea-ledger-fetchai": {"version": ">=2.0.0, <3.0.0"}
"""
JSON_DEPENDENCY_SPECIFIER_SET_PATTERN = (
    '(?<="{package_name}": ."version": ")({specifier_set})(?=".)'
)


_AEA_ALL_PATTERN = r"(?<={package_name}\[all\]==){version}"
AEA_PATHS: PatternByPath = {
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


def compute_specifier_from_version_custom(version: Version) -> str:
    """
    Post-process aea.helpers.compute_specifier_from_version

    The output is post-process in the following way:
    - remove spaces between specifier sets
    - put upper bound before lower bound

    :param version: the version
    :return: the specifier set according to the version and semantic versioning.
    """
    specifier_set_str = compute_specifier_from_version(version)
    specifiers = SpecifierSet(specifier_set_str)
    upper, lower = sorted(specifiers, key=str)
    return f"{upper},{lower}"


def get_regex_from_specifier_set(specifier_set: str) -> str:
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
    upper, lower = sorted(specifiers, key=str)
    alternatives = list()
    alternatives.append(f"{upper} *, *{lower}")
    alternatives.append(f"{lower} *, *{upper}")
    return "|".join(alternatives)


class PythonPackageVersionBumper:
    """Utility class to bump Python package versions."""

    IGNORE_DIRS = (Path(".git"),)

    def __init__(
        self,
        root_dir: Path,
        python_pkg_dir: Path,
        new_version: Version,
        files_to_pattern: PatternByPath,
        specifier_set_patterns: Sequence[str],
        package_name: Optional[str] = None,
        ignore_dirs: Sequence[Path] = (),
    ):
        """
        Initialize the utility class.

        :param root_dir: the root directory from which to look for files.
        :param python_pkg_dir: the path to the Python package to upgrade.
        :param new_version: the new version.
        :param files_to_pattern: a list of pairs.
        :param specifier_set_patterns: a list of patterns for specifier sets.
        :param package_name: the Python package name aliases (defaults to dirname of python_pkg_dir).
        :param ignore_dirs: a list of paths to ignore during the substitution.
        """
        self.root_dir = root_dir
        self.python_pkg_dir = python_pkg_dir
        self.new_version = new_version
        self.files_to_pattern = files_to_pattern
        self.specifier_set_patterns = specifier_set_patterns
        self.package_name = package_name or self.python_pkg_dir.name
        self.ignore_dirs = ignore_dirs or self.IGNORE_DIRS

        self.repo = Repo(self.root_dir)
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
        if not self.is_different_from_latest_tag():
            logging.info(
                f"The package {self.python_pkg_dir} has no changes since last tag."
            )
            return False
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

        If __version__.py is available, parse it and check for __version__ variable.
        Otherwise, try to parse setup.py.
        Otherwise, raise error.

        :param new_version: the new version
        :return: the current version
        """
        version_path = self.python_pkg_dir / Path("__version__.py")
        setup_path = self.python_pkg_dir.parent / "setup.py"
        if version_path.exists():
            regex_template = '(?<=__version__ = [\'"])({version})(?=")'
            path = version_path
        elif setup_path.exists():
            regex_template = r'(?<=version=[\'"])({version})(?=[\'"],)'
            path = setup_path
        else:
            raise ValueError("cannot fine neither '__version__.py' nor 'setup.py'")

        content = path.read_text()
        pattern = regex_template.format(version=".*")
        current_version_candidates = re.findall(pattern, content)
        more_than_one_match = len(current_version_candidates) > 1
        if more_than_one_match:
            raise ValueError(
                f"find more than one match for current version in {path}: {current_version_candidates}"
            )
        current_version = current_version_candidates[0]
        self.update_version_for_file(
            path, current_version, new_version, version_regex_template=regex_template
        )
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
        :param version_regex_template: the regex template to replace with the current version. Defaults to exactly the current version.
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
        old_specifier_set = compute_specifier_from_version_custom(old_version)
        new_specifier_set = compute_specifier_from_version_custom(new_version)
        logging.info(f"Old version specifier: {old_specifier_set}")
        logging.info(f"New version specifier: {new_specifier_set}")
        if old_specifier_set == new_specifier_set:
            logging.info("Not updating version specifier - they haven't changed.")
            return False
        for file in filter(lambda p: not p.is_dir(), self.root_dir.rglob("*")):
            dir_root = Path(file.parts[0])
            if dir_root in self.ignore_dirs:
                logging.info(f"Skipping '{file}'...")
                continue
            logging.info(
                f"Replacing '{old_specifier_set}' with '{new_specifier_set}' in '{file}'... ",
            )
            try:
                content = file.read_text()
            except UnicodeDecodeError as e:
                logging.info(f"Cannot read {file}: {str(e)}. Continue...")
            else:
                content = self._replace_specifier_sets(
                    old_specifier_set, new_specifier_set, content
                )
                file.write_text(content)
        return True

    def _replace_specifier_sets(
        self, old_specifier_set: str, new_specifier_set: str, content: str
    ) -> str:
        old_specifier_set_regex = get_regex_from_specifier_set(old_specifier_set)
        for pattern_template in self.specifier_set_patterns:
            regex = pattern_template.format(
                package_name=self.package_name, specifier_set=old_specifier_set_regex,
            )
            pattern = re.compile(regex)
            if pattern.search(content) is not None:
                content = pattern.sub(new_specifier_set, content)
        return content

    def is_different_from_latest_tag(self) -> bool:
        """Check whether the package has changes since the latest tag."""
        assert len(self.repo.tags) > 0, "no git tags found"
        latest_tag_str = str(self.repo.tags[-1])
        args = latest_tag_str, "--", str(self.python_pkg_dir)
        logging.info(f"Running 'git diff {' '.join(args)}'")
        diff = self.repo.git.diff(*args)
        return diff != ""


def parse_args() -> argparse.Namespace:
    """Parse arguments."""

    parser = argparse.ArgumentParser("bump_aea_version")
    parser.add_argument(
        "--new-version", type=str, required=False, help="The new AEA version."
    )
    parser.add_argument(
        "-p",
        "--plugin-new-version",
        metavar="KEY=VALUE",
        nargs="+",
        help="Set a number of key-value pairs plugin-name=new-plugin-version",
        default={},
    )
    parser.add_argument(
        "--no-fingerprints",
        action="store_true",
        help="Skip the computation of fingerprints.",
    )
    parser.add_argument(
        "--only-check", action="store_true", help="Only check the need of upgrade."
    )
    arguments_ = parser.parse_args()
    return arguments_


def make_aea_bumper(new_aea_version: Version) -> PythonPackageVersionBumper:
    """Build the AEA Python package version bumper."""
    aea_version_bumper = PythonPackageVersionBumper(
        ROOT_DIR,
        AEA_DIR,
        new_aea_version,
        specifier_set_patterns=[
            "(?<=aea_version:) *({specifier_set})",
            "(?<={package_name})({specifier_set})",
        ],
        files_to_pattern=AEA_PATHS,
    )
    return aea_version_bumper


def make_plugin_bumper(
    plugin_dir: Path, new_version: Version
) -> PythonPackageVersionBumper:
    """Build the plugin Python package version bumper."""
    plugin_package_dir = plugin_dir / plugin_dir.name.replace("-", "_")
    plugin_version_bumper = PythonPackageVersionBumper(
        ROOT_DIR,
        plugin_package_dir,
        new_version,
        files_to_pattern={},
        specifier_set_patterns=[
            YAML_DEPENDENCY_SPECIFIER_SET_PATTERN,
            JSON_DEPENDENCY_SPECIFIER_SET_PATTERN,
        ],
        package_name=plugin_dir.name,
    )
    return plugin_version_bumper


def process_plugins(new_versions: Dict[str, Version]) -> bool:
    """Process plugins."""
    result = False
    for plugin_dir in ALL_PLUGINS:
        plugin_dir_name = plugin_dir.name
        if plugin_dir_name not in new_versions:
            logging.info(
                f"Skipping {plugin_dir_name} as it is not specified in input {new_versions}"
            )
            continue
        new_version = new_versions[plugin_dir_name]
        logging.info(
            f"Processing {plugin_dir_name}: upgrading at version {new_version}"
        )
        plugin_bumper = make_plugin_bumper(plugin_dir, new_version)
        plugin_bumper.run()
        result |= plugin_bumper.result
    return result


def parse_plugin_versions(key_value_strings: List[str]) -> Dict[str, Version]:
    """Parse plugin versions."""
    return {
        plugin_name: Version(version)
        for plugin_name, version in map(
            operator.methodcaller("split", "="), key_value_strings
        )
    }


def only_check_bump_needed() -> int:
    """
    Check whether a version bump is needed for AEA and plugins.

    :return: the return code
    """
    bumpers: List[PythonPackageVersionBumper] = list()
    to_upgrade: List[Path] = list()
    bumpers.append(make_aea_bumper(None))  # type: ignore
    for plugin_dir in ALL_PLUGINS:
        bumpers.append(make_plugin_bumper(plugin_dir, None))  # type: ignore

    latest_tag = str(bumpers[0].repo.tags[-1])
    logging.info(
        f"Checking packages that have changes from tag {latest_tag} and that require a new release..."
    )
    for bumper in bumpers:
        if bumper.is_different_from_latest_tag():
            logging.info(
                f"Package {bumper.python_pkg_dir} is different from latest tag {latest_tag}."
            )
            to_upgrade.append(bumper.python_pkg_dir)

    if len(to_upgrade) > 0:
        logging.info("Packages to upgrade:")
        for path in to_upgrade:
            logging.info(path)
    else:
        logging.info("No packages to upgrade.")
    return 0


def bump(arguments: argparse.Namespace) -> int:
    """
    Bump versions.

    :param arguments: arguments from argparse
    :return: the return code
    """
    new_plugin_versions = parse_plugin_versions(arguments.plugin_new_version)
    logging.info(f"Parsed arguments: {arguments}")
    logging.info(f"Parsed plugin versions: {new_plugin_versions}")

    have_updated_specifier_set = False
    if arguments.new_version is not None:
        new_aea_version = Version(arguments.new_version)
        aea_version_bumper = make_aea_bumper(new_aea_version)
        aea_version_bumper.run()
        have_updated_specifier_set = aea_version_bumper.result
        logging.info("AEA package processed.")
    else:
        logging.info("AEA package not processed - no version provided.")

    logging.info("Processing plugins:")
    have_updated_specifier_set |= process_plugins(new_plugin_versions)

    logging.info("OK")
    return_code = 0
    if arguments.no_fingerprints:
        logging.info(
            "Not updating fingerprints, since --no-fingerprints was specified."
        )
    elif have_updated_specifier_set is False:
        logging.info(
            "Not updating fingerprints, since no specifier set has been updated."
        )
    else:
        logging.info("Updating hashes and fingerprints.")
        return_code = update_hashes()
    return return_code


def main() -> None:
    """Run the script."""
    repo = Repo(str(ROOT_DIR))
    if repo.is_dirty():
        logging.info(
            "Repository is dirty. Please clean it up before running this script."
        )
        sys.exit(1)

    arguments = parse_args()
    if arguments.only_check:
        sys.exit(only_check_bump_needed())

    return_code = bump(arguments)
    sys.exit(return_code)


if __name__ == "__main__":
    main()
