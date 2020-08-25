# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Implementation of the 'aea get_multiaddress' subcommand."""
from pathlib import Path
from typing import Optional, cast

import click
from click import ClickException

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_path_to_package_configuration
from aea.configurations.base import (
    ConnectionConfig,
    PublicId,
)
from aea.crypto.base import Crypto
from aea.crypto.registries import crypto_registry
from aea.helpers.multiaddr.base import MultiAddr


@click.command()
@click.argument(
    "ledger_id",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.option("-c", "--connection", is_flag=True)
@click.option(
    "-i", "--connection-id", type=PublicIdParameter(), required=False, default=None,
)
@click.option(
    "-h", "--host-field", type=str, required=False, default="host",
)
@click.option(
    "-p", "--port-field", type=str, required=False, default="port",
)
@click.pass_context
@check_aea_project
def get_multiaddress(
    click_context,
    ledger_id: str,
    connection: bool,
    connection_id: Optional[PublicId],
    host_field: str,
    port_field: str,
):
    """Get the address associated with the private key."""
    address = _try_get_multiaddress(
        click_context, ledger_id, connection, connection_id, host_field, port_field
    )
    click.echo(address)


def _try_get_multiaddress(
    click_context,
    ledger_id: str,
    is_connection: bool,
    connection_id: Optional[PublicId],
    host_field: str,
    port_field: str,
):
    """
    Try to get the multi-address.

    :param click_context: click context object.
    :param ledger_id: the ledger id.
    :param is_connection: whether the key to load is from the wallet or from connections.
    :param connection_id: the connection id.
    :param host_field: if connection_id specified, the config field to retrieve the host
    :param port_field: if connection_id specified, the config field to retrieve the port

    :return: address.
    """
    ctx = cast(Context, click_context.obj)
    # connection_id not None implies is_connection
    is_connection = connection_id is not None or is_connection

    private_key_paths = (
        ctx.agent_config.private_key_paths
        if not is_connection
        else ctx.agent_config.connection_private_key_paths
    )
    private_key_path = private_key_paths.read(ledger_id)

    if private_key_path is None:
        raise ClickException(
            f"Cannot find '{ledger_id}'. Please check {'private_key_path' if not is_connection else 'connection_private_key_paths'}."
        )

    path_to_key = Path(private_key_path)
    crypto = crypto_registry.make(ledger_id, private_key_path=path_to_key)

    if connection_id is None:
        return _try_get_peerid(crypto)
    return _try_get_connection_multiaddress(
        click_context, crypto, cast(PublicId, connection_id), host_field, port_field
    )


def _try_get_peerid(crypto: Crypto) -> str:
    """Try to get the peer id."""
    try:
        peer_id = MultiAddr("", 0, crypto.public_key).peer_id
        return peer_id
    except Exception as e:
        raise ClickException(str(e))


def _try_get_connection_multiaddress(
    click_context,
    crypto: Crypto,
    connection_id: PublicId,
    host_field: str,
    port_field: str,
) -> str:
    """
    Try to get the connection multiaddress.

    :param click_context: the click context object.
    :param crypto: the crypto.
    :param connection_id: the connection id.
    :param host_field: the host field.
    :param port_field: the port field.
    :return: the multiaddress.
    """
    ctx = cast(Context, click_context.obj)
    if connection_id not in ctx.agent_config.connections:
        raise ValueError(f"Cannot find connection with the public id {connection_id}.")

    configuration_path = Path(
        get_path_to_package_configuration(ctx, "connection", connection_id)
    )
    with configuration_path.open() as fp:
        connection_config = cast(ConnectionConfig, ctx.connection_loader.load(fp))

    if host_field not in connection_config.config:
        raise ValueError(
            f"Host field '{host_field}' not present in connection configuration {connection_id}"
        )
    if port_field not in connection_config.config:
        raise ValueError(
            f"Port field '{port_field}' not present in connection configuration {connection_id}"
        )

    host = connection_config.config[host_field]
    port = int(connection_config.config[port_field])

    try:
        multiaddr = MultiAddr(host, port, crypto.public_key)
        return multiaddr.format()
    except Exception as e:
        raise ClickException(f"An error occurred while creating the multiaddress: {e}")
