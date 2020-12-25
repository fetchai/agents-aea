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

from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.registries import make_crypto, make_faucet_api


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
