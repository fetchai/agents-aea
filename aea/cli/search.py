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
from typing import Set, cast
import click
import os

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, DEFAULT_REGISTRY_PATH, logger
from aea.cli.registry.utils import format_items, format_skills, request_api


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
        registry = os.path.join(AEA_DIR, DEFAULT_REGISTRY_PATH)
        ctx.set_config("registry", registry)
        logger.debug("Using registry {}".format(registry))


@search.command()
@click.option('--query', prompt='Connection search query',
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
            click.echo('No connections found.')
        else:
            click.echo('Connections found:\n')
            click.echo(format_items(resp))
            return

    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[str]
    for r in Path(AEA_DIR).glob("connections/[!_]*[!.py]/"):
        result.add(r.name)

    try:
        for r in Path(registry).glob("connections/[!_]*[!.py]/"):
            result.add(r.name)
    except Exception:  # pragma: no cover
        pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available connections:")
    for conn in sorted(result):
        print("- " + conn)


@search.command()
@click.option('--query', prompt='Protocol search query',
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
            click.echo('No protocols found.')
        else:
            click.echo('Protocols found:\n')
            click.echo(format_items(resp))
            return

    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[str]
    for r in Path(AEA_DIR).glob("protocols/[!_]*[!.py]"):
        result.add(r.name)

    try:
        for r in Path(registry).glob("protocols/[!_]*[!.py]/"):
            result.add(r.name)
    except Exception:  # pragma: no cover
        pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available protocols:")
    for protocol in sorted(result):
        print("- " + protocol)


@search.command()
@click.option('--query', prompt='Skill search query',
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
            click.echo('No skills found.')
        else:
            click.echo('Skills found:\n')
            click.echo(format_skills(resp))
            return

    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[str]
    for r in Path(AEA_DIR).glob("skills/[!_]*[!.py]"):
        result.add(r.name)

    try:
        for r in Path(registry).glob("skills/[!_]*[!.py]/"):
            result.add(r.name)
    except Exception:  # pragma: no cover
        pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available skills:")
    for skill in sorted(result):
        print("- " + skill)
