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

"""Implementation of the 'aea search' subcommand."""

from pathlib import Path
from typing import Dict, List, Tuple, cast

import click

from aea import AEA_DIR
from aea.cli.registry.utils import request_api
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.cli.utils.formatting import format_items, retrieve_details
from aea.common import JSONLike
from aea.configurations.constants import (
    AGENT,
    AGENTS,
    CONNECTION,
    CONNECTIONS,
    CONTRACT,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOL,
    PROTOCOLS,
    SKILL,
    SKILLS,
)
from aea.configurations.loader import ConfigLoader


@click.group()
@click.option("--local", is_flag=True, help="For local search.")
@click.pass_context
def search(click_context: click.Context, local: bool) -> None:
    """Search for packages in the registry."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)


@search.command()
@click.option("--query", default="", help="Query string to search Connections by name.")
@click.option("--page", type=int, default=1, help="Page number to display.")
@pass_ctx
def connections(ctx: Context, query: str, page: int) -> None:
    """Search for Connections."""
    item_type = CONNECTION
    _output_search_results(item_type, *search_items(ctx, item_type, query, page), page)


@search.command()
@click.option("--query", default="", help="Query string to search Contracts by name.")
@click.option("--page", type=int, default=1, help="Page number to display.")
@pass_ctx
def contracts(ctx: Context, query: str, page: int) -> None:
    """Search for Contracts."""
    item_type = CONTRACT
    _output_search_results(item_type, *search_items(ctx, item_type, query, page), page)


@search.command()
@click.option("--query", default="", help="Query string to search Protocols by name.")
@click.option("--page", type=int, default=1, help="Page number to display.")
@pass_ctx
def protocols(ctx: Context, query: str, page: int) -> None:
    """Search for Protocols."""
    item_type = PROTOCOL
    _output_search_results(item_type, *search_items(ctx, item_type, query, page), page)


@search.command()
@click.option("--query", default="", help="Query string to search Skills by name.")
@click.option("--page", type=int, default=1, help="Page number to display.")
@pass_ctx
def skills(ctx: Context, query: str, page: int) -> None:
    """Search for Skills."""
    item_type = SKILL
    _output_search_results(item_type, *search_items(ctx, item_type, query, page), page)


@search.command()
@click.option("--query", default="", help="Query string to search Agents by name.")
@click.option("--page", type=int, default=1, help="Page number to display.")
@pass_ctx
def agents(ctx: Context, query: str, page: int) -> None:
    """Search for Agents."""
    item_type = AGENT
    _output_search_results(item_type, *search_items(ctx, item_type, query, page), page)


def _is_invalid_item(name: str, dir_path: Path, config_path: Path) -> bool:
    """Return true if this protocol, connection or skill should not be returned in the list."""
    return (
        name == "scaffold"
        or not Path(dir_path).is_dir()
        or not Path(config_path).is_file()
    )


def _get_details_from_dir(
    loader: ConfigLoader,
    root_path: str,
    sub_dir_glob_pattern: str,
    config_filename: str,
    results: List[Dict],
) -> None:
    for dir_path in Path(root_path).glob(sub_dir_glob_pattern + "/*/"):
        config_path = dir_path / config_filename

        if _is_invalid_item(dir_path.name, dir_path, config_path):
            continue

        details = retrieve_details(dir_path.name, loader, str(config_path))
        results.append(details)


def _search_items_locally(ctx: Context, item_type_plural: str) -> List[Dict]:
    result = []  # type: List[Dict]
    configs = {
        AGENTS: {"loader": ctx.agent_loader, "config_file": DEFAULT_AEA_CONFIG_FILE},
        CONNECTIONS: {
            "loader": ctx.connection_loader,
            "config_file": DEFAULT_CONNECTION_CONFIG_FILE,
        },
        CONTRACTS: {
            "loader": ctx.contract_loader,
            "config_file": DEFAULT_CONTRACT_CONFIG_FILE,
        },
        PROTOCOLS: {
            "loader": ctx.protocol_loader,
            "config_file": DEFAULT_PROTOCOL_CONFIG_FILE,
        },
        SKILLS: {"loader": ctx.skill_loader, "config_file": DEFAULT_SKILL_CONFIG_FILE},
    }
    if item_type_plural != AGENTS:
        # look in aea distribution for default packages
        _get_details_from_dir(
            cast(ConfigLoader, configs[item_type_plural]["loader"]),
            AEA_DIR,
            item_type_plural,
            cast(str, configs[item_type_plural]["config_file"]),
            result,
        )

    try:
        registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))
    # look in packages dir for all other packages
    _get_details_from_dir(
        cast(ConfigLoader, configs[item_type_plural]["loader"]),
        registry_path,
        "*/{}".format(item_type_plural),
        cast(str, configs[item_type_plural]["config_file"]),
        result,
    )

    return sorted(result, key=lambda k: k["name"])


def search_items(
    ctx: Context, item_type: str, query: str, page: int
) -> Tuple[List[Dict], int]:
    """
    Search items by query and click.echo results.

    :param ctx: Context object.
    :param item_type: item type.
    :param query: query string.
    :param page: page.

    :return: (List of items, int items total count).
    """
    click.echo('Searching for "{}"...'.format(query))
    item_type_plural = item_type + "s"
    if ctx.config.get("is_local"):
        results = _search_items_locally(ctx, item_type_plural)
        count = len(results)
    else:
        resp = cast(
            JSONLike,
            request_api(
                "GET",
                "/{}".format(item_type_plural),
                params={"search": query, "page": page},
            ),
        )
        results = cast(List[Dict], resp["results"])
        count = cast(int, resp["count"])
    return results, count


def _output_search_results(
    item_type: str, results: List[Dict], count: int, page: int
) -> None:
    """
    Output search results.

    :param item_type: str item type.
    :param results: list of found items.
    :param count: items total count.
    :param page: page.
    """
    item_type_plural = item_type + "s"
    len_results = len(results)
    if len_results == 0:
        click.echo("No {} found.".format(item_type_plural))  # pragma: no cover
    else:
        click.echo("{} found:\n".format(item_type_plural.title()))
        click.echo(format_items(results))
        if count > len_results:
            click.echo(
                "{} {} out of {}.\nPage {}".format(
                    len_results, item_type_plural, count, page
                )
            )  # pragma: no cover
