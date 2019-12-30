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

"""Implementation of the 'aea push' subcommand."""
import click

from aea.cli.common import pass_ctx, Context, PublicIdParameter
from aea.cli.registry.push import push_item, save_item_locally


@click.group()
@click.option('--local', is_flag=True, help="For saving item locally.")
@pass_ctx
def push(ctx: Context, local):
    """Push item to Registry or save it in local packages."""
    ctx.set_config("local", local)


@push.command(name='connection')
@click.argument('connection-id', type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """Push connection to Registry or save it in local packages."""
    if ctx.config.get("local"):
        save_item_locally('connection', connection_id)
    else:
        push_item('connection', connection_id.name)


@push.command(name='protocol')
@click.argument('protocol-id', type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """Push protocol to Registry or save it in local packages."""
    if ctx.config.get("local"):
        save_item_locally('protocol', protocol_id)
    else:
        push_item('protocol', protocol_id.name)


@push.command(name='skill')
@click.argument('skill-id', type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """Push skill to Registry or save it in local packages."""
    if ctx.config.get("local"):
        save_item_locally('skill', skill_id)
    else:
        push_item('skill', skill_id.name)
