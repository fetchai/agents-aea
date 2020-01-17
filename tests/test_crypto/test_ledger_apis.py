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

from hexbytes import HexBytes

import pytest

from aea.crypto.ethereum import ETHEREUM, EthereumCrypto
from aea.crypto.fetchai import DEFAULT_FETCHAI_CONFIG, FETCHAI, FetchAICrypto
from aea.crypto.ledger_apis import (
    LedgerApis,
    _try_to_instantiate_ethereum_ledger_api,
    _try_to_instantiate_fetchai_ledger_api,
)

from ..conftest import CUR_PATH

logger = logging.getLogger(__name__)

DEFAULT_ETHEREUM_CONFIG = (
    "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
    3,
)
fet_address = "B3t9pv4rYccWqCjeuoXsDoeXLiKxVAQh6Q3CLAiNZZQ2mtqF1"
eth_address = "0x21795D753752ccC1AC728002D23Ba33cbF13b8b0"
GAS_PRICE = "50"
GAS_ID = "gwei"


class TestLedgerApis:
    """Test the ledger_apis module."""

    def test_initialisation(self):
        """Test the initialisation of the ledger APIs."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        assert ledger_apis.configs.get(ETHEREUM) == DEFAULT_ETHEREUM_CONFIG
        assert ledger_apis.has_fetchai
        assert ledger_apis.has_ethereum
        assert isinstance(ledger_apis.last_tx_statuses, Dict)
        unknown_config = ("UknownPath", 8080)
        with pytest.raises(ValueError):
            LedgerApis({"UNKNOWN": unknown_config}, FETCHAI)

    def test_eth_token_balance(self):
        """Test the token_balance for the eth tokens."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )

        api = ledger_apis.apis[ETHEREUM]
        with mock.patch.object(api.api.eth, "getBalance", return_value=10):
            balance = ledger_apis.token_balance(ETHEREUM, eth_address)
            assert balance == 10
            assert ledger_apis.last_tx_statuses[ETHEREUM] == "OK"

        with mock.patch.object(
            api.api.eth, "getBalance", return_value=0, side_effect=Exception
        ):
            balance = ledger_apis.token_balance(ETHEREUM, fet_address)
            assert balance == 0, "This must be 0 since the address is wrong"
            assert ledger_apis.last_tx_statuses[ETHEREUM] == "ERROR"

    def test_unknown_token_balance(self):
        """Test the token_balance for the unknown tokens."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        with pytest.raises(AssertionError):
            balance = ledger_apis.token_balance("UNKNOWN", fet_address)
            assert balance == 0, "Unknown identifier so it will return 0"

    def test_fet_token_balance(self):
        """Test the token_balance for the fet tokens."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )

        api = ledger_apis.apis[FETCHAI]
        with mock.patch.object(api.api.tokens, "balance", return_value=10):
            balance = ledger_apis.token_balance(FETCHAI, fet_address)
            assert balance == 10
            assert ledger_apis.last_tx_statuses[FETCHAI] == "OK"

        with mock.patch.object(
            api.api.tokens, "balance", return_value=0, side_effect=Exception
        ):
            balance = ledger_apis.token_balance(FETCHAI, eth_address)
            assert balance == 0, "This must be 0 since the address is wrong"
            assert ledger_apis.last_tx_statuses[FETCHAI] == "ERROR"

    def test_transfer_fetchai(self):
        """Test the transfer function for fetchai token."""
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        fet_obj = FetchAICrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )

        with mock.patch.object(
            ledger_apis.apis.get(FETCHAI).api.tokens,
            "transfer",
            return_value="97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35",
        ):
            with mock.patch.object(ledger_apis.apis.get(FETCHAI).api, "sync"):
                tx_digest = ledger_apis.transfer(
                    fet_obj, fet_address, amount=10, tx_fee=10
                )
                assert tx_digest is not None
                assert ledger_apis.last_tx_statuses[FETCHAI] == "OK"

    def test_failed_transfer_fetchai(self):
        """Test the transfer function for fetchai token fails."""
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        fet_obj = FetchAICrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )

        with mock.patch.object(
            ledger_apis.apis.get(FETCHAI).api.tokens,
            "transfer",
            return_value="97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35",
        ):
            with mock.patch.object(
                ledger_apis.apis.get(FETCHAI).api, "sync", side_effect=Exception
            ):
                tx_digest = ledger_apis.transfer(
                    fet_obj, fet_address, amount=10, tx_fee=10
                )
                assert tx_digest is None
                assert ledger_apis.last_tx_statuses[FETCHAI] == "ERROR"

    def test_transfer_ethereum(self):
        """Test the transfer function for ethereum token."""
        private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        eth_obj = EthereumCrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        with mock.patch.object(
            ledger_apis.apis.get(ETHEREUM).api.eth,
            "getTransactionCount",
            return_value=5,
        ):
            with mock.patch.object(
                ledger_apis.apis.get(ETHEREUM).api.eth.account,
                "signTransaction",
                return_value=mock.Mock(),
            ):
                result = HexBytes(
                    "0xf85f808082c35094d898d5e829717c72e7438bad593076686d7d164a80801ba005c2e99ecee98a12fbf28ab9577423f42e9e88f2291b3acc8228de743884c874a077d6bc77a47ad41ec85c96aac2ad27f05a039c4787fca8a1e5ee2d8c7ec1bb6a"
                )
                with mock.patch.object(
                    ledger_apis.apis.get(ETHEREUM).api.eth,
                    "sendRawTransaction",
                    return_value=result,
                ):
                    with mock.patch.object(
                        ledger_apis.apis.get(ETHEREUM).api.eth,
                        "getTransactionReceipt",
                        return_value=b"0xa13f2f926233bc4638a20deeb8aaa7e8d6a96e487392fa55823f925220f6efed",
                    ):
                        tx_digest = ledger_apis.transfer(
                            eth_obj, eth_address, amount=10, tx_fee=200000
                        )
                        assert tx_digest is not None
                        assert ledger_apis.last_tx_statuses[ETHEREUM] == "OK"

    def test_failed_transfer_ethereum(self):
        """Test the transfer function for ethereum token fails."""
        private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        eth_obj = EthereumCrypto(private_key_path=private_key_path)
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        with mock.patch.object(
            ledger_apis.apis.get(ETHEREUM).api.eth,
            "getTransactionCount",
            return_value=5,
            side_effect=Exception,
        ):
            tx_digest = ledger_apis.transfer(
                eth_obj, eth_address, amount=10, tx_fee=200000
            )
            assert tx_digest is None
            assert ledger_apis.last_tx_statuses[ETHEREUM] == "ERROR"

    def test_is_tx_settled_fetchai(self):
        """Test if the transaction is settled for fetchai."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        tx_digest = "97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35"
        with pytest.raises(AssertionError):
            ledger_apis.is_tx_settled("Unknown", tx_digest=tx_digest)

        with mock.patch.object(
            ledger_apis.apis[FETCHAI].api.tx, "status", return_value="Submitted"
        ):
            is_successful = ledger_apis.is_tx_settled(FETCHAI, tx_digest=tx_digest)
            assert is_successful
            assert ledger_apis.last_tx_statuses[FETCHAI] == "OK"

        with mock.patch.object(
            ledger_apis.apis[FETCHAI].api.tx, "status", side_effect=Exception
        ):
            is_successful = ledger_apis.is_tx_settled(FETCHAI, tx_digest=tx_digest)
            assert not is_successful
            assert ledger_apis.last_tx_statuses[FETCHAI] == "ERROR"

    def test_is_tx_settled_ethereum(self):
        """Test if the transaction is settled for eth."""
        ledger_apis = LedgerApis(
            {ETHEREUM: DEFAULT_ETHEREUM_CONFIG, FETCHAI: DEFAULT_FETCHAI_CONFIG},
            FETCHAI,
        )
        tx_digest = "97fcacaaf94b62318c4e4bbf53fd2608c15062f17a6d1bffee0ba7af9b710e35"
        result = HexBytes(
            "0xf85f808082c35094d898d5e829717c72e7438bad593076686d7d164a80801ba005c2e99ecee98a12fbf28ab9577423f42e9e88f2291b3acc8228de743884c874a077d6bc77a47ad41ec85c96aac2ad27f05a039c4787fca8a1e5ee2d8c7ec1bb6a"
        )
        with mock.patch.object(
            ledger_apis.apis[ETHEREUM].api.eth,
            "getTransactionReceipt",
            return_value=result,
        ):
            is_successful = ledger_apis.is_tx_settled(ETHEREUM, tx_digest=tx_digest)
            assert is_successful
            assert ledger_apis.last_tx_statuses[ETHEREUM] == "OK"

        with mock.patch.object(
            ledger_apis.apis[ETHEREUM].api.eth,
            "getTransactionReceipt",
            side_effect=Exception,
        ):
            is_successful = ledger_apis.is_tx_settled(ETHEREUM, tx_digest=tx_digest)
            assert not is_successful
            assert ledger_apis.last_tx_statuses[ETHEREUM] == "ERROR"

    def test_try_to_instantiate_fetchai_ledger_api(self):
        """Test the instantiation of the fetchai ledger api."""
        _try_to_instantiate_fetchai_ledger_api(addr="127.0.0.1", port=80)
        from fetchai.ledger.api import LedgerApi

        with mock.patch.object(LedgerApi, "__init__", side_effect=Exception):
            with pytest.raises(SystemExit):
                _try_to_instantiate_fetchai_ledger_api(addr="127.0.0.1", port=80)

    def test__try_to_instantiate_ethereum_ledger_api(self):
        """Test the instantiation of the ethereum ledger api."""
        _try_to_instantiate_ethereum_ledger_api(addr="127.0.0.1")
        from web3 import Web3

        with mock.patch.object(Web3, "__init__", side_effect=Exception):
            with pytest.raises(SystemExit):
                _try_to_instantiate_ethereum_ledger_api(addr="127.0.0.1")
