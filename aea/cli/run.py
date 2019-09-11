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

"""Implementation of the 'aea run' subcommand."""

from pathlib import Path
from pydoc import locate
from typing import cast

import click

from aea.aea import AEA
from aea.channel.gym import GymConnection
from aea.channel.local import OEFLocalConnection, LocalNode
from aea.channel.oef import OEFConnection
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config, AEAConfigException
from aea.mail.base import MailBox, Connection


def _setup_connection(connection_name: str, ctx: Context) -> Connection:
    """
    Set up a connection.

    :param connection_name: the name of the connection.
    :param ctx: the CLI context object.
    :return: a Connection object.
    :raises AEAConfigException: if the connection name provided as argument is not declared in the configuration file,
                              | or if the connection type is not supported by the framework.
    """
    available_connections = ctx.agent_config.connections
    available_connection_names = available_connections.keys()
    if connection_name not in available_connection_names:
        raise AEAConfigException("Connection name '{}' not declared in the configuration file.".format(connection_name))

    connection_configuration = available_connections[connection_name]
    connection_type = connection_configuration.type
    agent_name = cast(str, ctx.agent_config.agent_name)
    if connection_type == "oef":
        oef_addr = connection_configuration.config.get("addr", "127.0.0.1")
        oef_port = connection_configuration.config.get("port", 10000)
        return OEFConnection(agent_name, oef_addr, oef_port)
    elif connection_type == "local":
        local_node = LocalNode()
        return OEFLocalConnection(agent_name, local_node)
    elif connection_type == "gym":
        gym_env_package = cast(str, connection_configuration.config.get("env"))
        gym_env = locate(gym_env_package)
        return GymConnection(agent_name, gym_env)
    else:
        raise AEAConfigException("Connection type '{}' not supported.".format(connection_type))


@click.command()
@click.option('--connection', 'connection_name', metavar="CONN_NAME", type=str, required=False, default=None,
              help="The connection name. Must be declared in the agent's configuration file.")
@pass_ctx
def run(ctx: Context, connection_name):
    """Run the agent."""
    _try_to_load_agent_config(ctx)
    agent_name = cast(str, ctx.agent_config.agent_name)
    connection_name = ctx.agent_config.default_connection if connection_name is None else connection_name
    try:
        connection = _setup_connection(connection_name, ctx)
    except AEAConfigException as e:
        logger.error(str(e))
        exit(-1)
        return

    mailbox = MailBox(connection)
    agent = AEA(agent_name, mailbox, directory=str(Path(".")))
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")
    except Exception:
        raise
    finally:
        agent.stop()
