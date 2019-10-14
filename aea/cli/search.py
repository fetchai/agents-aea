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

import click

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx


@click.group()
@click.option("--registry", type=str, default=None, help="Path/URL to the registry.")
@pass_ctx
def search(ctx: Context, registry):
    """Search for components in the registry.

    E.g.

        aea search --registry packages/ skills
    """
    ctx.set_config("registry", registry)


@search.command()
@pass_ctx
def connections(ctx: Context):
    """List all the connections available in the registry."""
    registry = ctx.config.get("registry")
    result = set()
    for r in Path(AEA_DIR).glob("connections/[!_]*[!.py]/"):
        result.add(r.name)

    try:
        for r in Path(registry).glob("connections/[!_]*[!.py]/"):
            result.add(r.name)
    except:
        pass

    if "scaffold" in result: result.remove("scaffold")
    for r in sorted(result):
        print(r)


@search.command()
@pass_ctx
def protocols(ctx: Context):
    """List all the protocols available in the registry."""
    registry = ctx.config.get("registry")
    result = set()
    for r in Path(AEA_DIR).glob("protocols/[!_]*[!.py]"):
        result.add(r.name)

    try:
        for r in Path(registry).glob("protocols/[!_]*[!.py]/"):
            result.add(r.name)
    except:
        pass

    if "scaffold" in result: result.remove("scaffold")
    for r in sorted(result):
        print(r)


@search.command()
@pass_ctx
def skills(ctx: Context):
    """List all the skills available in the registry."""
    registry = ctx.config.get("registry")
    result = set()
    for e in Path(AEA_DIR).glob("skills/[!_]*[!.py]"):
        result.add(e.name)

    try:
        for r in Path(registry).glob("skills/[!_]*[!.py]/"):
            result.add(r.name)
    except:
        pass

    if "scaffold" in result: result.remove("scaffold")
    for r in sorted(result):
        print(r)
