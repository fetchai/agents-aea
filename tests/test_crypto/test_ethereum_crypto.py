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

from aea.crypto.ethereum import EthereumCrypto
from ..conftest import ROOT_DIR

PRIVATE_KEY_PATH = os.path.join(ROOT_DIR, "/tests/data/eth_private_key.txt")


def test_creation():
    """Test the creation of the crypto_objects."""
    assert EthereumCrypto(), "Managed to initialise the eth_account"
    assert EthereumCrypto(PRIVATE_KEY_PATH), "Managed to load the eth private key"
    assert EthereumCrypto("./"), "Managed to create a new eth private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = EthereumCrypto()
    assert account.entity is not None, "The property must return the account."
    assert account.address is not None, "After creation the display address must not be None"
    assert account.public_key is not None, "After creation the public key must no be None"
    assert account.entity is not None, "After creation the entity must no be None"


def test_sign_transaction():
    """Test the signing function for the eth_crypto."""
    account = EthereumCrypto(PRIVATE_KEY_PATH)
    sign_bytes = account.sign_transaction(b'hello')
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addr = account.recover_from_hash(b'hello', signature=sign_bytes)
    assert recovered_addr == account.address, "Failed to recover the correct address."
