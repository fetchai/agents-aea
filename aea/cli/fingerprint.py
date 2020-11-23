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
from pathlib import Path
from typing import Dict

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.base import (
    PublicId,
    _compute_fingerprint,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import (  # noqa: F401 # pylint: disable=unused-import
    CONNECTION,
    CONTRACT,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.configurations.loader import ConfigLoader


@click.group()
@click.pass_context
def fingerprint(click_context: click.core.Context):  # pylint: disable=unused-argument
    """Fingerprint a non-vendor package of the agent."""


@fingerprint.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId):
    """Fingerprint a connection and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, CONNECTION, connection_public_id)


@fingerprint.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId):
    """Fingerprint a contract and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, CONTRACT, contract_public_id)


@fingerprint.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id: PublicId):
    """Fingerprint a protocol and add the fingerprints to the configuration file.."""
    fingerprint_item(ctx, PROTOCOL, protocol_public_id)


@fingerprint.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId):
    """Fingerprint a skill and add the fingerprints to the configuration file."""
    fingerprint_item(ctx, SKILL, skill_public_id)


def fingerprint_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Fingerprint components of an item.

    :param ctx: the context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    item_type_plural = item_type + "s"

    click.echo(
        "Fingerprinting {} components of '{}' ...".format(item_type, item_public_id)
    )

    # create fingerprints
    package_dir = Path(ctx.cwd, item_type_plural, item_public_id.name)
    try:
        default_config_file_name = _get_default_configuration_file_name_from_type(
            item_type
        )
        config_loader = ConfigLoader.from_configuration_type(item_type)
        config_file_path = Path(package_dir, default_config_file_name)
        config = config_loader.load(config_file_path.open())

        if not package_dir.exists():
            # we only permit non-vendorized packages to be fingerprinted
            raise click.ClickException(
                "Package not found at path {}".format(package_dir)
            )

        fingerprints_dict = _compute_fingerprint(
            package_dir, ignore_patterns=config.fingerprint_ignore_patterns
        )  # type: Dict[str, str]

        # Load item specification yaml file and add fingerprints
        config.fingerprint = fingerprints_dict
        config_loader.dump(config, open(config_file_path, "w"))
    except Exception as e:
        raise click.ClickException(str(e))
