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

"""Module wrapping the ledger sdk of public and private key cryptography."""
import logging

from fetchai.ledger.crypto import Entity, Identity
import cryptography.hazmat.primitives.serialization

TEMP_PRIVATE_KEY_FILE = 'temp_private_key.pem'

logger = logging.getLogger(__name__)


def _create_temporary_private_key() -> bytes:
    """
    Create a temporary private key.

    :return: the private key in pem format.
    """
    crypto = Entity()
    pem = crypto.private_key_hex.encode()
    return pem


def _try_validate_private_key_pem_path(private_key_pem_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_pem_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        Entity(Identity.from_hex(private_key_pem_path))

    except ValueError:
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


def _create_key_pem_path(private_key: str) -> None:
    file = open(TEMP_PRIVATE_KEY_FILE, "w+")
    file.write(private_key)

    file.close()
