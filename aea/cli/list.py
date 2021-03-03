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

from aea.cli.utils.constants import ITEM_TYPES
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.formatting import format_items, retrieve_details, sort_items
from aea.configurations.base import (
    PackageType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL, VENDOR
from aea.configurations.loader import ConfigLoader


@click.group(name="list")
@click.pass_context
@check_aea_project
def list_command(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """List the installed packages of the agent."""


@list_command.command(name="all")
@pass_ctx
def all_command(ctx: Context) -> None:
    """List all the installed packages."""
    for item_type in ITEM_TYPES:
        details = list_agent_items(ctx, item_type)
        if not details:
            continue
        output = "{}:\n{}".format(
            item_type.title() + "s", format_items(sort_items(details))
        )
        click.echo(output)


@list_command.command()
@pass_ctx
def connections(ctx: Context) -> None:
    """List all the installed connections."""
    result = list_agent_items(ctx, CONNECTION)
    click.echo(format_items(sort_items(result)))


@list_command.command()
@pass_ctx
def contracts(ctx: Context) -> None:
    """List all the installed protocols."""
    result = list_agent_items(ctx, CONTRACT)
    click.echo(format_items(sort_items(result)))


@list_command.command()
@pass_ctx
def protocols(ctx: Context) -> None:
    """List all the installed protocols."""
    result = list_agent_items(ctx, PROTOCOL)
    click.echo(format_items(sort_items(result)))


@list_command.command()
@pass_ctx
def skills(ctx: Context) -> None:
    """List all the installed skills."""
    result = list_agent_items(ctx, SKILL)
    click.echo(format_items(sorted(result, key=lambda k: k["name"])))


def list_agent_items(ctx: Context, item_type: str) -> List[Dict]:
    """Return a list of item details, given the item type."""
    result = []
    item_type_plural = item_type + "s"
    public_ids = getattr(ctx.agent_config, item_type_plural)  # type: Set[PublicId]
    default_file_name = _get_default_configuration_file_name_from_type(item_type)
    for public_id in public_ids:
        # first, try to retrieve the item from the vendor directory.
        configuration_filepath = Path(
            ctx.cwd,
            VENDOR,
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
            PackageType(item_type)
        )
        details = retrieve_details(
            public_id.name, configuration_loader, str(configuration_filepath)
        )
        result.append(details)
    return result
