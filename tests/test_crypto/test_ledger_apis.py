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

"""This module contains the tests for the crypto/helpers module."""

import logging
import os
from typing import Dict
from unittest import mock

from eth_account.datastructures import AttributeDict

from fetchai.ledger.api.tx import TxContents

from hexbytes import HexBytes

import pytest

from aea.crypto.cosmos import CosmosApi
from aea.crypto.ethereum import EthereumApi, EthereumCrypto
from aea.crypto.fetchai import FetchAIApi, FetchAICrypto
from aea.crypto.ledger_apis import LedgerApis

from ..conftest import (
    COSMOS_TESTNET_CONFIG,
    CUR_PATH,
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_TESTNET_CONFIG,
    FETCHAI_ADDRESS_ONE,
    FETCHAI_TESTNET_CONFIG,
)

logger = logging.getLogger(__name__)


def _raise_exception(*args, **kwargs):
    raise Exception("Message")


class TestLedgerApis:
    """Test the ledger_apis module."""

    def test_initialisation(self):
        """Test the initialisation of the ledger APIs."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
                CosmosApi.identifier: COSMOS_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        assert (
            ledger_apis.configs.get(EthereumApi.identifier) == ETHEREUM_TESTNET_CONFIG
        )
        assert ledger_apis.has_ledger(FetchAIApi.identifier)
        assert type(ledger_apis.get_api(FetchAIApi.identifier)) == FetchAIApi
        assert ledger_apis.has_ledger(EthereumApi.identifier)
        assert type(ledger_apis.get_api(EthereumApi.identifier)) == EthereumApi
        assert ledger_apis.has_ledger(CosmosApi.identifier)
        assert type(ledger_apis.get_api(CosmosApi.identifier)) == CosmosApi
        assert isinstance(ledger_apis.last_tx_statuses, Dict)
        unknown_config = ("UknownPath", 8080)
        with pytest.raises(ValueError):
            LedgerApis({"UNKNOWN": unknown_config}, FetchAIApi.identifier)

    def test_eth_token_balance(self):
        """Test the token_balance for the eth tokens."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

        api = ledger_apis.apis[EthereumApi.identifier]
        with mock.patch.object(api.api.eth, "getBalance", return_value=10):
            balance = ledger_apis.token_balance(
                EthereumApi.identifier, ETHEREUM_ADDRESS_ONE
            )
            assert balance == 10

        with mock.patch.object(
            api.api.eth, "getBalance", return_value=-1, side_effect=Exception
        ):
            balance = ledger_apis.token_balance(
                EthereumApi.identifier, FETCHAI_ADDRESS_ONE
            )
            assert balance == -1, "This must be -1 since the address is wrong"

    def test_unknown_token_balance(self):
        """Test the token_balance for the unknown tokens."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        with pytest.raises(AssertionError):
            balance = ledger_apis.token_balance("UNKNOWN", FETCHAI_ADDRESS_ONE)
            assert balance == 0, "Unknown identifier so it will return 0"

    def test_fet_token_balance(self):
        """Test the token_balance for the fet tokens."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

        api = ledger_apis.apis[FetchAIApi.identifier]
        with mock.patch.object(api.api.tokens, "balance", return_value=10):
            balance = ledger_apis.token_balance(
                FetchAIApi.identifier, FETCHAI_ADDRESS_ONE
            )
            assert balance == 10

        with mock.patch.object(
            api.api.tokens, "balance", return_value=-1, side_effect=Exception
        ):
            balance = ledger_apis.token_balance(
                FetchAIApi.identifier, ETHEREUM_ADDRESS_ONE
            )
            assert balance == -1, "This must be -1 since the address is wrong"

    def test_transfer_fetchai(self):
        """Test the transfer function for fetchai token."""
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        fet_obj = FetchAICrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

        with mock.patch.object(
            ledger_apis.apis.get(FetchAIApi.identifier).api.tokens,
            "transfer",
            return_value="97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35",
        ):
            with mock.patch.object(
                ledger_apis.apis.get(FetchAIApi.identifier).api, "sync"
            ):
                tx_digest = ledger_apis.transfer(
                    fet_obj,
                    FETCHAI_ADDRESS_ONE,
                    amount=10,
                    tx_fee=10,
                    tx_nonce="transaction nonce",
                )
                assert tx_digest is not None

    def test_failed_transfer_fetchai(self):
        """Test the transfer function for fetchai token fails."""
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        fet_obj = FetchAICrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

        with mock.patch.object(
            ledger_apis.apis.get(FetchAIApi.identifier).api.tokens,
            "transfer",
            side_effect=Exception,
        ):
            tx_digest = ledger_apis.transfer(
                fet_obj,
                FETCHAI_ADDRESS_ONE,
                amount=10,
                tx_fee=10,
                tx_nonce="transaction nonce",
            )
            assert tx_digest is None

    # def test_transfer_ethereum(self):
    #     """Test the transfer function for ethereum token."""
    #     private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
    #     eth_obj = EthereumCrypto(private_key_path=private_key_path)
    #     ledger_apis = LedgerApis(
    #         {EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG, FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG},
    #         FetchAIApi.identifier,
    #     )
    #     with mock.patch.object(
    #         ledger_apis.apis.get(EthereumApi.identifier).api.eth,
    #         "getTransactionCount",
    #         return_value=5,
    #     ):
    #         with mock.patch.object(
    #             ledger_apis.apis.get(EthereumApi.identifier).api.eth.account,
    #             "signTransaction",
    #             return_value=mock.Mock(),
    #         ):
    #             result = HexBytes(
    #                 "0xf85f808082c35094d898d5e829717c72e7438bad593076686d7d164a80801ba005c2e99ecee98a12fbf28ab9577423f42e9e88f2291b3acc8228de743884c874a077d6bc77a47ad41ec85c96aac2ad27f05a039c4787fca8a1e5ee2d8c7ec1bb6a"
    #             )
    #             with mock.patch.object(
    #                 ledger_apis.apis.get(EthereumApi.identifier).api.eth,
    #                 "sendRawTransaction",
    #                 return_value=result,
    #             ):
    #                 with mock.patch.object(
    #                     ledger_apis.apis.get(EthereumApi.identifier).api.eth,
    #                     "getTransactionReceipt",
    #                     return_value=b"0xa13f2f926233bc4638a20deeb8aaa7e8d6a96e487392fa55823f925220f6efed",
    #                 ):
    #                     with mock.patch.object(
    #                         ledger_apis.apis.get(EthereumApi.identifier).api.eth,
    #                         "estimateGas",
    #                         return_value=100000,
    #                     ):
    #                         tx_digest = ledger_apis.transfer(
    #                             eth_obj,
    #                             ETHEREUM_ADDRESS_ONE,
    #                             amount=10,
    #                             tx_fee=200000,
    #                             tx_nonce="transaction nonce",
    #                         )
    #                         assert tx_digest is not None

    def test_failed_transfer_ethereum(self):
        """Test the transfer function for ethereum token fails."""
        private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        eth_obj = EthereumCrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        with mock.patch.object(
            ledger_apis.apis.get(EthereumApi.identifier).api.eth,
            "getTransactionCount",
            return_value=5,
            side_effect=Exception,
        ):
            tx_digest = ledger_apis.transfer(
                eth_obj,
                ETHEREUM_ADDRESS_ONE,
                amount=10,
                tx_fee=200000,
                tx_nonce="transaction nonce",
            )
            assert tx_digest is None

    def test_is_tx_settled_fetchai(self):
        """Test if the transaction is settled for fetchai."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        tx_digest = "97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35"
        with mock.patch.object(
            ledger_apis.apis[FetchAIApi.identifier],
            "is_transaction_settled",
            return_value=True,
        ):
            is_successful = ledger_apis.is_transaction_settled(
                FetchAIApi.identifier, tx_digest=tx_digest
            )
            assert is_successful

        with mock.patch.object(
            ledger_apis.apis[FetchAIApi.identifier],
            "is_transaction_settled",
            return_value=False,
        ):
            is_successful = ledger_apis.is_transaction_settled(
                FetchAIApi.identifier, tx_digest=tx_digest
            )
            assert not is_successful

    def test_is_tx_settled_ethereum(self):
        """Test if the transaction is settled for eth."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        tx_digest = "97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35"
        with mock.patch.object(
            ledger_apis.apis[EthereumApi.identifier],
            "is_transaction_settled",
            return_value=True,
        ):
            is_successful = ledger_apis.is_transaction_settled(
                EthereumApi.identifier, tx_digest=tx_digest
            )
            assert is_successful

        with mock.patch.object(
            ledger_apis.apis[EthereumApi.identifier],
            "is_transaction_settled",
            return_value=False,
        ):
            is_successful = ledger_apis.is_transaction_settled(
                EthereumApi.identifier, tx_digest=tx_digest
            )
            assert not is_successful

    @mock.patch("time.time", mock.MagicMock(return_value=1579533928))
    def test_validate_ethereum_transaction(self):
        seller = EthereumCrypto()
        client = EthereumCrypto()
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        tx_nonce = ledger_apis.generate_tx_nonce(
            EthereumApi.identifier, seller.address, client.address
        )

        tx_digest = "0xbefa7768c313ff49bf274eefed001042a0ff9e3cfbe75ff1a9c2baf18001cec4"
        result = AttributeDict(
            {
                "blockHash": HexBytes(
                    "0x0bfc237d2a17f719a3300a4822779391ec6e3a74832fe1b05b8c477902b0b59e"
                ),
                "blockNumber": 7161932,
                "from": client.address,
                "gas": 200000,
                "gasPrice": 50000000000,
                "hash": HexBytes(
                    "0xbefa7768c313ff49bf274eefed001042a0ff9e3cfbe75ff1a9c2baf18001cec4"
                ),
                "input": tx_nonce,
                "nonce": 4,
                "r": HexBytes(
                    "0xb54ce8b9fa1d1be7be316c068af59a125d511e8dd51202b1a7e3002dee432b52"
                ),
                "s": HexBytes(
                    "0x4f44702b3812d3b4e4b76da0fd5b554b3ae76d1717db5b6b5faebd7b85ae0303"
                ),
                "to": seller.address,
                "transactionIndex": 0,
                "v": 42,
                "value": 2,
            }
        )
        with mock.patch.object(
            ledger_apis.apis.get(EthereumApi.identifier).api.eth,
            "getTransaction",
            return_value=result,
        ):
            assert ledger_apis.is_tx_valid(
                identifier=EthereumApi.identifier,
                tx_digest=tx_digest,
                seller=seller.address,
                client=client.address,
                tx_nonce=tx_nonce,
                amount=2,
            )

    def test_generate_tx_nonce_fetchai(self):
        """Test the generated tx_nonce."""
        seller_crypto = FetchAICrypto()
        client_crypto = FetchAICrypto()
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        seller_address = seller_crypto.address
        client_address = client_crypto.address
        tx_nonce = ledger_apis.generate_tx_nonce(
            FetchAIApi.identifier, seller_address, client_address
        )
        logger.info(tx_nonce)
        assert tx_nonce != ""

    def test_validate_transaction_fetchai(self):
        """Test the validate transaction for fetchai ledger."""
        seller_crypto = FetchAICrypto()
        client_crypto = FetchAICrypto()
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

        seller_address = str(seller_crypto.address)
        client_address = str(client_crypto.address)
        tx_contents = TxContents(
            digest=b"digest",
            action="action",
            chain_code="1",
            from_address=client_address,
            contract_digest="Contract_digest",
            contract_address=None,
            valid_from=1,
            valid_until=6,
            charge=10,
            charge_limit=2,
            transfers=[{"to": seller_address, "amount": 100}],
            signatories=["signatories"],
            data="data",
        )

        with mock.patch.object(
            ledger_apis.apis.get(FetchAIApi.identifier)._api.tx,
            "contents",
            return_value=tx_contents,
        ):
            with mock.patch.object(
                ledger_apis.apis.get(FetchAIApi.identifier),
                "is_transaction_settled",
                return_value=True,
            ):
                result = ledger_apis.is_tx_valid(
                    identifier=FetchAIApi.identifier,
                    tx_digest="transaction_digest",
                    seller=seller_address,
                    client=client_address,
                    tx_nonce="tx_nonce",
                    amount=100,
                )
                assert result

    def test_generate_tx_nonce_positive(self, *mocks):
        """Test generate_tx_nonce positive result."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        result = ledger_apis.generate_tx_nonce(
            FetchAIApi.identifier, "seller", "client"
        )
        assert result != ""

    def test_is_tx_valid_negative(self, *mocks):
        """Test is_tx_valid init negative result."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        with mock.patch.object(
            ledger_apis.apis.get(FetchAIApi.identifier),
            "is_transaction_valid",
            return_value=False,
        ):
            result = ledger_apis.is_tx_valid(
                FetchAIApi.identifier, "tx_digest", "seller", "client", "tx_nonce", 1
            )
        assert not result

    def test_has_default_ledger_positive(self):
        """Test has_default_ledger init positive result."""
        ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )
        assert ledger_apis.has_default_ledger
