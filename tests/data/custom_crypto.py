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

"""This module contains a custom crypto class for testing purposes."""
from typing import Any, Optional, Tuple

from aea.common import Address
from aea.crypto.base import Crypto, EntityClass


class CustomCrypto(Crypto):
    """This is a custom crypto class for testing purposes.."""

    @classmethod
    def generate_private_key(cls) -> EntityClass:
        """Generare private key."""
        pass

    @classmethod
    def load_private_key_from_path(
        cls, file_name: str, password: Optional[str] = None
    ) -> Any:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :param password: the password to encrypt/decrypt the private key.
        :return: the Entity.
        """
        pass

    @property
    def public_key(self) -> str:
        """Get public key."""
        pass

    @property
    def address(self) -> str:
        """Get address."""
        pass

    @property
    def private_key(self) -> str:
        """Get private key."""
        pass

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        """
        Get address from public key.

        :param public_key: the public key.
        :return: the address
        """
        pass

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign message.

        :param message: the message
        :param is_deprecated_mode: whether or not deprecated signing mode is used.
        :return: signed message string
        """
        pass

    def sign_transaction(self, transaction: Any) -> Any:
        """
        Sign transaction.

        :param transaction: the transaction to be signed
        :return: the signed transaction
        """
        pass

    def recover_message(
        self, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        """
        Recover message.

        :param message: the message
        :param signature: the signature
        :param is_deprecated_mode: whether or not it is deprecated
        """
        pass

    def encrypt(self, password: str) -> str:
        """
        Encrypt the private key and return in json.

        :param private_key: the raw private key.
        :param password: the password to decrypt.
        :return: json string containing encrypted private key.
        """

    @classmethod
    def decrypt(cls, keyfile_json: str, password: str) -> str:
        """
        Decrypt the private key and return in raw form.

        :param keyfile_json: json string containing encrypted private key.
        :param password: the password to decrypt.
        :return: the raw private key.
        """
