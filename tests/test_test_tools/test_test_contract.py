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

from typing import cast
import pytest


from aea.test_tools.test_contract import BaseContractTestCase


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
