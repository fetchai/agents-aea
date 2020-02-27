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

"""Implementation of the 'aea list' subcommand."""

from collections.abc import Set
from pathlib import Path
from typing import Dict, List

import click

from aea.cli.common import (
    Context,
    format_items,
    pass_ctx,
    retrieve_details,
    try_to_load_agent_config,
)
from aea.configurations.base import (
    ConfigurationType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.loader import ConfigLoader


@click.group()
@pass_ctx
def list(ctx: Context):
    """List the installed resources."""
    try_to_load_agent_config(ctx)


def _get_item_details(ctx, item_type) -> List[Dict]:
    """Return a list of item details, given the item type."""
    result = []
    item_type_plural = item_type + "s"
    public_ids = getattr(ctx.agent_config, item_type_plural)  # type: Set[PublicId]
    default_file_name = _get_default_configuration_file_name_from_type(item_type)
    for public_id in public_ids:
        # first, try to retrieve the item from the vendor directory.
        configuration_filepath = Path(
            ctx.cwd,
            "vendor",
            public_id.author,
            item_type_plural,
            public_id.name,
            default_file_name,
        )
        # otherwise, if it does not exist, retrieve the item from the agent custom packages
        if not configuration_filepath.exists():
            configuration_filepath = Path(
                ctx.cwd, item_type_plural, public_id.name, default_file_name
            )
        configuration_loader = ConfigLoader.from_configuration_type(
            ConfigurationType(item_type)
        )
        details = retrieve_details(
            public_id.name, configuration_loader, str(configuration_filepath)
        )
        result.append(details)
    return result


@list.command()
@pass_ctx
def connections(ctx: Context):
    """List all the installed connections."""
    result = _get_item_details(ctx, "connection")
    print(format_items(sorted(result, key=lambda k: k["name"])))


@list.command()
@pass_ctx
def contracts(ctx: Context):
    """List all the installed protocols."""
    result = _get_item_details(ctx, "contract")
    print(format_items(sorted(result, key=lambda k: k["name"])))


@list.command()
@pass_ctx
def protocols(ctx: Context):
    """List all the installed protocols."""
    result = _get_item_details(ctx, "protocol")
    print(format_items(sorted(result, key=lambda k: k["name"])))


@list.command()
@pass_ctx
def skills(ctx: Context):
    """List all the installed skills."""
    result = _get_item_details(ctx, "skill")
    print(format_items(sorted(result, key=lambda k: k["name"])))
