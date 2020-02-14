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

import json
import logging
import sys

from eth_account import Account  # type: ignore

from fetchai.ledger.crypto import Entity  # type: ignore

import requests

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

FETCHAI_PRIVATE_KEY_FILE = "fet_private_key.txt"
ETHEREUM_PRIVATE_KEY_FILE = "eth_private_key.txt"
FETCHAI_TESTNET_FAUCET_URL = "https://explore-testnet.fetch.ai/api/v1/send_tokens/"
ETHEREUM_TESTNET_FAUCET_URL = "https://faucet.ropsten.be/donate/"
TESTNETS = {FETCHAI: "testnet", ETHEREUM: "ropsten"}

logger = logging.getLogger(__name__)


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
    except Exception as e:
        logger.error(
            "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                private_key_path, e
            )
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
    except Exception as e:
        logger.error(
            "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                private_key_path, e
            )
        )
        sys.exit(1)


def _validate_private_key_path(private_key_path: str, ledger_id: str):
    """
    Validate a private key path.

    :param private_key_path: the path to the private key.
    :param ledger_id: one of 'fetchai', 'ethereum'
    :return: None
    :raises: ValueError if the private key is invalid.
    """
    if ledger_id == "fetchai":
        _try_validate_fet_private_key_path(private_key_path)
    elif ledger_id == "ethereum":
        _try_validate_ethereum_private_key_path(private_key_path)
    else:
        raise ValueError(
            "Ledger id {} is not valid.".format(repr(ledger_id))
        )  # pragma: no cover


def _create_fetchai_private_key(private_key_file: str = FETCHAI_PRIVATE_KEY_FILE) -> None:
    """
    Create a fetchai private key.

    :return: None
    """
    entity = Entity()
    with open(private_key_file, "w+") as file:
        file.write(entity.private_key_hex)


def _create_ethereum_private_key(private_key_file: str = ETHEREUM_PRIVATE_KEY_FILE) -> None:
    """
    Create an ethereum private key.

    :return: None
    """
    account = Account.create()
    with open(private_key_file, "w+") as file:
        file.write(account.key.hex())


def _try_generate_testnet_wealth(identifier: str, address: str) -> None:
    """
    Generate wealth on a testnet.

    :param identifier: the identifier of the ledger
    :param address: the address to check for
    :return: None
    """
    try:

        if identifier == FETCHAI:
            payload = json.dumps({"address": address})
            response = requests.post(FETCHAI_TESTNET_FAUCET_URL, data=payload)
            if response.status_code // 100 == 5:
                logger.error("Response: {}".format(response.status_code))
            else:
                response_dict = json.loads(response.text)
                if response_dict.get("error_message") is not None:
                    logger.warning(
                        "Response: {}\nMessage: {}".format(
                            response.status_code, response_dict.get("error_message")
                        )
                    )
                else:
                    logger.info(
                        "Response: {}\nMessage: {}\nDigest: {}".format(
                            response.status_code,
                            response_dict.get("message"),
                            response_dict.get("digest"),
                        )
                    )  # pragma: no cover
        elif identifier == ETHEREUM:
            response = requests.get(ETHEREUM_TESTNET_FAUCET_URL + address)
            if response.status_code // 100 == 5:
                logger.error("Response: {}".format(response.status_code))
            elif response.status_code // 100 in [3, 4]:
                response_dict = json.loads(response.text)
                logger.warning(
                    "Response: {}\nMessage: {}".format(
                        response.status_code, response_dict.get("message")
                    )
                )
            elif response.status_code // 100 == 2:
                response_dict = json.loads(response.text)
                logger.info(
                    "Response: {}\nMessage: {}".format(
                        response.status_code, response_dict.get("message")
                    )
                )  # pragma: no cover
    except Exception as e:
        logger.warning(
            "An error occured while attempting to generate wealth:\n{}".format(e)
        )
        sys.exit(1)
