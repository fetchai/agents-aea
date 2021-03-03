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
"""Module wrapping the helpers of public and private key cryptography."""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from aea.configurations.base import AgentConfig
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.registries import crypto_registry, make_crypto, make_faucet_api
from aea.crypto.wallet import Wallet
from aea.helpers.base import ensure_dir
from aea.helpers.env_vars import is_env_variable


_default_logger = logging.getLogger(__name__)

_ = PRIVATE_KEY_PATH_SCHEMA  # some modules expect this here


def try_validate_private_key_path(
    ledger_id: str, private_key_path: str, exit_on_error: bool = True
) -> None:
    """
    Try validate a private key path.

    :param ledger_id: one of 'fetchai', 'ethereum'
    :param private_key_path: the path to the private key.
    :return: None
    :raises: ValueError if the identifier is invalid.
    """
    try:
        # to validate the file, we just try to create a crypto object
        # with private_key_path as parameter
        make_crypto(ledger_id, private_key_path=private_key_path)
    except Exception as e:  # pylint: disable=broad-except  # thats ok, will exit or reraise
        error_msg = "This is not a valid private key file: '{}'\n Exception: '{}'".format(
            private_key_path, e
        )
        if exit_on_error:
            _default_logger.exception(error_msg)  # show exception traceback on exit
            sys.exit(1)
        else:  # pragma: no cover
            _default_logger.error(error_msg)
            raise


def create_private_key(ledger_id: str, private_key_file: str) -> None:
    """
    Create a private key for the specified ledger identifier.

    :param ledger_id: the ledger identifier.
    :param private_key_file: the private key file.
    :return: None
    :raises: ValueError if the identifier is invalid.
    """
    crypto = make_crypto(ledger_id)
    with open(private_key_file, "wb") as fp:
        crypto.dump(fp)


def try_generate_testnet_wealth(
    identifier: str, address: str, url: Optional[str] = None, _sync: bool = True
) -> None:
    """
    Try generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :param url: the url
    :param _sync: whether to wait to sync or not; currently unused
    :return: None
    """
    faucet_api = make_faucet_api(identifier)
    if faucet_api is not None:
        faucet_api.get_wealth(address, url)


def private_key_verify_or_create(
    aea_conf: AgentConfig, aea_project_path: Path, create_keys: bool = True
) -> None:
    """
    Check key or create if none present.

    :param aea_conf: AgentConfig
    :param aea_project_path: Path, where project placed.

    :return: None
    """
    for identifier, _ in aea_conf.private_key_paths.read_all():
        if identifier not in crypto_registry.supported_ids:  # pragma: nocover
            raise ValueError(
                "Unsupported identifier `{}` in private key paths. Supported identifiers: {}.".format(
                    identifier, sorted(crypto_registry.supported_ids)
                )
            )

    for identifier in crypto_registry.supported_ids:
        config_private_key_path = aea_conf.private_key_paths.read(identifier)

        if is_env_variable(config_private_key_path):
            # config_private_key_path is env vaariable to be used, skip it. check will be performed after substitution
            continue

        if config_private_key_path is None:
            private_key_path = PRIVATE_KEY_PATH_SCHEMA.format(identifier)
            if identifier == aea_conf.default_ledger:  # pragma: nocover
                if os.path.exists(private_key_path):
                    raise ValueError(
                        "File {} for private key {} already exists. Add to aea-config.yaml.".format(
                            repr(config_private_key_path), identifier
                        )
                    )
                if create_keys:
                    create_private_key(
                        identifier,
                        private_key_file=str(aea_project_path / private_key_path),
                    )
                    aea_conf.private_key_paths.update(identifier, private_key_path)
        else:
            try:
                try_validate_private_key_path(
                    identifier,
                    str(aea_project_path / config_private_key_path),
                    exit_on_error=False,  # do not exit process
                )
            except FileNotFoundError:  # pragma: no cover
                raise ValueError(
                    "File {} for private key {} not found.".format(
                        repr(config_private_key_path), identifier,
                    )
                )


def make_certificate(
    ledger_id: str, crypto_private_key_path: str, message: bytes, output_path: str
) -> str:
    """Create certificate."""
    crypto = crypto_registry.make(ledger_id, private_key_path=crypto_private_key_path)
    signature = crypto.sign_message(message).encode("ascii").hex()
    ensure_dir(os.path.dirname(output_path))
    Path(output_path).write_bytes(signature.encode("ascii"))
    return signature


def get_wallet_from_agent_config(agent_config: AgentConfig) -> Wallet:
    """Get wallet from agent_cofig provided."""
    private_key_paths: Dict[str, Optional[str]] = {
        config_pair[0]: config_pair[1]
        for config_pair in agent_config.private_key_paths.read_all()
    }
    connections_private_key_paths: Dict[str, Optional[str]] = {
        config_pair[0]: config_pair[1]
        for config_pair in agent_config.connection_private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths, connections_private_key_paths)
    return wallet
