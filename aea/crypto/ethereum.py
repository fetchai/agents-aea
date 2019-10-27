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

"""Ethereum module wrapping the public and private key cryptography and ledger api."""

from eth_account.messages import encode_defunct  # type: ignore
from web3 import Web3       # type: ignore
from eth_account import Account     # type: ignore
from eth_keys import keys       # type: ignore
import logging
from pathlib import Path
from typing import Optional

from aea.crypto.base import Crypto

logger = logging.getLogger(__name__)

ETHEREUM = "ethereum"


class EthereumCrypto(Crypto):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = ETHEREUM

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        self._account = self._generate_private_key() if private_key_path is None else self._load_private_key_from_path(private_key_path)
        bytes_representation = Web3.toBytes(hexstr=self._account.privateKey.hex())
        self._public_key = keys.PrivateKey(bytes_representation).public_key

    @property
    def entity(self) -> Account:
        """Get the entity."""
        return self._account

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self._public_key

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: a display_address str
        """
        return str(self._account.address)

    def _load_private_key_from_path(self, file_name) -> Account:
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
                    account = Account.from_key(data)
            else:
                account = self._generate_private_key()
            return account
        except IOError as e:        # pragma: no cover
            logger.exception(str(e))

    def sign_transaction(self, message: str) -> bytes:
        """
        Sing a transaction to send it to the ledger.

        :param message:
        :return: Signed message in bytes
        """
        m_message = encode_defunct(text=message)
        signature = self._account.sign_message(m_message)
        return signature

    def _generate_private_key(self) -> Account:
        """Generate a key pair for ethereum network."""
        account = Account.create()
        return account

    @staticmethod
    def get_address_from_public_key(self, public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        raise NotImplementedError
