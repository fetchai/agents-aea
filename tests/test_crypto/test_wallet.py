# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the tests of the wallet module."""

from unittest import TestCase

import pytest
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import ETHEREUM_PRIVATE_KEY_PATH
from aea_ledger_fetchai import FetchAICrypto
from aea_ledger_fetchai.test_tools.constants import FETCHAI_PRIVATE_KEY_PATH

from aea.crypto.wallet import Wallet
from aea.exceptions import AEAException

from tests.conftest import COSMOS_PRIVATE_KEY_PATH


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
        private_key_paths = {FetchAICrypto.identifier: "this_path_does_not_exists"}
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

    def test_wallet_private_keys_positive(self):
        """Test Wallet.private_keys init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        private_keys = wallet.private_keys
        self.assertTupleEqual(
            tuple(private_keys), (EthereumCrypto.identifier, FetchAICrypto.identifier)
        )

    def test_wallet_cryptos_positive(self):
        """Test Wallet.main_cryptos and connection cryptos init positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        connection_private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths, connection_private_key_paths)
        assert len(wallet.main_cryptos.crypto_objects) == len(
            wallet.connection_cryptos.crypto_objects
        ), "Incorrect amount of cryptos"

    def test_wallet_sign_message_positive(self):
        """Test Wallet.sign_message positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        signature = wallet.sign_message(
            EthereumCrypto.identifier, message=b"some message"
        )
        assert type(signature) == str and int(
            signature, 16
        ), "No signature present or not hexadecimal"

    def test_wallet_sign_message_negative(self):
        """Test Wallet.sign_message negative result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        signature = wallet.sign_message("unknown id", message=b"some message")
        assert signature is None, "Signature should be none"

    def test_wallet_sign_transaction_positive(self):
        """Test Wallet.sign_transaction positive result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        signed_transaction = wallet.sign_transaction(
            EthereumCrypto.identifier,
            transaction={"gasPrice": 50, "nonce": 10, "gas": 10},
        )
        assert type(signed_transaction) == dict, "No signed transaction returned"

    def test_wallet_sign_transaction_negative(self):
        """Test Wallet.sign_transaction negative result."""
        private_key_paths = {
            EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
        }
        wallet = Wallet(private_key_paths)
        signed_transaction = wallet.sign_transaction(
            "unknown id", transaction={"this is my tx": "here"}
        )
        assert signed_transaction is None, "Signed transaction should be none"
