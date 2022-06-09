# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from pathlib import Path
from typing import Dict, Optional, Union

from aea.configurations.base import AgentConfig
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.registries import crypto_registry, make_crypto, make_faucet_api
from aea.crypto.wallet import Wallet
from aea.helpers.base import ensure_dir
from aea.helpers.env_vars import is_env_variable


_default_logger = logging.getLogger(__name__)

_ = PRIVATE_KEY_PATH_SCHEMA  # some modules expect this here


def try_validate_private_key_path(
    ledger_id: str,
    private_key_path: str,
    password: Optional[str] = None,
) -> None:
    """
    Try validate a private key path.

    :param ledger_id: one of 'fetchai', 'ethereum'
    :param private_key_path: the path to the private key.
    :param password: the password to encrypt/decrypt the private key.
    :raises: ValueError if the identifier is invalid.
    """
    try:
        # to validate the file, we just try to create a crypto object
        # with private_key_path as parameter
        make_crypto(ledger_id, private_key_path=private_key_path, password=password)
    except Exception as e:  # pylint: disable=broad-except  # thats ok, reraise
        error_msg = (
            "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                private_key_path, e
            )
        )
        _default_logger.error(error_msg)
        raise


def create_private_key(
    ledger_id: str,
    private_key_file: str,
    password: Optional[str] = None,
    extra_entropy: Union[str, bytes, int] = "",
) -> None:
    """
    Create a private key for the specified ledger identifier.

    :param ledger_id: the ledger identifier.
    :param private_key_file: the private key file.
    :param password: the password to encrypt/decrypt the private key.
    :param extra_entropy: add extra randomness to whatever randomness your OS can provide
    :raises: ValueError if the identifier is invalid.
    """
    crypto = make_crypto(ledger_id, extra_entropy=extra_entropy)
    crypto.dump(private_key_file, password)


def try_generate_testnet_wealth(
    identifier: str, address: str, url: Optional[str] = None, _sync: bool = True
) -> None:
    """
    Try generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :param url: the url
    :param _sync: whether to wait to sync or not; currently unused
    """
    faucet_api = make_faucet_api(identifier)
    if faucet_api is not None:
        faucet_api.get_wealth(address, url)


def private_key_verify(
    aea_conf: AgentConfig,
    aea_project_path: Path,
    password: Optional[str] = None,
) -> None:
    """
    Check key.

    :param aea_conf: AgentConfig
    :param aea_project_path: Path, where project placed.
    :param password: the password to encrypt/decrypt the private key.
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
            # config_private_key_path is env variable to be used, skip it. check will be performed after substitution
            continue

        if config_private_key_path is None:
            continue
        try:
            try_validate_private_key_path(
                identifier,
                str(aea_project_path / config_private_key_path),
                password=password,
            )
        except FileNotFoundError:  # pragma: no cover
            raise ValueError(
                "File {} for private key {} not found.".format(
                    repr(config_private_key_path),
                    identifier,
                )
            )


def make_certificate(
    ledger_id: str,
    crypto_private_key_path: str,
    message: bytes,
    output_path: str,
    password: Optional[str] = None,
) -> str:
    """
    Create certificate.

    :param ledger_id: the ledger id
    :param crypto_private_key_path: the path to the private key.
    :param message: the message to be signed.
    :param output_path: the location where to save the certificate.
    :param password: the password to encrypt/decrypt the private keys.
    :return: the signature/certificate
    """
    crypto = crypto_registry.make(
        ledger_id, private_key_path=crypto_private_key_path, password=password
    )
    signature = crypto.sign_message(message).encode("ascii").hex()
    ensure_dir(os.path.dirname(output_path))
    Path(output_path).write_bytes(signature.encode("ascii"))
    return signature


def get_wallet_from_agent_config(
    agent_config: AgentConfig, password: Optional[str] = None
) -> Wallet:
    """
    Get wallet from agent_cofig provided.

    :param agent_config: the agent configuration object
    :param password: the password to encrypt/decrypt the private keys.
    :return: wallet
    """
    private_key_paths: Dict[str, Optional[str]] = {
        config_pair[0]: config_pair[1]
        for config_pair in agent_config.private_key_paths.read_all()
    }
    connections_private_key_paths: Dict[str, Optional[str]] = {
        config_pair[0]: config_pair[1]
        for config_pair in agent_config.connection_private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths, connections_private_key_paths, password=password)
    return wallet


class DecryptError(ValueError):
    """Error on bytes decryption with password."""

    msg = "Decrypt error! Bad password?"

    def __init__(self, msg: Optional[str] = None) -> None:
        """Init exception."""
        super().__init__(msg or self.msg)


class KeyIsIncorrect(ValueError):
    """Error decoding hex string to bytes for private key."""


def hex_to_bytes_for_key(data: str) -> bytes:
    """Convert hex string to bytes with error handling."""
    try:
        return bytes.fromhex(data)
    except ValueError as e:
        raise KeyIsIncorrect(str(e)) from e
