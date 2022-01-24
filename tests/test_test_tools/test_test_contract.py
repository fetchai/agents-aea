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

"""This module contains tests for aea.test_tools.test_contract.BaseContractTestCase."""


from pathlib import Path
from unittest import mock

import pytest
from aea_ledger_fetchai import CosmosCrypto, FetchAIApi, FetchAICrypto, FetchAIFaucetApi

from aea.test_tools.test_contract import BaseContractTestCase

from tests.conftest import ROOT_DIR


LEDGER_ID = "fetchai"
CONTRACT_ADDRESS = "contract_address"


class TestContractTestCase(BaseContractTestCase):
    """Test case for BaseContractTestCase."""

    path_to_contract = Path(ROOT_DIR, "tests", "data", "dummy_contract")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.ledger_identifier = LEDGER_ID

        with mock.patch.object(
            BaseContractTestCase,
            "sign_send_confirm_receipt_multisig_transaction",
            return_value="",
        ):
            with mock.patch.object(CosmosCrypto, "sign_transaction"):
                with mock.patch.object(FetchAIApi, "get_deploy_transaction"):
                    super().setup()

    @classmethod
    def finish_contract_deployment(cls):
        """Finish contract deployment method."""
        return CONTRACT_ADDRESS

    def test_setup(self):
        """Test the setup class method."""
        assert self.ledger_identifier == LEDGER_ID
        assert type(self.ledger_api) is FetchAIApi
        assert self.ledger_api.identifier == LEDGER_ID

        assert type(self.deployer_crypto) is FetchAICrypto
        assert self.deployer_crypto.identifier == LEDGER_ID
        assert type(self.item_owner_crypto) is FetchAICrypto
        assert self.item_owner_crypto.identifier == LEDGER_ID

        assert type(self.faucet_api) is FetchAIFaucetApi
        assert self.faucet_api.identifier == LEDGER_ID

        assert self.contract_address == CONTRACT_ADDRESS

    @mock.patch.object(FetchAIFaucetApi, "get_wealth")
    def test_refill_from_faucet(self, get_wealth_mock):
        """Test the refill_from_faucet static method."""
        with pytest.raises(ValueError) as e:
            self.refill_from_faucet(
                self.ledger_api, self.faucet_api, self.contract_address
            )
            assert str(e) == "Balance not increased!"
        get_wealth_mock.assert_called_once_with(CONTRACT_ADDRESS)

    @mock.patch.object(FetchAIApi, "get_deploy_transaction", return_value="tx")
    @mock.patch.object(
        BaseContractTestCase,
        "sign_send_confirm_receipt_multisig_transaction",
        return_value="tx_receipt",
    )
    def test__deploy_contract(
        self,
        sign_send_confirm_receipt_multisig_transaction_mock,
        get_deploy_transaction_mock,
    ):
        """Test the _deploy_contract class method."""
        gas = 1
        result = self._deploy_contract(
            self.contract, self.ledger_api, self.deployer_crypto, gas
        )
        assert result == "tx_receipt"
        sign_send_confirm_receipt_multisig_transaction_mock.assert_called_once_with(
            "tx", self.ledger_api, [self.deployer_crypto]
        )
        get_deploy_transaction_mock.assert_called_once()

    @mock.patch.object(FetchAIApi, "get_deploy_transaction", return_value=None)
    @mock.patch.object(
        BaseContractTestCase,
        "sign_send_confirm_receipt_multisig_transaction",
        return_value="tx_receipt",
    )
    def test__deploy_contract_tx_not_found(
        self,
        sign_send_confirm_receipt_multisig_transaction_mock,
        get_deploy_transaction_mock,
    ):
        """Test the _deploy_contract class method."""
        gas = 1
        with pytest.raises(ValueError) as e:
            self._deploy_contract(
                self.contract, self.ledger_api, self.deployer_crypto, gas
            )
            assert str(e) == "Deploy transaction not found!"
        sign_send_confirm_receipt_multisig_transaction_mock.assert_not_called()
        get_deploy_transaction_mock.assert_called_once()

    @mock.patch.object(FetchAICrypto, "sign_transaction", return_value="tx")
    @mock.patch.object(FetchAIApi, "send_signed_transaction", return_value="tx_digest")
    @mock.patch.object(FetchAIApi, "get_transaction_receipt", return_value="tx_receipt")
    @mock.patch.object(FetchAIApi, "is_transaction_settled", return_value=True)
    def test_sign_send_confirm_receipt_multisig_transaction(
        self,
        is_transaction_settled_mock,
        get_transaction_receipt_mock,
        send_signed_transaction_mock,
        sign_transaction_mock,
    ):
        """Test the sign_send_confirm_receipt_multisig_transaction static method."""
        sleep_time = 0
        tx = "tx"
        result = self.sign_send_confirm_receipt_multisig_transaction(
            tx, self.ledger_api, [self.deployer_crypto], sleep_time=sleep_time
        )
        assert result == "tx_receipt"
        is_transaction_settled_mock.assert_called_once_with("tx_receipt")
        get_transaction_receipt_mock.assert_called_with("tx_digest")
        send_signed_transaction_mock.assert_called_once_with(tx)
        sign_transaction_mock.assert_called_once_with(tx)

    @mock.patch.object(FetchAICrypto, "sign_transaction", return_value="tx")
    @mock.patch.object(FetchAIApi, "send_signed_transaction", return_value=None)
    @mock.patch.object(FetchAIApi, "get_transaction_receipt")
    @mock.patch.object(FetchAIApi, "is_transaction_settled")
    def test_sign_send_confirm_receipt_multisig_transaction_digest_not_found(
        self,
        is_transaction_settled_mock,
        get_transaction_receipt_mock,
        send_signed_transaction_mock,
        sign_transaction_mock,
    ):
        """Test the sign_send_confirm_receipt_multisig_transaction static method: digest not found."""
        tx = "tx"
        with pytest.raises(ValueError) as e:
            self.sign_send_confirm_receipt_multisig_transaction(
                tx, self.ledger_api, [self.deployer_crypto],
            )
            assert str(e) == "Transaction digest not found!"
        is_transaction_settled_mock.assert_not_called()
        get_transaction_receipt_mock.assert_not_called()
        send_signed_transaction_mock.assert_called_once_with(tx)
        sign_transaction_mock.assert_called_once_with(tx)

    @mock.patch.object(FetchAICrypto, "sign_transaction", return_value="tx")
    @mock.patch.object(FetchAIApi, "send_signed_transaction", return_value="tx_digest")
    @mock.patch.object(FetchAIApi, "get_transaction_receipt", return_value=None)
    @mock.patch.object(FetchAIApi, "is_transaction_settled")
    def test_sign_send_confirm_receipt_multisig_transaction_receipt_not_found(
        self,
        is_transaction_settled_mock,
        get_transaction_receipt_mock,
        send_signed_transaction_mock,
        sign_transaction_mock,
    ):
        """Test the sign_send_confirm_receipt_multisig_transaction static method: receipt not found."""
        tx = "tx"
        sleep_time = 0
        with pytest.raises(ValueError) as e:
            self.sign_send_confirm_receipt_multisig_transaction(
                tx, self.ledger_api, [self.deployer_crypto], sleep_time=sleep_time
            )
            assert str(e) == "Transaction receipt not found!"
        is_transaction_settled_mock.assert_not_called()
        get_transaction_receipt_mock.assert_called_with("tx_digest")
        send_signed_transaction_mock.assert_called_once_with(tx)
        sign_transaction_mock.assert_called_once_with(tx)

    @mock.patch.object(FetchAICrypto, "sign_transaction", return_value="tx")
    @mock.patch.object(FetchAIApi, "send_signed_transaction", return_value="tx_digest")
    @mock.patch.object(
        FetchAIApi, "get_transaction_receipt", return_value={"raw_log": "log"}
    )
    @mock.patch.object(FetchAIApi, "is_transaction_settled", return_value=False)
    def test_sign_send_confirm_receipt_multisig_transaction_receipt_not_valid(
        self,
        is_transaction_settled_mock,
        get_transaction_receipt_mock,
        send_signed_transaction_mock,
        sign_transaction_mock,
    ):
        """Test the sign_send_confirm_receipt_multisig_transaction static method: receipt not valid."""
        tx = "tx"
        sleep_time = 0
        with pytest.raises(ValueError) as e:
            self.sign_send_confirm_receipt_multisig_transaction(
                tx, self.ledger_api, [self.deployer_crypto], sleep_time=sleep_time
            )
            assert str(e) == "Transaction receipt not valid!\nlog"
        is_transaction_settled_mock.assert_called_with({"raw_log": "log"})
        get_transaction_receipt_mock.assert_called_with("tx_digest")
        send_signed_transaction_mock.assert_called_once_with(tx)
        sign_transaction_mock.assert_called_once_with(tx)
