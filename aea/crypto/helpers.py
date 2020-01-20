# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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

from eth_account import Account  # type: ignore

from fetchai.ledger.crypto import Entity  # type: ignore

from web3 import Web3

from aea.crypto.default import DefaultCrypto
from aea.mail.base import Address

DEFAULT_PRIVATE_KEY_FILE = "default_private_key.pem"
FETCHAI_PRIVATE_KEY_FILE = "fet_private_key.txt"
ETHEREUM_PRIVATE_KEY_FILE = "eth_private_key.txt"

logger = logging.getLogger(__name__)


def _try_validate_private_key_pem_path(private_key_pem_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_pem_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        DefaultCrypto(private_key_pem_path=private_key_pem_path)
    except ValueError:
        logger.error(
            "This is not a valid private key file: '{}'".format(private_key_pem_path)
        )
        sys.exit(1)


def _try_validate_fet_private_key_path(private_key_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        with open(private_key_path, "r") as key:
            data = key.read()
            Entity.from_hex(data)
    except ValueError:
        logger.error(
            "This is not a valid private key file: '{}'".format(private_key_path)
        )
        sys.exit(1)


def _try_validate_ethereum_private_key_path(private_key_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        with open(private_key_path, "r") as key:
            data = key.read()
            Account.from_key(data)
    except ValueError:
        logger.error(
            "This is not a valid private key file: '{}'".format(private_key_path)
        )
        sys.exit(1)


def _validate_private_key_path(private_key_path: str, ledger_id: str):
    """
    Validate a private key path.

    :param private_key_path: the path to the private key.
    :param ledger_id: one of 'fetchai', 'ethereum', 'default'
    :return: None
    :raises: ValueError if the private key is invalid.
    """
    if ledger_id == "default":
        _try_validate_private_key_pem_path(private_key_path)
    elif ledger_id == "fetchai":
        _try_validate_fet_private_key_path(private_key_path)
    elif ledger_id == "ethereum":
        _try_validate_ethereum_private_key_path(private_key_path)
    else:
        raise ValueError(
            "Ledger id {} is not valid.".format(repr(ledger_id))
        )  # pragma: no cover


def _create_default_private_key() -> None:
    """
    Create a default private key.

    :return: None
    """
    crypto = DefaultCrypto()
    with open(DEFAULT_PRIVATE_KEY_FILE, "wb") as file:
        file.write(crypto.private_key_pem)


def _create_fetchai_private_key() -> None:
    """
    Create a fetchai private key.

    :return: None
    """
    entity = Entity()
    with open(FETCHAI_PRIVATE_KEY_FILE, "w+") as file:
        file.write(entity.private_key_hex)


def _create_ethereum_private_key() -> None:
    """
    Create an ethereum private key.

    :return: None
    """
    account = Account.create()
    with open(ETHEREUM_PRIVATE_KEY_FILE, "w+") as file:
        file.write(account.key.hex())


def _generate_ethereum_random_message(
    nonce: int, seller: Address, client: Address, time_stamp: int
) -> str:
    """
    Generate a random str message in order to validate a transaction.

    :param nonce: A integer to use for the hash.
    :param seller: the address of the seller.
    :param client: the address of the client.
    :return: return the hash in hex.
    """
    aggregate_hash = Web3.keccak(
        b"".join(
            [
                nonce.to_bytes(32, "big"),
                seller.encode(),
                client.encode(),
                time_stamp.to_bytes(32, "big"),
            ]
        )
    )
    return aggregate_hash.hex()
