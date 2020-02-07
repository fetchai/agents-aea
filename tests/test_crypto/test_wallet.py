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

from unittest import TestCase, mock

import pytest

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.wallet import Wallet


def test_wallet_initialisation_error():
    """Test the value error when we initialise the wallet."""
    with pytest.raises(ValueError):
        Wallet({"Test": "test"})


@mock.patch("aea.crypto.wallet.EthereumCrypto")
@mock.patch("aea.crypto.wallet.FetchAICrypto")
class WalletTestCase(TestCase):
    """Test case for Wallet class."""

    def test_wallet_init_positive(self, *mocks):
        """Test Wallet init positive result."""
        private_key_paths = {ETHEREUM: "path1", FETCHAI: "path2"}
        Wallet(private_key_paths)

    def test_wallet_init_bad_id(self, *mocks):
        """Test Wallet init unsupported private key paths identifier."""
        private_key_paths = {"unknown-id": "path1"}
        with self.assertRaises(ValueError):
            Wallet(private_key_paths)

    def test_wallet_crypto_objects_positive(self, *mocks):
        """Test Wallet.crypto_objects init positive result."""
        private_key_paths = {ETHEREUM: "path1", FETCHAI: "path2"}
        wallet = Wallet(private_key_paths)
        crypto_objects = wallet.crypto_objects
        self.assertTupleEqual(tuple(crypto_objects), (ETHEREUM, FETCHAI))

    def test_wallet_public_keys_positive(self, *mocks):
        """Test Wallet.public_keys init positive result."""
        private_key_paths = {ETHEREUM: "path1", FETCHAI: "path2"}
        wallet = Wallet(private_key_paths)
        public_keys = wallet.public_keys
        self.assertTupleEqual(tuple(public_keys), (ETHEREUM, FETCHAI))

    def test_wallet_addresses_positive(self, *mocks):
        """Test Wallet.addresses init positive result."""
        private_key_paths = {ETHEREUM: "path1", FETCHAI: "path2"}
        wallet = Wallet(private_key_paths)
        addresses = wallet.addresses
        self.assertTupleEqual(tuple(addresses), (ETHEREUM, FETCHAI))
