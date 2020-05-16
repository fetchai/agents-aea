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

"""This module contains the tests of the wallet module."""

from unittest import TestCase

import pytest

from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import Wallet
from aea.exceptions import AEAException

from ..conftest import (
    COSMOS_PRIVATE_KEY_PATH,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI_PRIVATE_KEY_PATH,
)


def test_wallet_initialisation_error():
    """Test the value error when we initialise the wallet."""
    with pytest.raises(AEAException):
        Wallet({"Test": "test"})


class WalletTestCase(TestCase):
    """Test case for Wallet class."""

    def test_wallet_init_positive(self):
        """Test Wallet init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
            CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_PATH,
        }
        Wallet(private_key_paths)

    def test_wallet_init_bad_id(self):
        """Test Wallet init unsupported private key paths identifier."""
        private_key_paths = {"unknown_id": "path1"}
        with self.assertRaises(AEAException):
            Wallet(private_key_paths)

    def test_wallet_init_bad_paths(self):
        """Test Wallet init with bad paths to private keys"""
        private_key_paths = {FETCHAI: "this_path_does_not_exists"}
        with self.assertRaises(FileNotFoundError):
            Wallet(private_key_paths)

    def test_wallet_crypto_objects_positive(self):
        """Test Wallet.crypto_objects init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        crypto_objects = wallet.crypto_objects
        self.assertTupleEqual(
            tuple(crypto_objects), (EthereumCrypto.identifier, FetchAICrypto.identifier)
        )

    def test_wallet_public_keys_positive(self):
        """Test Wallet.public_keys init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        public_keys = wallet.public_keys
        self.assertTupleEqual(
            tuple(public_keys), (EthereumCrypto.identifier, FetchAICrypto.identifier)
        )

    def test_wallet_addresses_positive(self):
        """Test Wallet.addresses init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        addresses = wallet.addresses
        self.assertTupleEqual(
            tuple(addresses), (EthereumCrypto.identifier, FetchAICrypto.identifier)
        )
