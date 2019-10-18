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

"""This module contains the tests of the crypto module."""
import os
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from aea.crypto.base import DefaultCrypto, _load_pem_private_key_from_path
from ..conftest import ROOT_DIR


PRIVATE_KEY_PEM_PATH = os.path.join(ROOT_DIR, "tests/data/priv.pem")


def test_initialization_from_existing_private_key():
    """Test that the initialization from an existing private key works correctly."""
    private_key = _load_pem_private_key_from_path(path=PRIVATE_KEY_PEM_PATH)
    assert private_key is not None, "The private key is not None after the loading!"
    c = DefaultCrypto(private_key_pem_path=PRIVATE_KEY_PEM_PATH)

    expected_public_key = private_key.public_key().public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
    actual_public_key = c.public_key_pem
    assert expected_public_key == actual_public_key


def test_return_fingerprint():
    """Test that the fingerprint is not None."""
    c = DefaultCrypto(private_key_pem_path=PRIVATE_KEY_PEM_PATH)
    assert c.fingerprint is not None, "The fingerprint must be None"


def test_sign_data():
    """Test the sign message and the verification of the message."""
    c = DefaultCrypto(private_key_pem_path=PRIVATE_KEY_PEM_PATH)
    my_signature = c.sign_data(b"Hello")
    assert len(my_signature) > 0, "Signed data must not be none"
    assert c.is_confirmed_integrity(b"Hello", my_signature, c.public_key), "The verification must be True"
    obj = DefaultCrypto(private_key_pem_path=PRIVATE_KEY_PEM_PATH)

    # TODO:  I am not sure about this :)
    assert type(obj._pvk_obj_to_pem(obj._private_key)) == bytes, "Must return the bytes for the .pem file!"
