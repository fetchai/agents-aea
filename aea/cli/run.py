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
import re
import sys
from pathlib import Path
from typing import Dict, List, Union, cast

import click
from click import pass_context

from aea.aea import AEA
from aea.cli.common import (
    AEAConfigException,
    ConnectionsOption,
    Context,
    _load_env_file,
    _try_to_load_protocols,
    _validate_config_consistency,
    logger,
    try_to_load_agent_config,
)
from aea.cli.install import install
from aea.configurations.base import (
    AgentConfig,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    PublicId,
)
from aea.configurations.loader import ConfigLoader
from aea.connections.base import Connection
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import (
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
    _create_ethereum_private_key,
    _create_fetchai_private_key,
    _try_validate_ethereum_private_key_path,
    _try_validate_fet_private_key_path,
)
from aea.crypto.ledger_apis import (
    LedgerApis,
    SUPPORTED_LEDGER_APIS,
    _try_to_instantiate_ethereum_ledger_api,
    _try_to_instantiate_fetchai_ledger_api,
)
from aea.crypto.wallet import SUPPORTED_CRYPTOS, Wallet
from aea.helpers.base import (
    add_agent_component_module_to_sys_modules,
    load_agent_component_package,
    load_module,
)
from aea.identity.base import Identity
from aea.registries.base import Resources


