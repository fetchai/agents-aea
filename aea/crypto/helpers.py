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

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging

from aea.crypto.base import Crypto

TEMP_PRIVATE_KEY_FILE = 'temp_private_key.pem'

logger = logging.getLogger(__name__)


def _create_temporary_private_key() -> str:
    """
    Create a temporary private key.

    :return: the private key in pem format.
    """
    crypto = Crypto()
    pem = crypto._private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())  # type: ignore
    return pem


def _try_validate_private_key_pem_path(private_key_pem_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_pem_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        Crypto(private_key_pem_path=private_key_pem_path)
    except:
        logger.error("This is not a valid private key file: '{}'".format(private_key_pem_path))
        exit(-1)


def _create_temporary_private_key_pem_path() -> str:
    """
    Create a temporary private key and path to the file.

    :return: private_key_pem_path
    """
    pem = _create_temporary_private_key()
    file = open(TEMP_PRIVATE_KEY_FILE, "wb")
    file.write(pem)
    file.close()
    return TEMP_PRIVATE_KEY_FILE
