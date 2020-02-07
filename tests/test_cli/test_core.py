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

"""This test module contains the tests for commands in aea.cli.core module."""
from unittest import TestCase, mock

from aea.cli.core import _try_get_balance, _wait_funds_release


@mock.patch("aea.cli.core._try_get_balance", return_value=0)
@mock.patch("aea.cli.core.FUNDS_RELEASE_TIMEOUT", 0.5)
class WaitFundsReleaseTestCase(TestCase):
    """Test case for _wait_funds_release method."""

    def test__wait_funds_release_positive(self, _try_get_balance_mock):
        """Test for _wait_funds_release method positive result."""
        _wait_funds_release("agent_config", "wallet", "type_")


@mock.patch("aea.cli.core._verify_ledger_apis_access")
@mock.patch("aea.cli.core.LedgerApis", mock.MagicMock())
@mock.patch("aea.cli.core.cast")
class TryGetBalanceTestCase(TestCase):
    """Test case for _try_get_balance method."""

    def test__try_get_balance_positive(
        self, _verify_ledger_apis_access_mock, cast_mock
    ):
        """Test for _try_get_balance method positive result."""
        agent_config = mock.Mock()
        ledger_apis = mock.Mock()
        ledger_apis.read_all = lambda: [["id", "config"], ["id", "config"]]
        agent_config.ledger_apis = ledger_apis

        wallet_mock = mock.Mock()
        wallet_mock.addresses = {"type_": "some-adress"}
        _try_get_balance(agent_config, wallet_mock, "type_")
