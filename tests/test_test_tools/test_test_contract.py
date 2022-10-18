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

from typing import Iterable, Generator, Any, cast
import collections
from contextlib import contextmanager, ExitStack
from pathlib import Path
import pytest

from unittest import mock

from aea_ledger_ethereum import EthereumApi
from tests.data.dummy_contract.contract import DummyContract


from aea.test_tools.test_contract import BaseContractTestCase


DUMMY_TX = {'gasPrice': 0, 'nonce': 0, 'gas': 0}
PATH_TO_DUMMY_CONTRACT = Path(*DummyContract.__module__.split(".")).parent.absolute()


# mocks
mock_get_deploy_transaction = mock.patch.object(EthereumApi, "get_deploy_transaction", return_value=DUMMY_TX)
mock_send_signed_transaction = mock.patch.object(EthereumApi, "send_signed_transaction", return_value="")
mock_time_sleep = mock.patch('time.sleep', return_value=None)


# TODO: move to aea.test_tools.utils
def consume(iterator: Iterable) -> None:
    """Consume the iterator"""
    collections.deque(iterator, maxlen=0)


@contextmanager
def as_context(*contexts: Any) -> Generator[None, None, None]:
    """Set contexts"""
    with ExitStack() as stack:
        consume(map(stack.enter_context, contexts))
        yield


class TestCls(BaseContractTestCase):
    """Concrete `copy` of BaseContractTestCase"""

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """concrete finish_contract_deployment"""
        return ""


class TestBaseContractTestCaseSetup:
    """Test BaseContractTestCase setup."""

    def setup(self) -> None:
        """Setup test"""

        # must `copy` the class to avoid test interference
        class_copy = type('TestCls', TestCls.__bases__, dict(TestCls.__dict__))
        self.test_cls = cast(TestCls, class_copy)

    def setup_test_cls(self) -> TestCls:
        """Helper method to setup test to be tested"""

        self.test_cls.setup()
        return self.test_cls()

    def test_contract_setup_missing_ledger_identifier(self):
        """Test contract setup missing ledger identifier"""

        with pytest.raises(ValueError, match="ledger_identifier not set!"):
            self.setup_test_cls()

    def test_contract_setup_contract_configuration_not_found(self):
        """Test contract setup contract configuration not found"""

        self.test_cls.ledger_identifier = "ethereum"
        with pytest.raises(FileNotFoundError, match="Contract configuration not found: contract.yaml"):
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
