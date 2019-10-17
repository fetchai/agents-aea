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

from aea.crypto.ethereum_base import EthCrypto
from ..conftest import ROOT_DIR

PRIVATE_KEY_PATH = ROOT_DIR + "/tests/data/eth_private_key.txt"


def test_creation():
    """Test the creation of the crypto_objects.ls"""
    assert EthCrypto(), "Managed to initialise the eth_account"
    assert EthCrypto(PRIVATE_KEY_PATH), "Managed to load the eth private key"
    assert EthCrypto("./"), "Managed to create a new eth private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = EthCrypto()
    assert account.address is not None, "After creation the display address must not be None"
    assert account._bytes_representation is not None, "After creation the bytes_representation of the " \
                                                      "address must not be None"
    assert account.public_key is not None, "After creation the public key must no be None"


def test_sign_transaction():
    """Test the signing function for the eth_crypto."""
    account = EthCrypto(PRIVATE_KEY_PATH)
    sign_bytes = account.sign_transaction('Hello')
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
