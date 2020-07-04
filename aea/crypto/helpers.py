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
from typing import Optional

from aea.crypto.cosmos import CosmosCrypto, CosmosFaucetApi
from aea.crypto.ethereum import EthereumCrypto, EthereumFaucetApi
from aea.crypto.fetchai import FetchAICrypto, FetchAIFaucetApi
from aea.crypto.registries import make_crypto

COSMOS_PRIVATE_KEY_FILE = "cosmos_private_key.txt"
FETCHAI_PRIVATE_KEY_FILE = "fet_private_key.txt"
ETHEREUM_PRIVATE_KEY_FILE = "eth_private_key.txt"
TESTNETS = {
    FetchAICrypto.identifier: "testnet",
    EthereumCrypto.identifier: "ropsten",
    CosmosCrypto.identifier: "testnet",
}
IDENTIFIER_TO_KEY_FILES = {
    CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE,
    EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_FILE,
    FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE,
}
IDENTIFIER_TO_FAUCET_APIS = {
    CosmosCrypto.identifier: CosmosFaucetApi(),
    EthereumCrypto.identifier: EthereumFaucetApi(),
    FetchAICrypto.identifier: FetchAIFaucetApi(),
}

logger = logging.getLogger(__name__)


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


def create_private_key(ledger_id: str, private_key_file: Optional[str] = None) -> None:
    """
    Create a private key for the specified ledger identifier.

    :param ledger_id: the ledger identifier.
    :return: None
    :raises: ValueError if the identifier is invalid.
    """
    if private_key_file is None:
        private_key_file = IDENTIFIER_TO_KEY_FILES[ledger_id]
    crypto = make_crypto(ledger_id)
    crypto.dump(open(private_key_file, "wb"))


def try_generate_testnet_wealth(identifier: str, address: str) -> None:
    """
    Try generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :return: None
    """
    faucet_api = IDENTIFIER_TO_FAUCET_APIS.get(identifier, None)
    if faucet_api is not None:
        faucet_api.get_wealth(address)
