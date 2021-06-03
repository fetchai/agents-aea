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
import re
import typing
from pathlib import Path
from typing import Optional, Tuple, cast

import click
from click import ClickException

from aea.cli.utils.click_utils import PublicIdParameter, password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.base import PublicId
from aea.configurations.constants import CONNECTIONS
from aea.configurations.manager import AgentConfigManager
from aea.crypto.base import Crypto
from aea.crypto.registries import crypto_registry
from aea.exceptions import enforce
from aea.helpers.multiaddr.base import MultiAddr


URI_REGEX = re.compile(r"(?:https?://)?(?P<host>[^:/ ]+):(?P<port>[0-9]*)")


@click.command()
@click.argument(
    "ledger_id",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@password_option()
@click.option("-c", "--connection", is_flag=True)
@click.option(
    "-i", "--connection-id", type=PublicIdParameter(), required=False, default=None,
)
@click.option(
    "-h", "--host-field", type=str, required=False, default=None,
)
@click.option(
    "-p", "--port-field", type=str, required=False, default=None,
)
@click.option(
    "-u", "--uri-field", type=str, required=False, default="public_uri",
)
@click.pass_context
@check_aea_project
def get_multiaddress(
    click_context: click.Context,
    ledger_id: str,
    password: Optional[str],
    connection: bool,
    connection_id: Optional[PublicId],
    host_field: str,
    port_field: str,
    uri_field: str,
) -> None:
    """Get the multiaddress associated with a private key or connection of the agent."""
    address = _try_get_multiaddress(
        click_context,
        ledger_id,
        password,
        connection,
        connection_id,
        host_field,
        port_field,
        uri_field,
    )
    click.echo(address)


def _try_get_multiaddress(
    click_context: click.Context,
    ledger_id: str,
    password: Optional[str] = None,
    is_connection: bool = False,
    connection_id: Optional[PublicId] = None,
    host_field: Optional[str] = None,
    port_field: Optional[str] = None,
    uri_field: str = "public_uri",
) -> str:
    """
    Try to get the multi-address.

    :param click_context: click context object.
    :param ledger_id: the ledger id.
    :param password: the password to encrypt/decrypt the private key.
    :param is_connection: whether the key to load is from the wallet or from connections.
    :param connection_id: the connection id.
    :param host_field: if connection_id specified, the config field to retrieve the host
    :param port_field: if connection_id specified, the config field to retrieve the port
    :param uri_field: uri field

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
    crypto = crypto_registry.make(
        ledger_id, private_key_path=path_to_key, password=password
    )

    if connection_id is None:
        return _try_get_peerid(crypto)
    return _try_get_connection_multiaddress(
        click_context,
        crypto,
        cast(PublicId, connection_id),
        host_field,
        port_field,
        uri_field,
    )


def _try_get_peerid(crypto: Crypto) -> str:
    """Try to get the peer id."""
    try:
        peer_id = MultiAddr("", 0, crypto.public_key).peer_id
        return peer_id
    except Exception as e:
        raise ClickException(str(e))


def _read_host_and_port_from_config(
    connection_config: dict,
    connection_id: PublicId,
    uri_field: str,
    host_field: Optional[str],
    port_field: Optional[str],
) -> Tuple[str, int]:
    """
    Read host and port from config connection.

    :param connection_config: connection configuration.
    :param connection_id: the connection id.
    :param uri_field: the uri field.
    :param host_field: the host field.
    :param port_field: the port field.
    :return: the host and the port.
    """
    host_is_none = host_field is None
    port_is_none = port_field is None
    one_is_none = (not host_is_none and port_is_none) or (
        host_is_none and not port_is_none
    )
    if not host_is_none and not port_is_none:
        if host_field not in connection_config:
            raise ClickException(
                f"Host field '{host_field}' not present in connection configuration {connection_id}"
            )
        if port_field not in connection_config:
            raise ClickException(
                f"Port field '{port_field}' not present in connection configuration {connection_id}"
            )
        host = connection_config[host_field]
        port = int(connection_config[port_field])
        return host, port
    if one_is_none:
        raise ClickException(
            "-h/--host-field and -p/--port-field must be specified together."
        )
    if uri_field not in connection_config:
        raise ClickException(
            f"URI field '{uri_field}' not present in connection configuration {connection_id}"
        )
    url_value = connection_config[uri_field]
    try:
        m = URI_REGEX.search(url_value)
        enforce(m is not None, f"URI Doesn't match regex '{URI_REGEX}'")
        m = cast(typing.Match, m)
        host = m.group("host")
        port = int(m.group("port"))
        return host, port
    except Exception as e:
        raise ClickException(
            f"Cannot extract host and port from {uri_field}: '{url_value}'. Reason: {str(e)}"
        )


def _try_get_connection_multiaddress(
    click_context: click.Context,
    crypto: Crypto,
    connection_id: PublicId,
    host_field: Optional[str],
    port_field: Optional[str],
    uri_field: str,
) -> str:
    """
    Try to get the connection multiaddress.

    The host and the port options have the precedence over the uri option.

    :param click_context: the click context object.
    :param crypto: the crypto.
    :param connection_id: the connection id.
    :param host_field: the host field.
    :param port_field: the port field.
    :param uri_field: the uri field.
    :return: the multiaddress.
    """
    ctx = cast(Context, click_context.obj)
    if connection_id not in ctx.agent_config.connections:
        raise ValueError(f"Cannot find connection with the public id {connection_id}.")

    agent_config_manager = AgentConfigManager.load(ctx.cwd)
    connection_config = cast(
        dict,
        agent_config_manager.get_variable(
            f"vendor.{connection_id.author}.{CONNECTIONS}.{connection_id.name}.config"
        ),
    )

    host, port = _read_host_and_port_from_config(
        connection_config, connection_id, uri_field, host_field, port_field
    )

    try:
        multiaddr = MultiAddr(host, port, crypto.public_key)
        return multiaddr.format()
    except Exception as e:
        raise ClickException(f"An error occurred while creating the multiaddress: {e}")
