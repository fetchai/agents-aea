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
"""Run different checks on AEA packages."""

import pprint
import sys
from abc import abstractmethod
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Set

import click
import yaml

from aea.configurations.base import PackageId, PackageType, PublicId
from aea.configurations.constants import (
    AGENTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)


CONFIG_FILE_NAMES = [
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
]  # type: List[str]


class CustomException(Exception):
    """A custom exception class for this script."""

    @abstractmethod
    def print_error(self) -> None:
        """Print the error message."""


class DependencyNotFound(CustomException):
    """Custom exception for dependencies not found."""

    def __init__(
        self,
        configuration_file: Path,
        expected_deps: Set[PackageId],
        missing_dependencies: Set[PackageId],
        *args: Any,
    ) -> None:
        """
        Initialize DependencyNotFound exception.

        :param configuration_file: path to the checked file.
        :param expected_deps: expected dependencies.
        :param missing_dependencies: missing dependencies.
        :param args: super class args.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file
        self.expected_dependencies = expected_deps
        self.missing_dependencies = missing_dependencies

    def print_error(self) -> None:
        """Print the error message."""
        sorted_expected = list(map(str, sorted(self.expected_dependencies)))
        sorted_missing = list(map(str, sorted(self.missing_dependencies)))
        print("=" * 50)
        print(f"Package {self.configuration_file}:")
        print(f"Expected: {pprint.pformat(sorted_expected)}")
        print(f"Missing: {pprint.pformat(sorted_missing)}")
        print("=" * 50)


class EmptyPackageDescription(CustomException):
    """Custom exception for empty description field."""

    def __init__(
        self,
        configuration_file: Path,
        *args: Any,
    ) -> None:
        """
        Initialize EmptyPackageDescription exception.

        :param configuration_file: path to the checked file.
        :param args: super class args.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(f"Package '{self.configuration_file}' has empty description field.")
        print("=" * 50)


class UnexpectedAuthorError(CustomException):
    """Custom exception for unexpected author value."""

    def __init__(
        self,
        configuration_file: Path,
        expected_author: str,
        actual_author: str,
        *args: Any,
    ):
        """
        Initialize the exception.

        :param configuration_file: the file to the configuration that raised the error.
        :param expected_author: the expected author.
        :param actual_author: the actual author.
        :param args: other positional arguments.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file
        self.expected_author = expected_author
        self.actual_author = actual_author

    def print_error(self) -> None:
        """Print the error message."""
        print("=" * 50)
        print(
            f"Package '{self.configuration_file}' has an unexpected author value: "
            f"expected {self.expected_author}, found '{self.actual_author}'."
        )
        print("=" * 50)


def find_all_configuration_files(packages_dir: Path) -> List:
    """Find all configuration files."""
    config_files = [
        path
        for path in packages_dir.glob("*/*/*/*.yaml")
        if any([file in str(path) for file in CONFIG_FILE_NAMES])
    ]
    return config_files


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
        click.echo(f"No name or agent_name field in {str(configuration_file)}")
        raise
    version = data.get("version", None)
    if not version:
        raise KeyError(f"No version field in {str(configuration_file)}")
    return PublicId(author, name, version)


def find_all_packages_ids(packages_dir: Path) -> Set[PackageId]:
    """Find all packages ids."""
    package_ids: Set[PackageId] = set()
    for configuration_file in find_all_configuration_files(packages_dir):
        package_type = PackageType(configuration_file.parts[-3][:-1])
        package_public_id = get_public_id_from_yaml(configuration_file)
        package_id = PackageId(package_type, package_public_id)
        package_ids.add(package_id)

    return package_ids


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


def check_dependencies(
    configuration_file: Path, all_packages_ids: Set[PackageId]
) -> None:
    """
    Check dependencies of configuration file.

    :param configuration_file: path to a package configuration file.
    :param all_packages_ids: all the package ids.
    """
    data = unified_yaml_load(configuration_file)

    def _add_package_type(package_type: PackageType, public_id_str: str) -> PackageId:
        return PackageId(package_type, PublicId.from_str(public_id_str))

    def _get_package_ids(
        package_type: PackageType, public_ids: Set[PublicId]
    ) -> Set[PackageId]:
        return set(map(partial(_add_package_type, package_type), public_ids))

    dependencies: Set[PackageId] = set.union(
        *[
            _get_package_ids(package_type, data.get(package_type.to_plural(), set()))
            for package_type in list(PackageType)
        ]
    )

    diff = dependencies.difference(all_packages_ids)
    if len(diff) > 0:
        raise DependencyNotFound(configuration_file, dependencies, diff)


def check_description(configuration_file: Path) -> None:
    """Check description field of a package is non-empty."""
    yaml_object = unified_yaml_load(configuration_file)
    description = yaml_object.get("description")
    if description == "":
        raise EmptyPackageDescription(configuration_file)


def check_author(configuration_file: Path, expected_author: str) -> None:
    """Check the author matches a certain desired value."""
    yaml_object = unified_yaml_load(configuration_file)
    actual_author = yaml_object.get("author", "")
    if actual_author != expected_author:
        raise UnexpectedAuthorError(configuration_file, expected_author, actual_author)


@click.command(name="check-packages")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=Path.cwd() / "packages",
)
def check_packages(packages_dir: Path) -> None:
    """
    Run different checks on AEA packages.

    Namely:
    - Check that every package has existing dependencies
    - Check that every package has non-empty description

    :param packages_dir: Path to packages dir.
    """
    packages_dir = Path(packages_dir).absolute()
    all_packages_ids_ = find_all_packages_ids(packages_dir)
    failed: bool = False

    for file in find_all_configuration_files(packages_dir):
        try:
            expected_author = file.parent.parent.parent.name
            click.echo("Processing " + str(file))
            check_author(file, expected_author)
            check_dependencies(file, all_packages_ids_)
            check_description(file)
        except CustomException as exception:
            exception.print_error()
            failed = True

    if failed:
        click.echo("Failed!")
        sys.exit(1)
    else:
        click.echo("OK!")
        sys.exit(0)
