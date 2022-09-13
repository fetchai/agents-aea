# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
This script generates the IPFS hashes for all packages.

This script requires that you have IPFS installed:
- https://docs.ipfs.io/guides/guides/install/
"""

import sys
import traceback
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple, cast

import click

from aea.configurations.base import PackageConfiguration, PackageType
from aea.configurations.constants import (
    AGENT,
    PACKAGE_TYPE_TO_CONFIG_FILE,
    SCAFFOLD_PACKAGES,
    SCAFFOLD_PUBLIC_ID,
)
from aea.configurations.data_types import PackageId, PublicId
from aea.configurations.loader import load_configuration_object
from aea.helpers.cid import DEFAULT_ENCODING, to_v0, to_v1
from aea.helpers.dependency_tree import DependencyTree, dump_yaml, load_yaml, to_plural
from aea.helpers.fingerprint import update_fingerprint
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all


def to_package_id(package_path: Path) -> Tuple[PackageId, Path]:
    """Extract the package type from the path."""
    item_type_plural = package_path.parent.name
    item_type_singular = item_type_plural[:-1]
    return (
        PackageId(
            PackageType(item_type_singular), PublicId.from_str(SCAFFOLD_PUBLIC_ID)
        ),
        package_path,
    )


def package_id_and_path(
    package_id: PackageId, packages_dir: Path
) -> Tuple[PackageId, Path]:
    """Extract the package type from the path."""
    package_path = (
        packages_dir
        / package_id.author
        / package_id.package_type.to_plural()
        / package_id.name
    )

    return package_id, package_path


def sort_configuration_file(config: PackageConfiguration) -> None:
    """Sort the order of the fields in the configuration files."""
    # load config file to get ignore patterns, dump again immediately to impose ordering
    if config.directory is None:
        raise ValueError("config.directory cannot be None.")

    configuration_filepath = config.directory / config.default_configuration_filename
    if config.package_type == PackageType.AGENT:
        json_data = config.ordered_json
        component_configurations = json_data.pop("component_configurations")
        yaml_dump_all(
            [json_data] + component_configurations, configuration_filepath.open("w")
        )
    elif config.package_type == PackageType.SERVICE:
        json_data = config.ordered_json
        overrides = json_data.pop("overrides")
        yaml_dump_all([json_data, *overrides], configuration_filepath.open("w"))
    else:
        yaml_dump(config.ordered_json, configuration_filepath.open("w"))


def hash_package(
    configuration: PackageConfiguration,
    package_type: PackageType,
    no_wrap: bool = False,
) -> Tuple[str, str]:
    """
    Hashes a package and its components.

    :param configuration: the package configuration.
    :param package_type: the package type.
    :param no_wrap: Whether to use the wrapper node or not.
    :return: the identifier of the hash (e.g. 'fetchai/protocols/default')
           | and the hash of the whole package.
    """
    # hash again to get outer hash (this time all files)
    # we still need to ignore some files
    #      use ignore patterns somehow
    # ignore_patterns = configuration.fingerprint_ignore_patterns # noqa: E800
    if configuration.directory is None:
        raise ValueError("configuration.directory cannot be None.")

    key = "/".join(
        [
            configuration.author,
            package_type.to_plural(),
            configuration.directory.name,
        ]
    )
    package_hash = IPFSHashOnly.hash_directory(
        str(configuration.directory), wrap=(not no_wrap)
    )

    return key, package_hash


def load_configuration(
    package_type: PackageType, package_path: Path
) -> PackageConfiguration:
    """
    Load a configuration, knowing the type and the path to the package root.

    :param package_type: the package type.
    :param package_path: the path to the package root.
    :return: the configuration object.
    """
    configuration_obj = load_configuration_object(package_type, package_path)
    configuration_obj._directory = package_path  # pylint: disable=protected-access
    return cast(PackageConfiguration, configuration_obj)


def update_public_id_hash(
    public_id_str: str,
    package_type: str,
    public_id_to_hash_mappings: Dict[PackageId, str],
) -> str:
    """Update hash for given public from available mappings."""
    public_id = PublicId.from_str(public_id_str).without_hash()
    package_id = PackageId(PackageType(package_type), public_id)
    return str(
        PublicId.from_json(
            {
                **public_id.json,
                "package_hash": cast(str, public_id_to_hash_mappings.get(package_id)),
            }
        )
    )


def extend_public_ids(
    item_config: Dict, public_id_to_hash_mappings: Dict[PackageId, str]
) -> None:
    """Extend public id with hashes for given item config."""
    for component_type in PACKAGE_TYPE_TO_CONFIG_FILE:
        if component_type == AGENT:
            continue

        components = to_plural(component_type)
        if components in item_config:
            item_config[components] = [
                update_public_id_hash(d, component_type, public_id_to_hash_mappings)
                for d in item_config.get(components, [])
            ]


def update_hashes(
    packages_dir: Path,
    no_wrap: bool = False,
    vendor: Optional[str] = None,
    config_loader: Callable[
        [PackageType, Path], PackageConfiguration
    ] = load_configuration,
) -> int:
    """Process all AEA packages and update fingerprint."""
    return_code = 0
    package_hashes: Dict[str, str] = {}

    try:
        public_id_to_hash_mappings: Dict = {}
        dependency_tree = DependencyTree.generate(packages_dir)
        packages = [
            [package_id_and_path(package_id, packages_dir) for package_id in tree_level]
            for tree_level in dependency_tree
        ]
        packages[0] = packages[0] + list(map(to_package_id, SCAFFOLD_PACKAGES))
        for tree_level in packages:
            for package_id, package_path in tree_level:
                click.echo(
                    "Processing package {} of type {}".format(
                        package_path.name, package_id.package_type
                    )
                )

                config_file = package_path / cast(
                    str, PACKAGE_TYPE_TO_CONFIG_FILE.get(package_id.package_type.value)
                )
                item_config, extra_config = load_yaml(config_file)
                extend_public_ids(item_config, public_id_to_hash_mappings)
                dump_yaml(config_file, item_config, extra_config)

                configuration_obj = config_loader(package_id.package_type, package_path)
                sort_configuration_file(configuration_obj)
                update_fingerprint(configuration_obj)
                key, package_hash = hash_package(
                    configuration_obj, package_id.package_type, no_wrap=no_wrap
                )
                public_id_to_hash_mappings[package_id] = package_hash

                if vendor is not None and package_id.author != vendor:
                    continue
                package_hashes[key] = package_hash
        click.echo("Done!")
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()
        return_code = 1

    return return_code


@click.group(name="hash")
def hash_group() -> None:
    """Hashing utils."""


@hash_group.command(name="all")
@click.option(
    "--packages-dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=Path("packages/"),
)
@click.option("--vendor", type=str)
@click.option("--no-wrap", is_flag=True)
def generate_all(
    packages_dir: Path,
    vendor: Optional[str],
    no_wrap: bool,
) -> None:
    """Generate IPFS hashes."""
    packages_dir = Path(packages_dir).absolute()
    return_code = update_hashes(packages_dir, no_wrap, vendor=vendor)
    sys.exit(return_code)


@hash_group.command(name="one")
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option("--no-wrap", is_flag=True)
def hash_file(path: str, no_wrap: bool) -> None:
    """Hash a single file/directory."""

    click.echo(f"Path : {path}")
    click.echo(f"Hash : {IPFSHashOnly.get(path, wrap=not no_wrap)}")


@hash_group.command(name="to-v0")
@click.argument("hash_string")
def to_v0_string(hash_string: str) -> None:
    """Convert hash to CID v0."""
    try:
        v0_hash = to_v0(hash_string)
        click.echo(v0_hash)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@hash_group.command(name="to-v1")
@click.argument("hash_string")
@click.option("--encoding", type=str, default=DEFAULT_ENCODING)
def to_v1_string(hash_string: str, encoding: str) -> None:
    """Convert hash to CID v1."""
    try:
        v1_hash = to_v1(hash_string, encoding)
        click.echo(v1_hash)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e
