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

"""Module wrapping all the public and private keys cryptography."""

import logging
from typing import Any, Dict, Optional, cast

from aea.common import JSONLike
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto


_default_logger = logging.getLogger(__name__)


class CryptoStore:
    """Utility class to store and retrieve crypto objects."""

    __slots__ = ("_crypto_objects", "_public_keys", "_addresses", "_private_keys")

    def __init__(
        self,
        crypto_id_to_path: Optional[Dict[str, Optional[str]]] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize the crypto store.

        :param crypto_id_to_path: dictionary from crypto id to an (optional) path
            to the private key.
        :param password: the password to encrypt/decrypt the private key.
        """
        if crypto_id_to_path is None:
            crypto_id_to_path = {}
        crypto_objects = {}  # type: Dict[str, Crypto]
        public_keys = {}  # type: Dict[str, str]
        addresses = {}  # type: Dict[str, str]
        private_keys = {}  # type: Dict[str, str]

        for identifier, path in crypto_id_to_path.items():
            crypto = make_crypto(identifier, private_key_path=path, password=password)
            crypto_objects[identifier] = crypto
            public_keys[identifier] = cast(str, crypto.public_key)
            addresses[identifier] = cast(str, crypto.address)
            private_keys[identifier] = cast(str, crypto.private_key)

        self._crypto_objects = crypto_objects
        self._public_keys = public_keys
        self._addresses = addresses
        self._private_keys = private_keys

    @property
    def public_keys(self) -> Dict[str, str]:
        """Get the public_key dictionary."""
        return self._public_keys

    @property
    def crypto_objects(self) -> Dict[str, Crypto]:
        """Get the crypto objects (key pair)."""
        return self._crypto_objects

    @property
    def addresses(self) -> Dict[str, str]:
        """Get the crypto addresses."""
        return self._addresses

    @property
    def private_keys(self) -> Dict[str, str]:
        """Get the crypto addresses."""
        return self._private_keys


class Wallet:
    """
    Container for crypto objects.

    The cryptos are separated into two categories:

    - main cryptos: used by the AEA for the economic side (i.e. signing transaction)
    - connection cryptos: exposed to the connection objects for encrypted communication.

    """

    def __init__(
        self,
        private_key_paths: Dict[str, Optional[str]],
        connection_private_key_paths: Optional[Dict[str, Optional[str]]] = None,
        password: Optional[str] = None,
    ):
        """
        Instantiate a wallet object.

        :param private_key_paths: the private key paths
        :param connection_private_key_paths: the private key paths for the connections.
        :param password: the password to encrypt/decrypt the private key.
        """
        self._main_cryptos = CryptoStore(private_key_paths, password=password)
        self._connection_cryptos = CryptoStore(
            connection_private_key_paths, password=password
        )

    @property
    def public_keys(self) -> Dict[str, str]:
        """Get the public_key dictionary."""
        return self._main_cryptos.public_keys

    @property
    def crypto_objects(self) -> Dict[str, Crypto]:
        """Get the crypto objects (key pair)."""
        return self._main_cryptos.crypto_objects

    @property
    def addresses(self) -> Dict[str, str]:
        """Get the crypto addresses."""
        return self._main_cryptos.addresses

    @property
    def private_keys(self) -> Dict[str, str]:
        """Get the crypto addresses."""
        return self._main_cryptos.private_keys

    @property
    def main_cryptos(self) -> CryptoStore:
        """Get the main crypto store."""
        return self._main_cryptos

    @property
    def connection_cryptos(self) -> CryptoStore:
        """Get the connection crypto store."""
        return self._connection_cryptos

    def sign_message(
        self, crypto_id: str, message: bytes, is_deprecated_mode: bool = False
    ) -> Optional[str]:
        """
        Sign a message.

        :param crypto_id: the id of the crypto
        :param message: the message to be signed
        :param is_deprecated_mode: what signing mode to use
        :return: the signature of the message
        """
        crypto_object = self.crypto_objects.get(crypto_id, None)
        if crypto_object is None:
            _default_logger.warning(
                "No crypto object for crypto_id={} in wallet!".format(crypto_id)
            )
            signature = None  # type: Optional[str]
        else:
            signature = crypto_object.sign_message(message, is_deprecated_mode)
        return signature

    def sign_transaction(self, crypto_id: str, transaction: Any) -> Optional[JSONLike]:
        """
        Sign a tx.

        :param crypto_id: the id of the crypto
        :param transaction: the transaction to be signed
        :return: the signed tx
        """
        crypto_object = self.crypto_objects.get(crypto_id, None)
        if crypto_object is None:
            _default_logger.warning(
                "No crypto object for crypto_id={} in wallet!".format(crypto_id)
            )
            signed_transaction = None  # type: Optional[Any]
        else:
            signed_transaction = crypto_object.sign_transaction(transaction)
        return signed_transaction