def _verify_or_create_private_keys(ctx: Context) -> None:
    """
    Verify or create private keys.

    :param ctx: Context
    """
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = path.open(mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, _value in aea_conf.private_key_paths.read_all():
        if identifier not in SUPPORTED_CRYPTOS:
            ValueError("Unsupported identifier in private key paths.")

    fetchai_private_key_path = aea_conf.private_key_paths.read(FETCHAI)
    if fetchai_private_key_path is None:
        _create_fetchai_private_key()
        aea_conf.private_key_paths.update(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
    else:
        try:
            _try_validate_fet_private_key_path(fetchai_private_key_path)
        except FileNotFoundError:  # pragma: no cover
            logger.error(
                "File {} for private key {} not found.".format(
                    repr(fetchai_private_key_path), FETCHAI,
                )
            )
            sys.exit(1)

    ethereum_private_key_path = aea_conf.private_key_paths.read(ETHEREUM)
    if ethereum_private_key_path is None:
        _create_ethereum_private_key()
        aea_conf.private_key_paths.update(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
    else:
        try:
            _try_validate_ethereum_private_key_path(ethereum_private_key_path)
        except FileNotFoundError:  # pragma: no cover
            logger.error(
                "File {} for private key {} not found.".format(
                    repr(ethereum_private_key_path), ETHEREUM,
                )
            )
            sys.exit(1)

    # update aea config
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    fp = path.open(mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)
    ctx.agent_config = aea_conf


def _verify_ledger_apis_access() -> None:
    """Verify access to ledger apis."""
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = path.open(mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, _value in aea_conf.ledger_apis.read_all():
        if identifier not in SUPPORTED_LEDGER_APIS:
            ValueError("Unsupported identifier in ledger apis.")

    fetchai_ledger_api_config = aea_conf.ledger_apis.read(FETCHAI)
    if fetchai_ledger_api_config is None:
        logger.debug("No fetchai ledger api config specified.")
    else:
        network = cast(str, fetchai_ledger_api_config.get("network"))
        host = cast(str, fetchai_ledger_api_config.get("host"))
        port = cast(int, fetchai_ledger_api_config.get("port"))
        if network is not None:
            _try_to_instantiate_fetchai_ledger_api(network=network)
        elif host is not None and port is not None:
            _try_to_instantiate_fetchai_ledger_api(host=host, port=port)
        else:  # pragma: no cover
            raise ValueError("Either network or host and port must be specified.")
    ethereum_ledger_config = aea_conf.ledger_apis.read(ETHEREUM)
    if ethereum_ledger_config is None:
        logger.debug("No ethereum ledger api config specified.")
    else:
        address = cast(str, ethereum_ledger_config.get("address"))
        if address is not None:
            _try_to_instantiate_ethereum_ledger_api(address)
        else:  # pragma: no cover
            raise ValueError("Address must be specified.")


def _setup_connection(
    connection_public_id: PublicId, address: str, ctx: Context
) -> Connection:
    """
    Set up a connection.

    :param connection_public_id: the public id of the connection.
    :param ctx: the CLI context object.
    :param address: the address.
    :return: a Connection object.
    :raises AEAConfigException: if the connection name provided as argument is not declared in the configuration file,
                              | or if the connection type is not supported by the framework.
    """
    # TODO handle the case when there are multiple connections with the same name
    supported_connection_ids = ctx.agent_config.connections
    if connection_public_id not in supported_connection_ids:
        raise AEAConfigException(
            "Connection id '{}' not declared in the configuration file.".format(
                connection_public_id
            )
        )
    connection_dir = Path(
        "vendor", connection_public_id.author, "connections", connection_public_id.name
    )
    if not connection_dir.exists():
        connection_dir = Path("connections", connection_public_id.name)

    try:
        connection_config = ctx.connection_loader.load(
            open(connection_dir / DEFAULT_CONNECTION_CONFIG_FILE)
        )
    except FileNotFoundError:
        raise AEAConfigException(
            "Connection config for '{}' not found.".format(connection_public_id)
        )

    connection_package = load_agent_component_package(
        "connection",
        connection_public_id.name,
        connection_config.author,
        connection_dir,
    )
    add_agent_component_module_to_sys_modules(
        "connection",
        connection_public_id.name,
        connection_config.author,
        connection_package,
    )
    try:
        connection_module = load_module(
            "connection_module", connection_dir / "connection.py"
        )
    except FileNotFoundError:
        raise AEAConfigException(
            "Connection '{}' not found.".format(connection_public_id)
        )
    classes = inspect.getmembers(connection_module, inspect.isclass)
    connection_classes = list(
        filter(lambda x: re.match("\\w+Connection", x[0]), classes)
    )
    name_to_class = dict(connection_classes)
    connection_class_name = cast(str, connection_config.class_name)
    logger.debug("Processing connection {}".format(connection_class_name))
    connection_class = name_to_class.get(connection_class_name, None)
    if connection_class is None:
        raise AEAConfigException(
            "Connection class '{}' not found.".format(connection_class_name)
        )

    connection = connection_class.from_config(address, connection_config)
    return connection


@click.command()
@click.option(
    "--connections",
    "connection_ids",
    cls=ConnectionsOption,
    required=False,
    default=None,
    help="The connection names to use for running the agent. Must be declared in the agent's configuration file.",
)
@click.option(
    "--env",
    "env_file",
    type=click.Path(),
    required=False,
    default=".env",
    help="Specify an environment file (default: .env)",
)
@click.option(
    "--install-deps",
    "is_install_deps",
    is_flag=True,
    required=False,
    default=False,
    help="Install all the dependencies before running the agent.",
)
@pass_context
def run(
    click_context, connection_ids: List[PublicId], env_file: str, is_install_deps: bool
):
    """Run the agent."""
    ctx = cast(Context, click_context.obj)
    try_to_load_agent_config(ctx)
    _validate_config_consistency(ctx)
    _load_env_file(env_file)
    agent_name = cast(str, ctx.agent_config.agent_name)

    _verify_or_create_private_keys(ctx)
    _verify_ledger_apis_access()
    private_key_paths = {
        config_pair[0]: config_pair[1]
        for config_pair in ctx.agent_config.private_key_paths.read_all()
    }
    ledger_api_configs = dict(
        [
            (identifier, cast(Dict[str, Union[str, int]], config))
            for identifier, config in ctx.agent_config.ledger_apis.read_all()
        ]
    )

    wallet = Wallet(private_key_paths)
    if len(wallet.addresses) > 1:
        identity = Identity(
            agent_name,
            addresses=wallet.addresses,
            default_address_key=ctx.agent_config.default_ledger,
        )
    else:  # pragma: no cover
        identity = Identity(
            agent_name, address=wallet.addresses[ctx.agent_config.default_ledger],
        )
    ledger_apis = LedgerApis(ledger_api_configs, ctx.agent_config.default_ledger)

    default_connection_id = PublicId.from_str(ctx.agent_config.default_connection)
    connection_ids = (
        [default_connection_id] if connection_ids is None else connection_ids
    )
    connections = []
    _try_to_load_protocols(ctx)
    try:
        for connection_id in connection_ids:
            connection = _setup_connection(connection_id, identity.address, ctx)
            connections.append(connection)
    except AEAConfigException as e:
        logger.error(str(e))
        sys.exit(1)

    if is_install_deps:
        if Path("requirements.txt").exists():
            click_context.invoke(install, requirement="requirements.txt")
        else:
            click_context.invoke(install)

    agent = AEA(
        identity,
        connections,
        wallet,
        ledger_apis,
        resources=Resources(str(Path("."))),
        is_programmatic=False,
    )
    try:
        agent.start()
    except KeyboardInterrupt:
        click.echo("Interrupted.")  # pragma: no cover
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    finally:
        agent.stop()
