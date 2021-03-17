# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Password based encryption functionality."""
import base64
import json
import os
from hashlib import pbkdf2_hmac
from json.decoder import JSONDecodeError
from typing import Tuple

import pyaes  # type: ignore


class DataEncrypt:
    """Class to encrypt/decrypt data strings with password provided."""

    hash_algo = "sha256"
    hash_iterations = 20000

    @classmethod
    def _aes_encrypt(
        cls, password: str, data: bytes
    ) -> Tuple[bytes, int, bytes, bytes]:
        """
        Encryption schema for private keys

        :param password: plaintext password to use for encryption
        :param data: plaintext data to encrypt

        :return: encrypted data, length of original data, initialisation vector for aes, password hashing salt
        """
        # Generate hash from password
        salt = os.urandom(16)
        hashed_pass = cls._get_hashed_password(password, salt)

        # Random initialisation vector
        iv = os.urandom(16)

        # Encrypt data using AES
        aes = pyaes.AESModeOfOperationCBC(hashed_pass, iv=iv)

        # Pad data to multiple of 16
        data_length = len(data)
        if data_length % 16 != 0:  # pragma: nocover
            data += b" " * (16 - data_length % 16)

        encrypted = b""
        while data:
            encrypted += aes.encrypt(data[:16])
            data = data[16:]

        return encrypted, data_length, iv, salt

    @classmethod
    def _aes_decrypt(
        cls,
        password: str,
        salt: bytes,
        encrypted_data: bytes,
        data_length: int,
        initialisation_vector: bytes,
    ) -> bytes:
        """
        Decryption schema for private keys.

        :param password: plaintext password used for encryption
        :param salt: password hashing salt
        :param encrypted_data: encrypted data string
        :param data_length: length of original plaintext data
        :param initialisation_vector: initialisation vector for aes

        :return: decrypted data as plaintext
        """
        # Hash password
        hashed_pass = cls._get_hashed_password(password, salt)
        # Decrypt data, noting original length
        aes = pyaes.AESModeOfOperationCBC(hashed_pass, iv=initialisation_vector)

        decrypted = b""
        while encrypted_data:
            decrypted += aes.decrypt(encrypted_data[:16])
            encrypted_data = encrypted_data[16:]
        decrypted_data = decrypted[:data_length]

        # Return original data
        return decrypted_data

    @classmethod
    def _get_hashed_password(cls, password: str, salt: bytes) -> bytes:
        """Get hashed password."""
        return pbkdf2_hmac(cls.hash_algo, password.encode(), salt, cls.hash_iterations)

    @classmethod
    def encrypt(cls, data: bytes, password: str) -> bytes:
        """Encrypt data with password."""
        if not isinstance(data, bytes):  # pragma: nocover
            raise ValueError(f"data has to be bytes! not {type(data)}")

        encrypted_data, data_length, initialisation_vector, salt = cls._aes_encrypt(
            password, data
        )

        json_data = {
            "encrypted_data": cls.bytes_encode(encrypted_data),
            "data_length": data_length,
            "initialisation_vector": cls.bytes_encode(initialisation_vector),
            "salt": cls.bytes_encode(salt),
        }
        return json.dumps(json_data).encode()

    @staticmethod
    def bytes_encode(data: bytes) -> str:
        """Encode bytes to ascii friendly string."""
        return base64.b64encode(data).decode()

    @staticmethod
    def bytes_decode(data: str) -> bytes:
        """Decode ascii friendly string to bytes."""
        return base64.b64decode(data)

    @classmethod
    def decrypt(cls, encrypted_data: bytes, password: str) -> bytes:
        """Decrypt data with passwod provided."""
        if not isinstance(encrypted_data, bytes):  # pragma: nocover
            raise ValueError(
                f"encrypted_data has to be str! not {type(encrypted_data)}"
            )

        try:
            json_data = json.loads(encrypted_data)
            return cls._aes_decrypt(
                password,
                encrypted_data=cls.bytes_decode(json_data["encrypted_data"]),
                data_length=json_data["data_length"],
                initialisation_vector=cls.bytes_decode(
                    json_data["initialisation_vector"]
                ),
                salt=cls.bytes_decode(json_data["salt"]),
            )
        except (KeyError, JSONDecodeError) as e:
            raise ValueError(f"Bad encrypted key format!: {str(e)}") from e
