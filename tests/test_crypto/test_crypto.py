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

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, \
    load_pem_private_key

from aea.crypto.base import Crypto
from ..conftest import ROOT_DIR


def test_initialization_from_existing_private_key():
    """Test that the initialization from an existing private key works correctly."""
    private_key_pem_path = ROOT_DIR + "/tests/data/priv.pem"

    private_key = load_pem_private_key(open(private_key_pem_path, "rb").read(), None, default_backend())

    c = Crypto(private_key_pem_path=private_key_pem_path)

    expected_public_key = private_key.public_key().public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
    actual_public_key = c.public_key_pem
    assert expected_public_key == actual_public_key
