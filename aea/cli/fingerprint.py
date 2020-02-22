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
import sys
from pathlib import Path
from typing import Dict, cast

import click
from click import pass_context

from aea.cli.common import (
    Context,
    PublicIdParameter,
    logger,
    pass_ctx,
    try_to_load_agent_config,
)
from aea.configurations.base import (  # noqa: F401
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.configurations.base import (
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.loader import ConfigLoader
from aea.helpers.ipfs.base import IPFSHashOnly


@click.group()
@pass_ctx
def fingerprint(ctx: Context):
    """Fingerprint a resource."""
    try_to_load_agent_config(ctx)


def _fingerprint_item(click_context, item_type, item_public_id) -> None:
    """
    Fingerprint components of an item.

    :param click_context: the click context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    ctx = cast(Context, click_context.obj)
    item_type_plural = item_type + "s"
    ipfs_hash_only = IPFSHashOnly()

    click.echo(
        "Fingerprinting {} components of '{}' ...".format(item_type, item_public_id)
    )

    # create fingerprints
    fingerprints_dict = {}  # type: Dict[str, str]
    package_dir = Path(ctx.cwd, item_type_plural, item_public_id.name)
    if not package_dir.exists():
        # we only permit non-vendorized packages to be fingerprinted
        logger.error("Package not found at path {}".format(package_dir))
        sys.exit(1)

    for file in os.listdir(package_dir):
        if file.endswith(".py"):
            file_path = os.path.join(package_dir, file)
            ipfs_hash = ipfs_hash_only.get(file_path)
            fingerprints_dict[file] = ipfs_hash

    # Load item specification yaml file and add fingerprints
    try:
        default_config_file_name = _get_default_configuration_file_name_from_type(
            item_type
        )
        config_loader = ConfigLoader.from_configuration_type(item_type)
        config_file_path = Path(package_dir, default_config_file_name)
        config = config_loader.load(config_file_path.open())
        config.fingerprint = fingerprints_dict
        config_loader.dump(config, open(config_file_path, "w"))
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


@fingerprint.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_context
def connection(click_context, connection_public_id: PublicId):
    """Fingerprint a connection and add the fingerprints to the configuration file."""
    _fingerprint_item(click_context, "connection", connection_public_id)


@fingerprint.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_context
def protocol(click_context, protocol_public_id):
    """Fingerprint a protocol and add the fingerprints to the configuration file.."""
    _fingerprint_item(click_context, "protocol", protocol_public_id)


@fingerprint.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_context
def skill(click_context, skill_public_id: PublicId):
    """Fingerprint a skill and add the fingerprints to the configuration file."""
    _fingerprint_item(click_context, "skill", skill_public_id)
