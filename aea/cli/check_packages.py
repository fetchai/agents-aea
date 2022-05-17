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

import importlib
import pprint
import sys
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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


class DependencyNotFound(Exception):
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


class EmptyPackageDescription(Exception):
    """Custom exception for empty description field."""

    def __init__(self, configuration_file: Path, *args: Any,) -> None:
        """
        Initialize EmptyPackageDescription exception.

        :param configuration_file: path to the checked file.
        :param args: super class args.
        """
        super().__init__(*args)
        self.configuration_file = configuration_file


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


def handle_dependency_not_found(e: DependencyNotFound) -> None:
    """Handle PackageIdNotFound errors."""
    sorted_expected = list(map(str, sorted(e.expected_dependencies)))
    sorted_missing = list(map(str, sorted(e.missing_dependencies)))
    click.echo("=" * 50)
    click.echo(f"Package {e.configuration_file}:")
    click.echo(f"Expected: {pprint.pformat(sorted_expected)}")
    click.echo(f"Missing: {pprint.pformat(sorted_missing)}")
    click.echo("=" * 50)


def handle_empty_package_description(e: EmptyPackageDescription) -> None:
    """Handle EmptyPackageDescription errors."""
    click.echo("=" * 50)
    click.echo(f"Package '{e.configuration_file}' has empty description field.")
    click.echo("=" * 50)


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


def check_handlers(config_file: Path, handler_config: Any) -> None:
    """Check handlers"""

    if config_file.absolute().parent in handler_config.SKIP_SKILLS:
        return

    handler_file_path = (config_file.parent / "handlers.py").relative_to(Path.cwd())
    module_name = str(handler_file_path).replace(".py", "").replace("/", ".")
    skill_name = module_name.split(".")[-2]

    try:
        module = importlib.import_module(module_name)
        module_attributes = dir(module)
    except ModuleNotFoundError as exc:
        raise FileNotFoundError(f"Handler file {module_name} does not exist") from exc

    with open(str(config_file), mode="r", encoding="utf-8") as fp:
        config = yaml.safe_load(fp)
        if skill_name not in handler_config.SKIP_HANDLERS:
            for common_handler in handler_config.COMMON_HANDLERS:
                if common_handler not in config["handlers"].keys():
                    raise ValueError(
                        f"Common handler '{common_handler}' is not defined in {config_file}"
                    )

        for handler_info in config["handlers"].values():
            if handler_info["class_name"] not in module_attributes:
                raise ValueError(
                    f"Handler {handler_info['class_name']} declared in {config_file} is missing from {handler_file_path}"
                )


def is_skill(file: Path) -> bool:
    """Check if a file is a skill config."""
    return file.name.endswith(DEFAULT_SKILL_CONFIG_FILE)


@click.command(name="check-packages")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=Path.cwd() / "packages",
)
@click.option(
    "--handler-config",
    type=click.Path(dir_okay=True, exists=True),
    default=Path.cwd() / "scripts" / "handler_config.py",
)
@click.option(
    "--abci-consistency", type=bool, is_flag=True, help="Check ABCI app consistency."
)
def check_packages(
    packages_dir: Path, abci_consistency: bool, handler_config: Path
) -> None:
    """
    Run different checks on AEA packages.

    Namely:
    - Check that every package has existing dependencies
    - Check that every package has non-empty description

    :param packages_dir: Path to packages dir.
    :param abci_consistency: Check abci app consistency
    :param handler_config: Path to handler config file.
    """
    handler_config_module: Optional[Any] = None
    packages_dir = Path(packages_dir).absolute()
    all_packages_ids_ = find_all_packages_ids(packages_dir)
    failed: bool = False

    if abci_consistency:
        handler_config_file = Path(handler_config).relative_to(Path.cwd())
        module_name = str(handler_config_file).replace(".py", "").replace("/", ".")
        handler_config_module = importlib.import_module(module_name)

    for file in find_all_configuration_files(packages_dir):
        try:
            click.echo("Processing " + str(file))
            check_dependencies(file, all_packages_ids_)
            check_description(file)
            if abci_consistency and is_skill(file):
                check_handlers(file, handler_config_module)
        except DependencyNotFound as e_:
            handle_dependency_not_found(e_)
            failed = True
        except EmptyPackageDescription as e_:
            handle_empty_package_description(e_)
            failed = True

    if failed:
        click.echo("Failed!")
        sys.exit(1)
    else:
        click.echo("OK!")
        sys.exit(0)
