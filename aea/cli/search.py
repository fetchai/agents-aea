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
from aea.cli.common import Context, pass_ctx, DEFAULT_REGISTRY_PATH, logger, retrieve_description
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, \
    DEFAULT_PROTOCOL_CONFIG_FILE

@click.group()
@click.option("--registry", type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True),
              default=None, help="Path/URL to the registry.")
@pass_ctx
def search(ctx: Context, registry):
    """Search for components in the registry.

    E.g.

        aea search --registry packages/ skills
    """
    if registry is None:
        registry = os.path.join(ctx.cwd, DEFAULT_REGISTRY_PATH)
    logger.debug("Using registry {}".format(registry))
    ctx.set_config("registry", str(registry))


@search.command()
@pass_ctx
def connections(ctx: Context):
    """List all the connections available in the registry."""
    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[(str, str)]
    for r in Path(AEA_DIR).glob("connections/*/"):
        if ".py" in r.name or "__" in r.name:
            continue
        configuration_path = os.path.join(AEA_DIR, "connections", r.name, DEFAULT_CONNECTION_CONFIG_FILE)
        result.add((r.name, retrieve_description(ctx.connection_loader, configuration_path)))

    for r in Path(registry).glob("connections/*/"):
        if ".py" in r.name or "__" in r.name:
            continue
        try:
            configuration_path = os.path.join(registry, "connections", r.name, DEFAULT_CONNECTION_CONFIG_FILE)
            result.add((r.name, retrieve_description(ctx.connection_loader, configuration_path)))

        except Exception:  # pragma: no cover
            pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available connections:")
    for conn in sorted(result):
        print("{}\t[{}]".format(conn[0], conn[1]))


@search.command()
@pass_ctx
def protocols(ctx: Context):
    """List all the protocols available in the registry."""
    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[(str, str)]
    for r in Path(AEA_DIR).glob("protocols/*"):
        if ".py" in r.name or "__" in r.name:
            continue
        configuration_path = os.path.join(AEA_DIR, "protocols", r.name, DEFAULT_PROTOCOL_CONFIG_FILE)
        result.add((r.name, retrieve_description(ctx.protocol_loader, configuration_path)))

    for r in Path(registry).glob("protocols/*/"):
        if ".py" in r.name or "__" in r.name:
            continue
        try:
            configuration_path = os.path.join(registry, "protocols", r.name, DEFAULT_PROTOCOL_CONFIG_FILE)
            result.add((r.name, retrieve_description(ctx.protocol_loader, configuration_path)))
        except Exception:  # pragma: no cover
            pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available protocols:")
    for protocol in sorted(result):
        print("{}\t[{}]".format(protocol[0], protocol[1]))


@search.command()
@pass_ctx
def skills(ctx: Context):
    """List all the skills available in the registry."""
    registry = cast(str, ctx.config.get("registry"))
    result = set()  # type: Set[(str, str)]
    for r in Path(AEA_DIR).glob("skills/*/"):
        if ".py" in r.name or "__" in r.name:
            continue
        configuration_path = os.path.join(AEA_DIR, "skills", r.name, DEFAULT_SKILL_CONFIG_FILE)
        result.add((r.name, retrieve_description(ctx.skill_loader, configuration_path)))

    for r in Path(registry).glob("skills/*/"):
        if ".py" in r.name or "__" in r.name:
            continue
        try:
            configuration_path = os.path.join(registry, "skills", r.name, DEFAULT_SKILL_CONFIG_FILE)
            result.add((r.name, retrieve_description(ctx.skill_loader, configuration_path)))
        except Exception:  # pragma: no cover
            pass

    if "scaffold" in result: result.remove("scaffold")
    if ".DS_Store" in result: result.remove(".DS_Store")
    print("Available skills:")
    for skill in sorted(result):
        print("{}\t[{}]".format(skill[0], skill[1]))
