# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from typing import Dict, List, Optional, cast

import click
from click import ClickException

from aea.cli.utils.click_utils import password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import get_dotted_package_path_unified
from aea.configurations.base import AgentConfig, PublicId
from aea.configurations.constants import CONNECTION
from aea.configurations.manager import AgentConfigManager, VariableDoesNotExist
from aea.crypto.helpers import make_certificate
from aea.crypto.registries import crypto_registry
from aea.exceptions import enforce
from aea.helpers.base import CertRequest, prepend_if_not_absolute


@click.command()
@password_option()
@click.option(
    "--aev",
    "apply_environment_variables",
    required=False,
    is_flag=True,
    default=False,
    help="Populate Agent configs from Environment variables.",
)
@click.pass_context
@check_aea_project
def issue_certificates(
    click_context: click.Context,
    apply_environment_variables: bool,
    password: Optional[str],
) -> None:
    """Issue certificates for connections that require them."""
    ctx = cast(Context, click_context.obj)
    agent_config_manager = AgentConfigManager.load(
        ctx.cwd,
        substitude_env_vars=apply_environment_variables,
    )
    issue_certificates_(ctx.cwd, agent_config_manager, password=password)


def issue_certificates_(
    project_directory: str,
    agent_config_manager: AgentConfigManager,
    path_prefix: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """
    Issue certificates for connections that require them.

    :param project_directory: the directory of the project.
    :param agent_config_manager: the agent configuration manager.
    :param path_prefix: the path prefix for "save_path". Defaults to project directory.
    :param password: the password to encrypt/decrypt the private key.
    """
    path_prefix = path_prefix or project_directory
    for connection_id in agent_config_manager.agent_config.connections:
        cert_requests = _get_cert_requests(
            project_directory, agent_config_manager, connection_id
        )
        _process_connection(
            path_prefix, agent_config_manager, cert_requests, connection_id, password
        )

    click.echo("All certificates have been issued.")


def _get_cert_requests(
    project_directory: str, manager: AgentConfigManager, connection_id: PublicId
) -> List[CertRequest]:
    """
    Get certificate requests, taking the overrides into account.

    :param project_directory: aea project directory.
    :param manager: AgentConfigManager
    :param connection_id: the connection id.

    :return: the list of cert requests.
    """
    path = get_dotted_package_path_unified(
        project_directory, manager.agent_config, CONNECTION, connection_id
    )
    path_to_cert_requests = f"{path}.cert_requests"

    try:
        cert_requests = manager.get_variable(path_to_cert_requests)
    except VariableDoesNotExist:
        return []

    cert_requests = cast(List[Dict], cert_requests)
    return [
        CertRequest.from_json(cert_request_json) for cert_request_json in cert_requests
    ]


def _process_certificate(
    path_prefix: str,
    agent_config: AgentConfig,
    cert_request: CertRequest,
    connection_id: PublicId,
    password: Optional[str] = None,
) -> None:
    """Process a single certificate request."""
    ledger_id = cert_request.ledger_id
    if cert_request.key_identifier is not None:
        key_identifier = cert_request.key_identifier
        connection_private_key_path = agent_config.connection_private_key_paths.read(
            key_identifier
        )
        if connection_private_key_path is None:
            raise ClickException(
                f"Cannot find connection private key with id '{key_identifier}'. Connection '{connection_id}' requires this. Please use `aea generate-key {key_identifier} connection_{key_identifier}_private_key.txt` and `aea add-key {key_identifier} connection_{key_identifier}_private_key.txt --connection` to add a connection private key with id '{key_identifier}'."
            )
        new_connection_private_key_path = prepend_if_not_absolute(
            connection_private_key_path, path_prefix
        )
        connection_crypto = crypto_registry.make(
            key_identifier,
            private_key_path=new_connection_private_key_path,
            password=password,
        )
        public_key = connection_crypto.public_key
    else:
        public_key = cast(str, cert_request.public_key)
        enforce(
            public_key is not None,
            "Internal error - one of key_identifier or public_key must be not None.",
        )
    crypto_private_key_path = agent_config.private_key_paths.read(ledger_id)
    if crypto_private_key_path is None:
        raise ClickException(
            f"Cannot find private key with id '{ledger_id}'. Please use `aea generate-key {key_identifier}` and `aea add-key {key_identifier}` to add a private key with id '{key_identifier}'."
        )
    message = cert_request.get_message(public_key)
    output_path = cert_request.get_absolute_save_path(path_prefix)
    absolute_crypto_private_key_path = prepend_if_not_absolute(
        crypto_private_key_path, path_prefix
    )
    cert = make_certificate(
        ledger_id,
        str(absolute_crypto_private_key_path),
        message,
        str(output_path),
        password=password,
    )
    click.echo(f"Generated signature: '{cert}'")
    click.echo(
        f"Dumped certificate '{cert_request.identifier}' in '{output_path}' for connection {connection_id}."
    )


def _process_connection(
    path_prefix: str,
    agent_config_manager: AgentConfigManager,
    cert_requests: List[CertRequest],
    connection_id: PublicId,
    password: Optional[str] = None,
) -> None:
    """Process a single connection."""
    if len(cert_requests) == 0:
        logger.debug("No certificates to process.")
        return

    logger.debug(f"Processing connection '{connection_id}'...")
    for cert_request in cert_requests:
        click.echo(
            f"Issuing certificate '{cert_request.identifier}' for connection {connection_id}..."
        )
        _process_certificate(
            path_prefix,
            agent_config_manager.agent_config,
            cert_request,
            connection_id,
            password,
        )
