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
"""Implementation of the 'aea add' subcommand."""
import os
from pathlib import Path
from typing import Dict, Union, cast

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.configurations.base import (
    PublicId,
    _compute_fingerprint,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import (  # noqa: F401 # pylint: disable=unused-import
    CONFIG_FILE_TO_PACKAGE_TYPE,
    CONNECTION,
    CONTRACT,
    DEFAULT_IGNORE_DIRS_AGENT_FINGERPRINT,
    PROTOCOL,
    SKILL,
)
from aea.configurations.data_types import PackageType
from aea.configurations.loader import ConfigLoader
from aea.helpers.io import open_file


@click.group(invoke_without_command=True)
@click.pass_context
def fingerprint(click_context: click.core.Context,) -> None:
    """Fingerprint a non-vendor package of the agent."""
    if click_context.invoked_subcommand is None:
        fingerprint_agent(click_context)


@fingerprint.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId) -> None:
    """Fingerprint a connection and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, CONNECTION, connection_public_id)


@fingerprint.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId) -> None:
    """Fingerprint a contract and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, CONTRACT, contract_public_id)


@fingerprint.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id: PublicId) -> None:
    """Fingerprint a protocol and add the fingerprints to the configuration file.."""
    fingerprint_item(ctx, PROTOCOL, protocol_public_id)


@fingerprint.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId) -> None:
    """Fingerprint a skill and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, SKILL, skill_public_id)


@fingerprint.command()
@click.argument("path", type=str, required=True)
@pass_ctx
def by_path(ctx: Context, path: str) -> None:
    """Fingerprint a package by its path."""
    try:
        click.echo("Fingerprinting component in '{}' ...".format(path))
        full_path = Path(ctx.cwd) / Path(path)
        fingerprint_package_by_path(full_path)
    except Exception as e:
        raise click.ClickException(str(e))


def fingerprint_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Fingerprint components of an item.

    :param ctx: the context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    """
    item_type_plural = item_type + "s"

    click.echo(
        "Fingerprinting {} components of '{}' ...".format(item_type, item_public_id)
    )

    # create fingerprints
    package_dir = Path(ctx.cwd, item_type_plural, item_public_id.name)
    try:
        fingerprint_package(package_dir, item_type)
    except Exception as e:
        raise click.ClickException(str(e))


def fingerprint_package_by_path(package_dir: Path) -> None:
    """
    Fingerprint package placed in package_dir.

    :param package_dir: directory of the package
    """
    package_type = determine_package_type_for_directory(package_dir)
    fingerprint_package(package_dir, package_type)


def determine_package_type_for_directory(package_dir: Path) -> PackageType:
    """
    Find package type for the package directory by checking config file names.

    :param package_dir: package dir to determine package type:

    :return: PackageType
    """
    config_files = list(
        set(os.listdir(str(package_dir))).intersection(
            set(CONFIG_FILE_TO_PACKAGE_TYPE.keys())
        )
    )

    if len(config_files) > 1:
        raise ValueError(
            f"Too many config files in the directory, only one has to present!: {', '.join(config_files)}"
        )
    if len(config_files) == 0:
        raise ValueError(
            f"No package config file found in `{str(package_dir)}`. Incorrect directory?"
        )

    config_file = config_files[0]
    package_type = PackageType(CONFIG_FILE_TO_PACKAGE_TYPE[config_file])

    return package_type


def fingerprint_package(
    package_dir: Path, package_type: Union[str, PackageType]
) -> None:
    """
    Fingerprint components of an item.

    :param package_dir: the package directory.
    :param package_type: the package type.
    """
    package_type = PackageType(package_type)
    item_type = str(package_type)
    default_config_file_name = _get_default_configuration_file_name_from_type(item_type)
    config_loader = ConfigLoader.from_configuration_type(item_type)
    config_file_path = Path(package_dir, default_config_file_name)
    config = config_loader.load(open_file(config_file_path))

    if not package_dir.exists():
        # we only permit non-vendorized packages to be fingerprinted
        raise ValueError("Package not found at path {}".format(package_dir))

    fingerprints_dict = _compute_fingerprint(
        package_dir, ignore_patterns=config.fingerprint_ignore_patterns
    )  # type: Dict[str, str]

    # Load item specification yaml file and add fingerprints
    config.fingerprint = fingerprints_dict
    config_loader.dump(config, open_file(config_file_path, "w"))


@check_aea_project(check_finger_prints=False)  # pylint: disable=no-value-for-parameter
def fingerprint_agent(click_context: click.Context) -> None:
    """Do a fingerprint for an agent."""
    ctx = cast(Context, click_context.obj)
    click.echo(
        f"Fingerprinting files in agent project '{ctx.agent_config.agent_name}'..."
    )
    fingerprints_dict = _compute_fingerprint(
        Path(ctx.cwd),
        ignore_patterns=ctx.agent_config.fingerprint_ignore_patterns,
        ignore_directories=DEFAULT_IGNORE_DIRS_AGENT_FINGERPRINT,
    )  # type: Dict[str, str]
    ctx.agent_config.fingerprint = fingerprints_dict
    ctx.dump_agent_config()
    click.echo(f"Fingerprint for agent `{ctx.agent_config.name}` calculated!")
