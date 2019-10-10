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
import importlib.util
import inspect
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

import click

from aea.aea import AEA
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config, _try_to_load_protocols, \
    AEAConfigException
from aea.connections.base import Connection
from aea.crypto.base import Crypto
from aea.crypto.helpers import _try_validate_private_key_pem_path, _create_temporary_private_key_pem_path
# from aea.helpers.base import locate
from aea.mail.base import MailBox


def _setup_connection(connection_name: str, public_key: str, ctx: Context) -> Connection:
    """
    Set up a connection.

    :param connection_name: the name of the connection.
    :param ctx: the CLI context object.
    :param public_key: the path of the public key.
    :return: a Connection object.
    :raises AEAConfigException: if the connection name provided as argument is not declared in the configuration file,
                              | or if the connection type is not supported by the framework.
    """
    if connection_name not in ctx.agent_config.connections:
        raise AEAConfigException("Connection name '{}' not declared in the configuration file.".format(connection_name))

    connection_config = ctx.connection_loader.load(open(os.path.join(ctx.cwd, "connections", connection_name, "connection.yaml")))
    if connection_config is None:
        raise AEAConfigException("Connection config for '{}' not found.".format(connection_name))

    connection_spec = importlib.util.spec_from_file_location(connection_config.name, os.path.join(ctx.cwd, "connections", connection_config.name, "connection.py"))
    if connection_spec is None:
        raise AEAConfigException("Connection '{}' not found.".format(connection_name))

    connection_module = importlib.util.module_from_spec(connection_spec)
    sys.modules[connection_spec.name + "_connection"] = connection_module
    connection_spec.loader.exec_module(connection_module)  # type: ignore
    classes = inspect.getmembers(connection_module, inspect.isclass)
    connection_classes = list(filter(lambda x: re.match("\\w+Connection", x[0]), classes))
    name_to_class = dict(connection_classes)
    connection_class_name = cast(str, connection_config.class_name)
    logger.debug("Processing connection {}".format(connection_class_name))
    connection_class = name_to_class.get(connection_class_name, None)
    if connection_class is None:
        raise AEAConfigException("Connection class '{}' not found.".format(connection_class_name))

    connection = connection_class.from_config(public_key, connection_config)
    return connection


@click.command()
@click.option('--connection', 'connection_name', metavar="CONN_NAME", type=str, required=False, default=None,
              help="The connection name. Must be declared in the agent's configuration file.")
@pass_ctx
def run(ctx: Context, connection_name: str):
    """Run the agent."""
    _try_to_load_agent_config(ctx)
    agent_name = cast(str, ctx.agent_config.agent_name)
    private_key_pem_path = cast(str, ctx.agent_config.private_key_pem_path)
    if private_key_pem_path == "":
        private_key_pem_path = _create_temporary_private_key_pem_path()
    else:
        _try_validate_private_key_pem_path(private_key_pem_path)
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    connection_name = ctx.agent_config.default_connection if connection_name is None else connection_name
    _try_to_load_protocols(ctx)
    try:
        connection = _setup_connection(connection_name, public_key, ctx)
    except AEAConfigException as e:
        logger.error(str(e))
        exit(-1)
        return

    mailbox = MailBox(connection)
    agent = AEA(agent_name, mailbox, private_key_pem_path=private_key_pem_path, directory=str(Path(".")))
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")
    except Exception as e:
        logger.exception(e)
    finally:
        agent.stop()
