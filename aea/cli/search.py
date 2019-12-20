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
from typing import cast, List, Dict

import click

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, DEFAULT_REGISTRY_PATH, logger, retrieve_details, ConfigLoader, \
    format_items, format_skills
from aea.cli.registry.utils import request_api
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, \
    DEFAULT_PROTOCOL_CONFIG_FILE


@click.group()
@click.option('--registry', is_flag=True, help="For Registry search.")
@pass_ctx
def search(ctx: Context, registry):
    """Search for components in the registry.

    E.g.

        aea search --registry packages/ skills
    """
    if registry:
        ctx.set_config("is_registry", True)
    else:
        registry = os.path.join(ctx.cwd, DEFAULT_REGISTRY_PATH)
        ctx.set_config("registry", registry)
        logger.debug("Using registry {}".format(registry))


def _is_invalid_item(name, dir_path, config_path):
    """Return true if this protocol, connection or skill should not be returned in the list."""
    return ".py" in name or "__" in name or name == "scaffold" or os.path.isfile(dir_path) or not os.path.isfile(config_path)


def _get_details_from_dir(loader: ConfigLoader, root_path: str, sub_dir_name: str, config_filename: str, results: List[Dict]):
    for r in Path(root_path).glob(sub_dir_name + "/*/"):
        dir_path = os.path.join(root_path, sub_dir_name, r.name)
        config_path = os.path.join(root_path, sub_dir_name, r.name, config_filename)

        if _is_invalid_item(r.name, dir_path, config_path):
            continue

        details = retrieve_details(r.name, loader, config_path)
        results.append(details)


@search.command()
@click.option('--query', default='',
              help='Query string to search Connections by name.')
@pass_ctx
def connections(ctx: Context, query):
    """Search for Connections."""
    if ctx.config.get("is_registry"):
        click.echo('Searching for "{}"...'.format(query))
        resp = request_api(
            'GET', '/connections', params={'search': query}
        )
        if not len(resp):
            click.echo('No connections found.')  # pragma: no cover
        else:
            click.echo('Connections found:\n')
            click.echo(format_items(resp))
        return

    registry = cast(str, ctx.config.get("registry"))
    result: List[Dict] = []
    _get_details_from_dir(ctx.connection_loader, AEA_DIR, "connections", DEFAULT_CONNECTION_CONFIG_FILE, result)
    _get_details_from_dir(ctx.connection_loader, registry, "connections", DEFAULT_CONNECTION_CONFIG_FILE, result)

    print("Available connections:")
    print(format_items(sorted(result, key=lambda k: k['name'])))


@search.command()
@click.option('--query', default='',
              help='Query string to search Protocols by name.')
@pass_ctx
def protocols(ctx: Context, query):
    """Search for Protocols."""
    if ctx.config.get("is_registry"):
        click.echo('Searching for "{}"...'.format(query))
        resp = request_api(
            'GET', '/protocols', params={'search': query}
        )
        if not len(resp):
            click.echo('No protocols found.')  # pragma: no cover
        else:
            click.echo('Protocols found:\n')
            click.echo(format_items(resp))
        return

    registry = cast(str, ctx.config.get("registry"))
    result: List[Dict] = []
    _get_details_from_dir(ctx.protocol_loader, AEA_DIR, "protocols", DEFAULT_PROTOCOL_CONFIG_FILE, result)
    _get_details_from_dir(ctx.protocol_loader, registry, "protocols", DEFAULT_PROTOCOL_CONFIG_FILE, result)

    print("Available protocols:")
    print(format_items(sorted(result, key=lambda k: k['name'])))


@search.command()
@click.option('--query', default='',
              help='Query string to search Skills by name.')
@pass_ctx
def skills(ctx: Context, query):
    """Search for Skills."""
    if ctx.config.get("is_registry"):
        click.echo('Searching for "{}"...'.format(query))
        resp = request_api(
            'GET', '/skills', params={'search': query}
        )
        if not len(resp):
            click.echo('No skills found.')  # pragma: no cover
        else:
            click.echo('Skills found:\n')
            click.echo(format_skills(resp))
        return

    registry = cast(str, ctx.config.get("registry"))
    result: List[Dict] = []
    _get_details_from_dir(ctx.skill_loader, AEA_DIR, "skills", DEFAULT_SKILL_CONFIG_FILE, result)
    _get_details_from_dir(ctx.skill_loader, registry, "skills", DEFAULT_SKILL_CONFIG_FILE, result)

    print("Available skills:")
    print(format_items(sorted(result, key=lambda k: k['name'])))
