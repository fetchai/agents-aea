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
import inspect
import os
import re
import sys
from pathlib import Path
from typing import cast, List, Union

import click
from click import pass_context

from aea.aea import AEA
from aea.cli.common import Context, logger, _try_to_load_agent_config, _try_to_load_protocols, \
    AEAConfigException, _load_env_file, ConnectionsOption
from aea.cli.install import install
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PrivateKeyPathConfig, \
    PublicId
from aea.configurations.loader import ConfigLoader
from aea.connections.base import Connection
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import _create_default_private_key, _create_fetchai_private_key, _create_ethereum_private_key, \
    DEFAULT_PRIVATE_KEY_FILE, FETCHAI_PRIVATE_KEY_FILE, ETHEREUM_PRIVATE_KEY_FILE, _try_validate_private_key_pem_path, \
    _try_validate_fet_private_key_path, _try_validate_ethereum_private_key_path
from aea.crypto.ledger_apis import LedgerApis, _try_to_instantiate_fetchai_ledger_api, \
    _try_to_instantiate_ethereum_ledger_api, SUPPORTED_LEDGER_APIS
from aea.crypto.wallet import Wallet, DEFAULT, SUPPORTED_CRYPTOS
from aea.helpers.base import load_module, add_agent_component_module_to_sys_modules, load_agent_component_package
from aea.registries.base import Resources


