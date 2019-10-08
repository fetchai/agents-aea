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

"""Module wrapping the public and private key generation from fetch.ai ledger."""

from typing import Optional
import logging
from fetchai.ledger.crypto import Entity, Identity, Address


logger = logging.getLogger(__name__)


class FetchCryptoError(Exception):
    """Exception to be thrown when cryptographic signatures don't match!."""


def _load_private_key_from_path(path):
    """Load the private key from the file"""
    with open( path, "r") as key:
        data = key.read()
        entity = Entity.from_hex(data)
        return entity


class FetchCrypto(object):
    def __init__(self, private_key_path: Optional[str] = None):
        """Instantiate a crypto object."""
        self._entity = Entity() if private_key_path is None else self._load_private_key_from_path(private_key_path)
        self._public_key_obj = self._entity.public_key
        self._public_key_bytes = self._entity.public_key_bytes
        self._public_key_hex = self._entity.public_key_hex
        self._display_address = Address(Identity.from_hex(self._public_key_hex))
        self._private_key = self._entity.private_key
        self._private_key_hex = self._entity.private_key_hex
        self._private_key_bytes = self._entity.private_key_bytes

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self._public_key_hex

    @property
    def display_address(self) -> str:
        """
        Return the display_address for the key pair
        :return: a display_address str
        """
        return self._display_address

    def sign_transaction(self, message: bytes) -> bytes:
        signature = self._entity.sign(message)
        return signature

    @staticmethod
    def _load_private_key_from_path(path) -> Entity:
        """
        Load a private key in hex format from a file.

        :param path: the path to the hex file.

        :return: the Entity.
        """
        try:
            with open(path, "r") as key:
                data = key.read()
                entity = Entity.from_hex(data)
                return entity
        except IOError as e:
            logger.exception(str(e))


if __name__ == "__main__":
    a = FetchCrypto()
    print(a.display_address)


