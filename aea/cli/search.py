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
        registry = os.path.join(AEA_DIR, DEFAULT_REGISTRY_PATH)
    logger.debug("Using registry {}".format(registry))
    ctx.set_config("registry", str(registry))


@search.command()
@pass_ctx
def connections(ctx: Context):
    """List all the connections available in the registry."""
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
@pass_ctx
def protocols(ctx: Context):
    """List all the protocols available in the registry."""
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
@pass_ctx
def skills(ctx: Context):
    """List all the skills available in the registry."""
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
