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

from typing import cast

import click
from click import pass_context

from aea.cli.common import Context, pass_ctx, _try_to_load_agent_config


@click.group()
@pass_ctx
def list(ctx: Context):
    """Add a resource to the agent."""
    _try_to_load_agent_config(ctx)


@list.command()
@pass_context
def connections(click_context):
    """List all the available connections."""
    ctx = cast(Context, click_context.obj)
    for c in ctx.agent_config.connections:
        print(c)


@list.command()
@pass_context
def protocols(click_context):
    """List all the available connections."""
    ctx = cast(Context, click_context.obj)
    for c in ctx.agent_config.protocols:
        print(c)


@list.command()
@pass_context
def skills(click_context):
    """List all the available connections."""
    ctx = cast(Context, click_context.obj)
    for c in ctx.agent_config.skills:
        print(c)
