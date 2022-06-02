#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
Check that package ids are in sync with the current packages.

Run this script from the root of the project directory:

    python scripts/check_package_versions_in_docs.py

"""
import re
import sys
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Match, Pattern, Set

import yaml

from aea.configurations.base import ComponentType, PackageId, PackageType, PublicId
from aea.configurations.constants import (
    AGENTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)


PUBLIC_ID_REGEX = PublicId.PUBLIC_ID_REGEX[1:-1]
"""This regex removes the '^' and '$' respectively, at the beginning and at the end."""

ADD_COMMAND_IN_DOCS = re.compile(
    "aea +add +({}) +({})".format("|".join(map(str, ComponentType)), PUBLIC_ID_REGEX)
)
"""
This regex matches strings of the form:

  aea add (protocol|connection|contract|skill) some_author/some_package:some_version_number

"""


FETCH_COMMAND_IN_DOCS = re.compile("aea +fetch +({})".format(PUBLIC_ID_REGEX))
"""
This regex matches strings of the form:

  aea fetch some_author/some_package:some_version_number

"""


class PackageIdNotFound(Exception):
    """Custom exception for package id not found."""

    def __init__(
        self, file: Path, package_id: PackageId, match_obj: Any, *args: Any
    ) -> None:
        """
        Initialize PackageIdNotFound exception.

        :param file: path to the file checked.
        :param package_id: package id not found.
        :param match_obj: re.Match object.
        :param args: super class args.
        """
        super().__init__(*args)
        self.file = file
        self.package_id = package_id
        self.match_obj = match_obj


DEFAULT_CONFIG_FILE_PATHS = []  # type: List[Path]


CONFIG_FILE_NAMES = [
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
]  # type: List[str]


def default_config_file_paths() -> Generator:
    """Get (generator) the default config file paths."""
    for item in DEFAULT_CONFIG_FILE_PATHS:
        yield item


def unified_yaml_load(configuration_file: Path) -> Dict:
    """
    Load YAML file, unified (both single- and multi-paged).

    :param configuration_file: the configuration file path.
    :return: the data.
    """
    package_type = configuration_file.parent.parent.name
    with configuration_file.open() as fp:
        if package_type != AGENTS:
            return yaml.safe_load(fp)
        # when it is an agent configuration file,
        # we are interested only in the first page of the YAML,
        # because the dependencies are contained only there.
        data = yaml.safe_load_all(fp)
        return list(data)[0]


def get_public_id_from_yaml(configuration_file: Path) -> PublicId:
    """
    Get the public id from yaml.

    :param configuration_file: the path to the config yaml
    :return: public id
    """
    data = unified_yaml_load(configuration_file)
    author = data.get("author", None)
    if not author:
        raise KeyError(f"No author field in {str(configuration_file)}")
    # handle the case when it's a package or agent config file.
    try:
        name = data["name"] if "name" in data else data["agent_name"]
    except KeyError:
        print(f"No name or agent_name field in {str(configuration_file)}")
        raise
    version = data.get("version", None)
    if not version:
        raise KeyError(f"No version field in {str(configuration_file)}")
    return PublicId(author, name, version)


def find_all_packages_ids() -> Set[PackageId]:
    """Find all packages ids."""
    package_ids: Set[PackageId] = set()
    packages_dir = Path("packages")
    config_files = [
        path
        for path in packages_dir.glob("*/*/*/*.yaml")
        if any([file in str(path) for file in CONFIG_FILE_NAMES])
    ]
    for configuration_file in chain(config_files, default_config_file_paths()):
        package_type = PackageType(configuration_file.parts[-3][:-1])
        package_public_id = get_public_id_from_yaml(configuration_file)
        package_id = PackageId(package_type, package_public_id)
        package_ids.add(package_id)

    return package_ids


ALL_PACKAGE_IDS: Set[PackageId] = find_all_packages_ids()


def _checks(
    file: Path,
    regex: Pattern,
    extract_package_id_from_match: Callable[["re.Match"], PackageId],
) -> None:
    matches = regex.finditer(file.read_text())
    for match in matches:
        package_id = extract_package_id_from_match(match)
        if package_id.without_hash() not in ALL_PACKAGE_IDS:
            raise PackageIdNotFound(
                file, package_id, match, "Package {} not found.".format(package_id)
            )
        print(str(package_id), "OK!")


def check_add_commands(file: Path) -> None:
    """
    Check that 'aea add' commands of the documentation file contains known package ids.

    :param file: path to the file.
    """

    def extract_package_id(match: Match) -> PackageId:
        package_type, package = match.group(1), match.group(2)
        package_id = PackageId(PackageType(package_type), PublicId.from_str(package))
        return package_id

    _checks(file, ADD_COMMAND_IN_DOCS, extract_package_id)


def check_fetch_commands(file: Path) -> None:
    """
    Check that 'aea fetch' commands of the documentation file contains known package ids.

    :param file: path to the file.
    """

    def extract_package_id(match: Match) -> PackageId:
        package_public_id = match.group(1)
        package_id = PackageId(PackageType.AGENT, PublicId.from_str(package_public_id))
        return package_id

    _checks(file, FETCH_COMMAND_IN_DOCS, extract_package_id)


def check_file(file: Path) -> None:
    """
    Check documentation file.

    :param file: path to the file to check.
    """
    check_add_commands(file)
    check_fetch_commands(file)


def handle_package_not_found(e: PackageIdNotFound) -> None:
    """Handle PackageIdNotFound errors."""
    print("=" * 50)
    print("Package {} not found.".format(e.package_id))
    print("Path to file: ", e.file)
    print("Span: ", e.match_obj.span(0))
    print("Full Match: ", e.match_obj.group(0))
    sys.exit(1)


if __name__ == "__main__":
    docs_files = Path("docs").glob("**/*.md")

    try:
        for file_ in docs_files:
            print("Processing " + str(file_))
            check_file(file_)
    except PackageIdNotFound as e_:
        handle_package_not_found(e_)
        sys.exit(1)

    print("Done!")
    sys.exit(0)
