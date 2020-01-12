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
import os

import click


from aea.cli.common import Context, pass_ctx, try_to_load_agent_config, retrieve_details, format_items
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, \
    DEFAULT_PROTOCOL_CONFIG_FILE


@click.group()
@pass_ctx
def list(ctx: Context):
    """List the installed resources."""
    try_to_load_agent_config(ctx)


@list.command()
@pass_ctx
def connections(ctx: Context):
    """List all the installed connections."""
    result = []
    for connection_id in sorted(ctx.agent_config.connections):
        connection_name = connection_id.name
        connection_configuration_filepath = os.path.join("connections", connection_name, DEFAULT_CONNECTION_CONFIG_FILE)
        details = retrieve_details(connection_name, ctx.connection_loader, connection_configuration_filepath)
        result.append(details)

    print(format_items(sorted(result, key=lambda k: k['name'])))


@list.command()
@pass_ctx
def protocols(ctx: Context):
    """List all the installed protocols."""
    result = []
    for protocol_id in sorted(ctx.agent_config.protocols):
        protocol_name = protocol_id.name
        protocol_configuration_filepath = os.path.join("protocols", protocol_name, DEFAULT_PROTOCOL_CONFIG_FILE)
        details = retrieve_details(protocol_name, ctx.protocol_loader, protocol_configuration_filepath)
        result.append(details)

    print(format_items(sorted(result, key=lambda k: k['name'])))


@list.command()
@pass_ctx
def skills(ctx: Context):
    """List all the installed skills."""
    result = []
    for skill_id in sorted(ctx.agent_config.skills):
        skill_name = skill_id.name
        skill_configuration_filepath = os.path.join("skills", skill_name, DEFAULT_SKILL_CONFIG_FILE)
        details = retrieve_details(skill_name, ctx.skill_loader, skill_configuration_filepath)
        result.append(details)

    print(format_items(sorted(result, key=lambda k: k['name'])))
