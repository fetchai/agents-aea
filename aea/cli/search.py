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

import os
from pathlib import Path
from typing import Dict, List, cast

import click

from aea import AEA_DIR
from aea.cli.common import (
    ConfigLoader,
    Context,
    DEFAULT_REGISTRY_PATH,
    _format_items,
    _retrieve_details,
    logger,
    pass_ctx,
    try_to_load_agent_config,
)
from aea.cli.registry.utils import request_api
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)


@click.group()
@click.option("--local", is_flag=True, help="For local search.")
@click.pass_context
def search(click_context, local):
    """Search for components in the registry.

    If called from an agent directory, it will check

    E.g.

        aea search connections
        aea search --local skills
    """
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)
        # if we are in an agent directory, try to load the configuration file.
        # otherwise, use the default path (i.e. 'packages/' in the current directory.)
        try:
            try_to_load_agent_config(ctx, is_exit_on_except=False)
            # path = Path(DEFAULT_AEA_CONFIG_FILE)
            # fp = open(str(path), mode="r", encoding="utf-8")
            # agent_config = ctx.agent_loader.load(fp)
            registry_directory = ctx.agent_config.registry_path
        except Exception:
            registry_directory = os.path.join(ctx.cwd, DEFAULT_REGISTRY_PATH)

        ctx.set_config("registry_directory", registry_directory)
        logger.debug("Using registry {}".format(registry_directory))


def _is_invalid_item(name, dir_path, config_path):
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
):
    for dir_path in Path(root_path).glob(sub_dir_glob_pattern + "/*/"):
        config_path = dir_path / config_filename

        if _is_invalid_item(dir_path.name, dir_path, config_path):
            continue

        details = _retrieve_details(dir_path.name, loader, str(config_path))
        results.append(details)


def _search_items(ctx, item_type_plural):
    registry = cast(str, ctx.config.get("registry_directory"))
    result = []  # type: List[Dict]
    configs = {
        "agents": {"loader": ctx.agent_loader, "config_file": DEFAULT_AEA_CONFIG_FILE},
        "connections": {
            "loader": ctx.connection_loader,
            "config_file": DEFAULT_CONNECTION_CONFIG_FILE,
        },
        "contracts": {
            "loader": ctx.contract_loader,
            "config_file": DEFAULT_CONTRACT_CONFIG_FILE,
        },
        "protocols": {
            "loader": ctx.protocol_loader,
            "config_file": DEFAULT_PROTOCOL_CONFIG_FILE,
        },
        "skills": {
            "loader": ctx.skill_loader,
            "config_file": DEFAULT_SKILL_CONFIG_FILE,
        },
    }
    if item_type_plural == "agents":
        lookup_dir = registry
    else:
        lookup_dir = AEA_DIR
        _get_details_from_dir(
            configs[item_type_plural]["loader"],
            registry,
            "*/{}".format(item_type_plural),
            configs[item_type_plural]["config_file"],
            result,
        )

    _get_details_from_dir(
        configs[item_type_plural]["loader"],
        lookup_dir,
        item_type_plural,
        configs[item_type_plural]["config_file"],
        result,
    )

    return sorted(result, key=lambda k: k["name"])


@search.command()
@click.option("--query", default="", help="Query string to search Connections by name.")
@pass_ctx
def connections(ctx: Context, query):
    """Search for Connections."""
    click.echo('Searching for "{}"...'.format(query))
    if ctx.config.get("is_local"):
        results = _search_items(ctx, "connections")
    else:
        results = request_api("GET", "/connections", params={"search": query})

    if not len(results):
        click.echo("No connections found.")  # pragma: no cover
    else:
        click.echo("Connections found:\n")
        click.echo(_format_items(results))


@search.command()
@click.option("--query", default="", help="Query string to search Contracts by name.")
@pass_ctx
def contracts(ctx: Context, query):
    """Search for Contracts."""
    click.echo('Searching for "{}"...'.format(query))
    if ctx.config.get("is_local"):
        results = _search_items(ctx, "contracts")
    else:
        results = request_api("GET", "/contracts", params={"search": query})

    if not len(results):
        click.echo("No contracts found.")  # pragma: no cover
    else:
        click.echo("Contracts found:\n")
        click.echo(_format_items(results))


@search.command()
@click.option("--query", default="", help="Query string to search Protocols by name.")
@pass_ctx
def protocols(ctx: Context, query):
    """Search for Protocols."""
    click.echo('Searching for "{}"...'.format(query))
    if ctx.config.get("is_local"):
        results = _search_items(ctx, "protocols")
    else:
        results = request_api("GET", "/protocols", params={"search": query})

    if not len(results):
        click.echo("No protocols found.")  # pragma: no cover
    else:
        click.echo("Protocols found:\n")
        click.echo(_format_items(results))


@search.command()
@click.option("--query", default="", help="Query string to search Skills by name.")
@pass_ctx
def skills(ctx: Context, query):
    """Search for Skills."""
    click.echo('Searching for "{}"...'.format(query))
    if ctx.config.get("is_local"):
        results = _search_items(ctx, "skills")
    else:
        results = request_api("GET", "/skills", params={"search": query})

    if not len(results):
        click.echo("No skills found.")  # pragma: no cover
    else:
        click.echo("Skills found:\n")
        click.echo(_format_items(results))


@search.command()
@click.option("--query", default="", help="Query string to search Agents by name.")
@pass_ctx
def agents(ctx: Context, query):
    """Search for Agents."""
    click.echo('Searching for "{}"...'.format(query))
    if ctx.config.get("is_local"):
        results = _search_items(ctx, "agents")
    else:
        results = request_api("GET", "/agents", params={"search": query})

    if not len(results):
        click.echo("No agents found.")  # pragma: no cover
    else:
        click.echo("Agents found:\n")
        click.echo(_format_items(results))
