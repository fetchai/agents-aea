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
from typing import Optional

import requests

import aea.crypto
from aea.crypto.cosmos import COSMOS
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

COSMOS_PRIVATE_KEY_FILE = "cosmos_private_key.txt"
FETCHAI_PRIVATE_KEY_FILE = "fet_private_key.txt"
ETHEREUM_PRIVATE_KEY_FILE = "eth_private_key.txt"
FETCHAI_TESTNET_FAUCET_URL = "https://explore-testnet.fetch.ai/api/v1/send_tokens/"
ETHEREUM_TESTNET_FAUCET_URL = "https://faucet.ropsten.be/donate/"
TESTNETS = {FETCHAI: "testnet", ETHEREUM: "ropsten", COSMOS: "testnet"}
IDENTIFIER_TO_KEY_FILES = {
    COSMOS: COSMOS_PRIVATE_KEY_FILE,
    ETHEREUM: ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI: FETCHAI_PRIVATE_KEY_FILE,
}

logger = logging.getLogger(__name__)


def _try_validate_private_key_path(
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
        aea.crypto.make(ledger_id, private_key_path=private_key_path)
    except Exception as e:
        logger.error(
            "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                private_key_path, e
            )
        )
        if exit_on_error:
            sys.exit(1)
        else:
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
    crypto = aea.crypto.make(ledger_id)
    crypto.dump(open(private_key_file, "wb"))


# TODO replace the If-This-Then-That paradigm
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
