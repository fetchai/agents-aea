
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

"""This module contains the tests of the ethereum module."""
import os

from aea.crypto.fetchai import FetchAICrypto
from ..conftest import ROOT_DIR

PRIVATE_KEY_PATH = os.path.join(ROOT_DIR, "/tests/data/fet_private_key.txt")


def test_initialisation():
    """Test the initialisation of the the fet crypto."""
    fet_crypto = FetchAICrypto()
    assert fet_crypto.public_key is not None, "Public key must not be None after Initialisation"
    assert fet_crypto.address is not None, "Address must not be None after Initialisation"
    assert FetchAICrypto(PRIVATE_KEY_PATH), "Couldn't load the fet private_key from the path!"
    assert FetchAICrypto("./"), "Couldn't create a new entity for the given path!"


def test_get_address():
    """Test the get address."""
    fet_crypto = FetchAICrypto()
    assert fet_crypto.get_address_from_public_key(fet_crypto.public_key) is not None, "Get address must work"


def test_sign_transaction():
    """Test the signing process."""
    fet_crypto = FetchAICrypto()
    signature = fet_crypto.sign_transaction(tx_hash=b'HelloWorld')
    assert len(signature) > 1, "The len(signature) must be more than 0"


def test_get_address_from_public_key():
    """Test the address from public key."""
    fet_crypto = FetchAICrypto()
    address = FetchAICrypto().get_address_from_public_key(fet_crypto.public_key)
    assert str(address) == str(fet_crypto.address), "The address must be the same."
