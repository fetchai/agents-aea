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
from typing import List, cast

import click
from click import pass_context

from aea import __version__
from aea.aea import AEA
from aea.cli.common import (
    AEAConfigException,
    AEA_LOGO,
    ConnectionsOption,
    Context,
    _load_env_file,
    _verify_or_create_private_keys,
    logger,
    try_to_load_agent_config,
)
from aea.cli.install import install
from aea.configurations.base import (
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    PublicId,
)
from aea.connections.base import Connection
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.helpers.base import (
    add_agent_component_module_to_sys_modules,
    load_agent_component_package,
    load_module,
)
from aea.identity.base import Identity
from aea.registries.resources import Resources


AEA_DIR = str(Path("."))


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
    _try_to_load_required_protocols(ctx)
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


def _try_to_load_required_protocols(ctx: Context):
    for protocol_public_id in ctx.agent_config.protocols:
        protocol_name = protocol_public_id.name
        protocol_author = protocol_public_id.author
        logger.debug("Processing protocol {}".format(protocol_public_id))
        protocol_dir = Path(
            "vendor", protocol_public_id.author, "protocols", protocol_name
        )
        if not protocol_dir.exists():
            protocol_dir = Path("protocols", protocol_name)

        try:
            ctx.protocol_loader.load(open(protocol_dir / DEFAULT_PROTOCOL_CONFIG_FILE))
        except FileNotFoundError:
            logger.error(
                "Protocol configuration file for protocol {} not found.".format(
                    protocol_name
                )
            )
            sys.exit(1)

        try:
            protocol_package = load_agent_component_package(
                "protocol", protocol_name, protocol_author, protocol_dir
            )
            add_agent_component_module_to_sys_modules(
                "protocol", protocol_name, protocol_author, protocol_package
            )
        except Exception:
            logger.error(
                "A problem occurred while processing protocol {}.".format(
                    protocol_public_id
                )
            )
            sys.exit(1)


def _validate_aea(ctx: Context) -> None:
    """
    Validate aea project.

    :param ctx: the context
    """
    try_to_load_agent_config(ctx)
    _verify_or_create_private_keys(ctx)


def _prepare_environment(click_context, env_file: str, is_install_deps: bool) -> None:
    """
    Prepare the AEA project environment.

    :param click_context: the click context
    :param env_file: the path to the envrionemtn file.
    :param is_install_deps: whether to install the dependencies
    """
    _load_env_file(env_file)
    if is_install_deps:
        if Path("requirements.txt").exists():
            click_context.invoke(install, requirement="requirements.txt")
        else:
            click_context.invoke(install)


def _build_aea(ctx: Context, connection_ids: List[PublicId]) -> AEA:
    """
    Build the aea.

    :param ctx: the context
    :param connection_ids: the list of connection ids
    """
    agent_name = cast(str, ctx.agent_config.agent_name)

    wallet = Wallet(ctx.agent_config.private_key_paths_dict)

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

    ledger_apis = LedgerApis(
        ctx.agent_config.ledger_apis_dict, ctx.agent_config.default_ledger
    )

    all_connection_ids = ctx.agent_config.connections
    connection_ids = all_connection_ids if connection_ids is None else connection_ids
    connections = []
    try:
        for connection_id in connection_ids:
            connection = _setup_connection(connection_id, identity.address, ctx)
            connections.append(connection)
    except AEAConfigException as e:
        logger.error(str(e))
        sys.exit(1)

    resources = Resources(AEA_DIR)

    aea = AEA(
        identity, connections, wallet, ledger_apis, resources, is_programmatic=False,
    )
    return aea


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

    _validate_aea(ctx)

    _prepare_environment(click_context, env_file, is_install_deps)

    aea = _build_aea(ctx, connection_ids)

    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo("{} starting ...".format(ctx.agent_config.agent_name))
    try:
        aea.start()
    except KeyboardInterrupt:
        click.echo(
            " {} interrupted!".format(ctx.agent_config.agent_name)
        )  # pragma: no cover
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    finally:
        click.echo("{} stopping ...".format(ctx.agent_config.agent_name))
        aea.stop()
