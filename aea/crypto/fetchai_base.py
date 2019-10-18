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
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity, Identity, Address  # type: ignore
from pathlib import Path

from aea.crypto.base import Crypto

logger = logging.getLogger(__name__)


class FetchCryptoError(Exception):
    """Exception to be thrown when cryptographic signatures don't match!."""


class FetchCrypto(Crypto):
    """Class wrapping the Entity Generation from Fetch.AI ledger."""

    def __init__(self, private_key_path: Optional[str] = None):
        """Instantiate a crypto object."""
        self._entity = self._generate_private_key() if private_key_path is None else self._load_private_key_from_path(private_key_path)

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self._entity.public_key_hex

    @property
    def private_key(self) -> str:
        """
        Return the private key in hex format.

        :return: a public key string in hex format
        """
        return self._entity.private_key_hex

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: a display_address str
        """
        return str(Address(Identity.from_hex(self.public_key)))

    @property
    def token_balance(self) -> float:
        """Get the token balance."""
        api = LedgerApi("127.0.0.1", 8000)
        token_balance = api.tokens.balance(self.address)
        return token_balance

    def transfer(self, destination_address: str, amount: float, tx_fee: float) -> None:
        """
        Transfer from self to destination.

        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee
        """
        api = LedgerApi("127.0.0.1", 8000)
        api.sync(api.tokens.transfer(self._entity, destination, amount, tx_fee))

    @staticmethod
    def get_address_from_public_key(public_key: str) -> Address:
        """
        Get the address from the public key.

        :return: str
        """
        identity = Identity.from_hex(public_key)
        return Address(identity)

    def sign_transaction(self, message: bytes) -> bytes:
        """
        Sing a transaction to send it to the ledger.

        :param message:
        :return: Signed message in bytes
        """
        signature = self._entity.sign(message)
        return signature

    def _load_private_key_from_path(self, file_name) -> Entity:
        """
        Load a private key in hex format from a file.

        :param path: the path to the hex file.

        :return: the Entity.
        """
        path = Path(file_name)
        try:
            if path.is_file():
                with open(path, "r") as key:
                    data = key.read()
                    entity = Entity.from_hex(data)

            else:
                entity = self._generate_private_key()

            return entity
        except IOError as e:  # pragma: no cover
            logger.exception(str(e))

    def _generate_private_key(self) -> Entity:
        entity = Entity()
        return entity
