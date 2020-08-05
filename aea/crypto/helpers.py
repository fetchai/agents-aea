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
import sys
from pathlib import Path

from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from aea.configurations.loader import ConfigLoader
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.registries import crypto_registry, make_crypto, make_faucet_api

COSMOS_PRIVATE_KEY_FILE = "cosmos_private_key.txt"
FETCHAI_PRIVATE_KEY_FILE = "fet_private_key.txt"
ETHEREUM_PRIVATE_KEY_FILE = "eth_private_key.txt"
IDENTIFIER_TO_KEY_FILES = {
    CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE,
    EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_FILE,
    FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE,
}

logger = logging.getLogger(__name__)


def verify_or_create_private_keys(
    aea_project_path: Path, exit_on_error: bool = True,
) -> AgentConfig:
    """
    Verify or create private keys.

    :param ctx: Context
    """
    path_to_aea_config = aea_project_path / DEFAULT_AEA_CONFIG_FILE
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = path_to_aea_config.open(mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier, _value in aea_conf.private_key_paths.read_all():
        if identifier not in crypto_registry.supported_ids:  # pragma: nocover
            ValueError("Unsupported identifier in private key paths.")

    for identifier, private_key_path in IDENTIFIER_TO_KEY_FILES.items():
        config_private_key_path = aea_conf.private_key_paths.read(identifier)
        if config_private_key_path is None:
            if identifier == aea_conf.default_ledger:  # pragma: nocover
                create_private_key(
                    identifier,
                    private_key_file=str(aea_project_path / private_key_path),
                )
                aea_conf.private_key_paths.update(identifier, private_key_path)
        else:
            try:
                try_validate_private_key_path(
                    identifier,
                    str(aea_project_path / private_key_path),
                    exit_on_error=exit_on_error,
                )
            except FileNotFoundError:  # pragma: no cover
                raise ValueError(
                    "File {} for private key {} not found.".format(
                        repr(private_key_path), identifier,
                    )
                )

    # update aea config
    fp = path_to_aea_config.open(mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)
    return aea_conf


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
            logger.exception(error_msg)  # show exception traceback on exit
            sys.exit(1)
        else:  # pragma: no cover
            logger.error(error_msg)
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
    crypto.dump(open(private_key_file, "wb"))


def try_generate_testnet_wealth(identifier: str, address: str) -> None:
    """
    Try generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :return: None
    """
    faucet_api = make_faucet_api(identifier)
    if faucet_api is not None:
        faucet_api.get_wealth(address)
