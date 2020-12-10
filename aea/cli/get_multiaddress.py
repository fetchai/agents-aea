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

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_package_path_unified
from aea.configurations.base import ConnectionConfig, PublicId
from aea.configurations.constants import CONNECTION
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
    click_context,
    ledger_id: str,
    connection: bool,
    connection_id: Optional[PublicId],
    host_field: str,
    port_field: str,
    uri_field: str,
):
    """Get the multiaddress associated with a private key or connection of the agent."""
    address = _try_get_multiaddress(
        click_context,
        ledger_id,
        connection,
        connection_id,
        host_field,
        port_field,
        uri_field,
    )
    click.echo(address)


def _try_get_multiaddress(
    click_context,
    ledger_id: str,
    is_connection: bool,
    connection_id: Optional[PublicId],
    host_field: str,
    port_field: str,
    uri_field: str,
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
    connection_config: ConnectionConfig,
    uri_field: str,
    host_field: Optional[str],
    port_field: Optional[str],
) -> Tuple[str, int]:
    """
    Read host and port from config connection.

    :param host_field: the host field.
    :param port_field: the port field.
    :param uri_field: the uri field.
    :return: the host and the port.
    """
    host_is_none = host_field is None
    port_is_none = port_field is None
    one_is_none = (not host_is_none and port_is_none) or (
        host_is_none and not port_is_none
    )
    if not host_is_none and not port_is_none:
        if host_field not in connection_config.config:
            raise ClickException(
                f"Host field '{host_field}' not present in connection configuration {connection_config.public_id}"
            )
        if port_field not in connection_config.config:
            raise ClickException(
                f"Port field '{port_field}' not present in connection configuration {connection_config.public_id}"
            )
        host = connection_config.config[host_field]
        port = int(connection_config.config[port_field])
        return host, port
    if one_is_none:
        raise ClickException(
            "-h/--host-field and -p/--port-field must be specified together."
        )
    if uri_field not in connection_config.config:
        raise ClickException(
            f"URI field '{uri_field}' not present in connection configuration {connection_config.public_id}"
        )
    url_value = connection_config.config[uri_field]
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
    click_context,
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

    package_path = Path(get_package_path_unified(ctx, CONNECTION, connection_id))
    connection_config = cast(
        ConnectionConfig, load_item_config(CONNECTION, package_path)
    )

    host, port = _read_host_and_port_from_config(
        connection_config, uri_field, host_field, port_field
    )

    try:
        multiaddr = MultiAddr(host, port, crypto.public_key)
        return multiaddr.format()
    except Exception as e:
        raise ClickException(f"An error occurred while creating the multiaddress: {e}")
