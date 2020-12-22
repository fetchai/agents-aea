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

"""Implementation of the 'aea issue_certificates' subcommand."""
from pathlib import Path
from typing import cast

import click
from click import ClickException

from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_package_path_unified
from aea.configurations.base import ConnectionConfig, PublicId
from aea.configurations.constants import CONNECTION
from aea.crypto.registries import crypto_registry
from aea.exceptions import enforce
from aea.helpers.base import CertRequest


@click.command()
@click.pass_context
@check_aea_project
def issue_certificates(click_context):
    """Issue certificates for connections that require them."""
    ctx = cast(Context, click_context.obj)

    for connection_id in ctx.agent_config.connections:
        _process_connection(ctx, connection_id)

    click.echo("Done!")


def _process_certificate(ctx: Context, cert_request: CertRequest):
    """Process a single certificate request."""
    click.echo(f"Issuing certificate '{cert_request.identifier}'...")
    ledger_id = cert_request.ledger_id
    output_path = cert_request.path
    if cert_request.key_identifier is not None:
        key_identifier = cert_request.key_identifier
        connection_private_key_path = ctx.agent_config.connection_private_key_paths.read(
            key_identifier
        )
        if connection_private_key_path is None:
            raise ClickException(
                f"Cannot find connection private key with id '{key_identifier}'"
            )
        connection_crypto = crypto_registry.make(
            key_identifier, private_key_path=connection_private_key_path
        )
        public_key = connection_crypto.public_key
    else:
        public_key = cast(str, cert_request.public_key)
        enforce(
            public_key is not None,
            "Internal error - one of key_identifier or public_key must be not None.",
        )
    public_key_bytes = public_key.encode("ascii")
    identifier = cert_request.identifier.encode("ascii")
    not_before = cert_request.not_before_string.encode("ascii")
    not_after = cert_request.not_after_string.encode("ascii")
    crytpo_private_key_path = ctx.agent_config.connection_private_key_paths.read(
        ledger_id
    )
    if crytpo_private_key_path is None:
        raise ClickException(f"Cannot find private key with id '{ledger_id}'")
    crypto = crypto_registry.make(ledger_id, private_key_path=crytpo_private_key_path)
    message = public_key_bytes + identifier + not_before + not_after
    signature = crypto.sign_message(message).encode("ascii")
    Path(output_path).write_bytes(signature)
    click.echo(f"Dumped certificate in '{output_path}'.")


def _process_connection(ctx: Context, connection_id: PublicId):
    click.echo(f"Processing connection '{connection_id}'...")
    path = get_package_path_unified(ctx, CONNECTION, connection_id)
    connection_config = cast(ConnectionConfig, load_item_config(CONNECTION, Path(path)))
    if (
        connection_config.cert_requests is None
        or len(connection_config.cert_requests) == 0
    ):
        click.echo("No certificates to process.")
        return

    for cert_request in connection_config.cert_requests:
        _process_certificate(ctx, cert_request)
