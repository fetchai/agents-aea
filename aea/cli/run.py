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
import sys
from pathlib import Path
from typing import cast

import click
from click import pass_context

from aea.aea import AEA
from aea.cli.common import Context, logger, _try_to_load_agent_config, _try_to_load_protocols, \
    AEAConfigException, _load_env_file
from aea.cli.install import install
from aea.connections.base import Connection
from aea.crypto.helpers import _verify_or_create_private_keys, _verify_ledger_apis_access
from aea.crypto.wallet import Wallet, DEFAULT
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

    try:
        connection_config = ctx.connection_loader.load(open(os.path.join(ctx.cwd, "connections", connection_name, "connection.yaml")))
    except FileNotFoundError:
        raise AEAConfigException("Connection config for '{}' not found.".format(connection_name))

    try:
        connection_spec = importlib.util.spec_from_file_location(connection_config.name, os.path.join(ctx.cwd, "connections", connection_config.name, "connection.py"))
        connection_module = importlib.util.module_from_spec(connection_spec)
        connection_spec.loader.exec_module(connection_module)  # type: ignore
    except FileNotFoundError:
        raise AEAConfigException("Connection '{}' not found.".format(connection_name))

    sys.modules[connection_spec.name + "_connection"] = connection_module
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
@click.option('--env', 'env_file', type=click.Path(), required=False, default=".env",
              help="Specify an environment file (default: .env)")
@click.option('--install-deps', 'install_deps', is_flag=True, required=False, default=False,
              help="Install all the dependencies before running the agent.")
@pass_context
def run(click_context, connection_name: str, env_file: str, install_deps: bool):
    """Run the agent."""
    ctx = cast(Context, click_context.obj)
    _try_to_load_agent_config(ctx)
    _load_env_file(env_file)
    agent_name = cast(str, ctx.agent_config.agent_name)

    _verify_or_create_private_keys(ctx)
    _verify_ledger_apis_access(ctx)
    private_key_paths = dict([(identifier, config.path) for identifier, config in ctx.agent_config.private_key_paths.read_all()])
    ledger_api_configs = dict([(identifier, (config.addr, config.port)) for identifier, config in ctx.agent_config.ledger_apis.read_all()])

    wallet = Wallet(private_key_paths, ledger_api_configs)

    connection_name = ctx.agent_config.default_connection if connection_name is None else connection_name
    _try_to_load_protocols(ctx)
    try:
        connection = _setup_connection(connection_name, wallet.public_keys[DEFAULT], ctx)
    except AEAConfigException as e:
        logger.error(str(e))
        exit(-1)

    if install_deps:
        if Path("requirements.txt").exists():
            click_context.invoke(install, requirement="requirements.txt")
        else:
            click_context.invoke(install)

    mailbox = MailBox(connection)
    agent = AEA(agent_name, mailbox, wallet, directory=str(Path(".")))
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")  # pragma: no cover
    except Exception as e:
        logger.exception(e)
        exit(-1)
    finally:
        agent.stop()
