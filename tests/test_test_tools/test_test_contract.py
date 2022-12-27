# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains tests for test case classes for AEA contract testing."""

from pathlib import Path
from typing import cast
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumApi

from aea.test_tools.test_contract import BaseContractTestCase
from aea.test_tools.utils import as_context, copy_class

from tests.data.dummy_contract.contract import DummyContract


DUMMY_TX = {"gasPrice": 0, "nonce": 0, "gas": 0}
TX_RECEIPT = {"raw_log": ""}
PATH_TO_DUMMY_CONTRACT = Path(*DummyContract.__module__.split(".")).parent.absolute()


# mocks
mock_get_deploy_transaction = mock.patch.object(
    EthereumApi, "get_deploy_transaction", return_value=DUMMY_TX
)
mock_send_signed_transaction = mock.patch.object(
    EthereumApi, "send_signed_transaction", return_value=""
)
mock_time_sleep = mock.patch("time.sleep", return_value=None)
mock_tx_receipt = mock.patch.object(
    EthereumApi, "get_transaction_receipt", return_value=TX_RECEIPT
)
mock_is_transaction_settled = mock.patch.object(
    EthereumApi, "is_transaction_settled", return_value=True
)
mock_get_balance_increment = mock.patch.object(
    EthereumApi, "get_balance", side_effect=range(4)
)


class TestCls(BaseContractTestCase):
    """Concrete `copy` of BaseContractTestCase"""

    path_to_contract = Path(".")
    ledger_identifier = ""

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Concrete finish_contract_deployment"""
        return ""


def test_base_contract_test_case_definition_without_attributes_raises_error() -> None:
    """Test that definition of concrete subclass of BaseContractTestCase without attributes raises error."""
    with pytest.raises(ValueError):

        class TestCls(BaseContractTestCase):
            pass

    with pytest.raises(ValueError):

        class TestClsB(BaseContractTestCase):
            path_to_contract = Path(".")


class TestBaseContractTestCaseSetup:
    """Test BaseContractTestCase setup."""

    def setup(self) -> None:
        """Setup test"""

        # must `copy` the class to avoid test interference
        self.test_cls = cast(TestCls, copy_class(TestCls))

    def setup_test_cls(self) -> TestCls:
        """Helper method to setup test to be tested"""

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup_class()
        test_instance.setup()
        return test_instance

    def test_contract_setup_contract_configuration_not_found(self):
        """Test contract setup contract configuration not found"""

        self.test_cls.ledger_identifier = "ethereum"
        with pytest.raises(
            FileNotFoundError, match="Contract configuration not found: contract.yaml"
        ):
            self.setup_test_cls()

    def test_contract_setup_deploy_transaction_not_found(self):
        """Test contract setup deploy transaction not found"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        with pytest.raises(ValueError, match="Deploy transaction not found!"):
            self.setup_test_cls()

    def test_contract_setup_transaction_digest_not_found(self):
        """Test contract setup transaction digest not found"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        with as_context(
            mock_get_deploy_transaction,
            pytest.raises(ValueError, match="Transaction digest not found!"),
        ):
            self.setup_test_cls()

    def test_contract_setup_transaction_receipt_not_found(self):
        """Test contract setup transaction receipt not found"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        with as_context(
            mock_get_deploy_transaction,
            mock_send_signed_transaction,
            mock_time_sleep,
            pytest.raises(ValueError, match="Transaction receipt not found!"),
        ):
            self.setup_test_cls()

    def test_contract_setup_transaction_receipt_not_valid(self):
        """Test contract setup transaction receipt not valid"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        with as_context(
            mock_get_deploy_transaction,
            mock_send_signed_transaction,
            mock_time_sleep,
            mock_tx_receipt,
            pytest.raises(ValueError, match="Transaction receipt not valid!"),
        ):
            self.setup_test_cls()

    def test_contract_setup_successful(self):
        """Test contract setup successful"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        with as_context(
            mock_get_deploy_transaction,
            mock_send_signed_transaction,
            mock_time_sleep,
            mock_tx_receipt,
            mock_is_transaction_settled,
        ):
            test = self.setup_test_cls()
            assert test.contract
            # exists for backward compatibility
            args = DUMMY_TX, test.ledger_api, test.deployer_crypto
            assert test.sign_send_confirm_receipt_transaction(*args) is TX_RECEIPT

    def test_contract_not_set(self):
        """Test contract not set"""

        test_instance = TestCls()
        with pytest.raises(
            ValueError, match="Ensure the contract is set during setup."
        ):
            assert test_instance.contract

    def test_fund_from_faucet_balance_not_increased(self):
        """Test fund fom faucet balance NOT increased"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        self.test_cls.fund_from_faucet = True
        with as_context(
            mock_get_deploy_transaction,
            mock_send_signed_transaction,
            mock_time_sleep,
            mock_tx_receipt,
            mock_is_transaction_settled,
            pytest.raises(ValueError, match="Balance not increased!"),
        ):
            self.setup_test_cls()

    def test_fund_from_faucet_balance_increased(self):
        """Test fund fom faucet balance increased"""

        self.test_cls.ledger_identifier = "ethereum"
        self.test_cls.path_to_contract = PATH_TO_DUMMY_CONTRACT
        self.test_cls.fund_from_faucet = True
        with as_context(
            mock_get_deploy_transaction,
            mock_send_signed_transaction,
            mock_time_sleep,
            mock_tx_receipt,
            mock_is_transaction_settled,
            mock_get_balance_increment,
        ):
            self.setup_test_cls()