def _verify_or_create_private_keys(ctx: Context) -> None:
    """
    Verify or create private keys.

    :param ctx: Context
    """
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = open(str(path), mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, value in aea_conf.private_key_paths.read_all():
        if identifier not in SUPPORTED_CRYPTOS:
            ValueError("Unsupported identifier in private key paths.")

    default_private_key_config = aea_conf.private_key_paths.read(DEFAULT)
    if default_private_key_config is None:
        _create_default_private_key()
        default_private_key_config = PrivateKeyPathConfig(DEFAULT, DEFAULT_PRIVATE_KEY_FILE)
        aea_conf.private_key_paths.create(default_private_key_config.ledger, default_private_key_config)
    else:
        default_private_key_config = cast(PrivateKeyPathConfig, default_private_key_config)
        try:
            _try_validate_private_key_pem_path(default_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(default_private_key_config.path), default_private_key_config.ledger))
            sys.exit(1)

    fetchai_private_key_config = aea_conf.private_key_paths.read(FETCHAI)
    if fetchai_private_key_config is None:
        _create_fetchai_private_key()
        fetchai_private_key_config = PrivateKeyPathConfig(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        aea_conf.private_key_paths.create(fetchai_private_key_config.ledger, fetchai_private_key_config)
    else:
        fetchai_private_key_config = cast(PrivateKeyPathConfig, fetchai_private_key_config)
        try:
            _try_validate_fet_private_key_path(fetchai_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(fetchai_private_key_config.path), fetchai_private_key_config.ledger))
            sys.exit(1)

    ethereum_private_key_config = aea_conf.private_key_paths.read(ETHEREUM)
    if ethereum_private_key_config is None:
        _create_ethereum_private_key()
        ethereum_private_key_config = PrivateKeyPathConfig(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        aea_conf.private_key_paths.create(ethereum_private_key_config.ledger, ethereum_private_key_config)
    else:
        ethereum_private_key_config = cast(PrivateKeyPathConfig, ethereum_private_key_config)
        try:
            _try_validate_ethereum_private_key_path(ethereum_private_key_config.path)
        except FileNotFoundError:
            logger.error("File {} for private key {} not found.".format(repr(ethereum_private_key_config.path), ethereum_private_key_config.ledger))
            sys.exit(1)

    # update aea config
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    fp = open(str(path), mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)
    ctx.agent_config = aea_conf


def _verify_ledger_apis_access() -> None:
    """Verify access to ledger apis."""
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = open(str(path), mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, value in aea_conf.ledger_apis.read_all():
        if identifier not in SUPPORTED_LEDGER_APIS:
            ValueError("Unsupported identifier in ledger apis.")

    fetchai_ledger_api_config = aea_conf.ledger_apis.read(FETCHAI)
    if fetchai_ledger_api_config is None:
        logger.debug("No fetchai ledger api config specified.")
    else:
        _try_to_instantiate_fetchai_ledger_api(cast(str, fetchai_ledger_api_config.get('addr')),
                                               cast(int, fetchai_ledger_api_config.get('port')))

    ethereum_ledger_config = aea_conf.ledger_apis.read(ETHEREUM)
    if ethereum_ledger_config is None:
        logger.debug("No ethereum ledger api config specified.")
    else:
        _try_to_instantiate_ethereum_ledger_api(cast(str, ethereum_ledger_config.get('addr')))


def _setup_connection(connection_name: str, address: str, ctx: Context) -> Connection:
    """
    Set up a connection.

    :param connection_name: the name of the connection.
    :param ctx: the CLI context object.
    :param address: the address.
    :return: a Connection object.
    :raises AEAConfigException: if the connection name provided as argument is not declared in the configuration file,
                              | or if the connection type is not supported by the framework.
    """
    supported_connection_names = set(map(lambda x: x.name, ctx.agent_config.connections))
    if connection_name not in supported_connection_names:
        raise AEAConfigException("Connection name '{}' not declared in the configuration file.".format(connection_name))

    try:
        connection_config = ctx.connection_loader.load(open(os.path.join(ctx.cwd, "connections", connection_name, "connection.yaml")))
    except FileNotFoundError:
        raise AEAConfigException("Connection config for '{}' not found.".format(connection_name))

    try:
        connection_package = load_agent_component_package("connection", connection_name)
        add_agent_component_module_to_sys_modules("connection", connection_name, connection_package)
    except FileNotFoundError:
        raise AEAConfigException("Connection '{}' not found.".format(connection_name))

    connection_module = load_module("connection_module", Path("connections", connection_name, "connection.py"))
    classes = inspect.getmembers(connection_module, inspect.isclass)
    connection_classes = list(filter(lambda x: re.match("\\w+Connection", x[0]), classes))
    name_to_class = dict(connection_classes)
    connection_class_name = cast(str, connection_config.class_name)
    logger.debug("Processing connection {}".format(connection_class_name))
    connection_class = name_to_class.get(connection_class_name, None)
    if connection_class is None:
        raise AEAConfigException("Connection class '{}' not found.".format(connection_class_name))

    connection = connection_class.from_config(address, connection_config)
    return connection


@click.command()
@click.option('--connections', "connection_names", cls=ConnectionsOption, required=False, default=None,
              help="The connection names to use for running the agent. Must be declared in the agent's configuration file.")
@click.option('--env', 'env_file', type=click.Path(), required=False, default=".env",
              help="Specify an environment file (default: .env)")
@click.option('--install-deps', 'install_deps', is_flag=True, required=False, default=False,
              help="Install all the dependencies before running the agent.")
@pass_context
def run(click_context, connection_names: List[str], env_file: str, install_deps: bool):
    """Run the agent."""
    ctx = cast(Context, click_context.obj)
    _try_to_load_agent_config(ctx)
    _load_env_file(env_file)
    agent_name = cast(str, ctx.agent_config.agent_name)

    _verify_or_create_private_keys(ctx)
    _verify_ledger_apis_access()
    private_key_paths = dict([(identifier, config.path) for identifier, config in ctx.agent_config.private_key_paths.read_all()])
    ledger_api_configs = dict([(identifier, cast(List[Union[str, int]], list(config.values()))) for identifier, config in ctx.agent_config.ledger_apis.read_all()])

    wallet = Wallet(private_key_paths)
    ledger_apis = LedgerApis(ledger_api_configs, ctx.agent_config.default_ledger)

    default_connection_name = PublicId.from_string(ctx.agent_config.default_connection).name
    connection_names = [default_connection_name] if connection_names is None else connection_names
    connections = []
    _try_to_load_protocols(ctx)
    try:
        for connection_name in connection_names:
            connection = _setup_connection(connection_name, wallet.addresses[ctx.agent_config.default_ledger], ctx)
            connections.append(connection)
    except AEAConfigException as e:
        logger.error(str(e))
        sys.exit(1)

    if install_deps:
        if Path("requirements.txt").exists():
            click_context.invoke(install, requirement="requirements.txt")
        else:
            click_context.invoke(install)

    agent = AEA(agent_name, connections, wallet, ledger_apis, resources=Resources(str(Path("."))))
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")  # pragma: no cover
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    finally:
        agent.stop()
