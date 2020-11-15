# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This test module contains the tests for commands in aea.cli.transfer module."""
import random
import string
from pathlib import Path
from unittest.mock import patch

import pytest
from click.exceptions import ClickException

from aea.cli.transfer import wait_tx_settled
from aea.cli.utils.package_utils import get_wallet_from_agent_config, try_get_balance
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import verify_or_create_private_keys
from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.common.utils import wait_for_condition
from tests.conftest import MAX_FLAKY_RERUNS


class TestCliTransferFetchAINetwork(AEATestCaseEmpty):
    """Test cli transfer command."""

    LEDGER_ID = FetchAICrypto.identifier
    ANOTHER_LEDGER_ID = CosmosCrypto.identifier

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        super(TestCliTransferFetchAINetwork, cls).setup_class()
        cls.agent_name2 = "agent-" + "".join(
            random.choices(string.ascii_lowercase, k=5)
        )
        cls.create_agents(cls.agent_name2)

        cls.gen_key(cls.agent_name)
        cls.gen_key(cls.agent_name2)

    @classmethod
    def gen_key(cls, agent_name: str) -> None:
        """Generate crypto key."""
        cls.set_agent_context(agent_name)
        key_file = f"{cls.LEDGER_ID}.key"
        assert cls.run_cli_command(
            "generate-key", cls.LEDGER_ID, key_file, cwd=cls._get_cwd()
        )
        assert cls.run_cli_command(
            "add-key", cls.LEDGER_ID, key_file, cwd=cls._get_cwd()
        )

    def get_address(self) -> str:
        """Get current agent address."""
        result = self.invoke("get-address", self.LEDGER_ID)
        return result.stdout_bytes.decode("utf-8").strip()

    def get_balance(self) -> int:
        """Get balance for current agent."""
        with cd(self._get_cwd()):
            agent_config = verify_or_create_private_keys(Path("."), False)
            wallet = get_wallet_from_agent_config(agent_config)
            return int(try_get_balance(agent_config, wallet, self.LEDGER_ID))

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_integration(self):
        """Perform integration tests of cli transfer command with real transfer."""
        self.set_agent_context(self.agent_name2)
        agent2_balance = self.get_balance()
        agent2_address = self.get_address()
        assert agent2_balance == 0

        self.set_agent_context(self.agent_name)
        self.generate_wealth()

        wait_for_condition(lambda: self.get_balance() > 0, timeout=15, period=1)

        agent1_balance = self.get_balance()
        assert agent1_balance > 0

        amount = round(agent1_balance / 10)
        fee = round(agent1_balance / 20)

        self.invoke(
            "transfer", self.LEDGER_ID, agent2_address, str(amount), str(fee), "-y"
        )

        wait_for_condition(
            lambda: self.get_balance() == (agent1_balance - amount - fee),
            timeout=15,
            period=1,
        )

        self.set_agent_context(self.agent_name2)
        wait_for_condition(
            lambda: self.get_balance() == (agent2_balance + amount),
            timeout=15,
            period=1,
        )

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_yes_option_enabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test yes option is enabled."""
        self.invoke(
            "transfer", self.LEDGER_ID, self.get_address(), "100000", "100", "-y"
        )
        confirm_mock.assert_not_called()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_yes_option_disabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test yes option is disabled."""
        self.invoke("transfer", self.LEDGER_ID, self.get_address(), "100000", "100")
        confirm_mock.assert_called_once()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_sync_option_enabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test sync option is enabled."""
        self.invoke(
            "transfer", self.LEDGER_ID, self.get_address(), "100000", "100", "-y"
        )
        wait_tx_settled_mock.assert_not_called()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_sync_option_disabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test sync option is disabled."""
        self.invoke(
            "transfer",
            self.LEDGER_ID,
            self.get_address(),
            "100000",
            "100",
            "-y",
            "--sync",
        )
        wait_tx_settled_mock.assert_called_once()

    @patch("aea.cli.transfer.do_transfer", return_value=None)
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_failed_on_send(self, wait_tx_settled_mock, confirm_mock, do_transfer_mock):
        """Test fail to send a transaction."""
        with pytest.raises(ClickException, match=r"Failed to send a transaction!"):
            self.invoke("transfer", self.LEDGER_ID, self.get_address(), "100000", "100")

    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_no_wallet_registered(self, wait_tx_settled_mock, confirm_mock):
        """Test no wallet for crypto id registered."""
        with pytest.raises(
            ClickException, match=r"No private key registered for `.*` in wallet!"
        ):
            self.invoke(
                "transfer", self.ANOTHER_LEDGER_ID, self.get_address(), "100000", "100"
            )

    @patch("aea.cli.transfer.try_get_balance", return_value=10)
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_balance_too_low(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test balance too low exception."""
        with pytest.raises(
            ClickException,
            match=r"Balance is not enough! Available=[0-9]+, required=[0-9]+!",
        ):
            self.invoke("transfer", self.LEDGER_ID, self.get_address(), "100000", "100")

    @patch(
        "aea.cli.transfer.LedgerApis.is_transaction_settled", side_effects=[False, True]
    )
    def test_wait_tx_settled_ok(self, is_transaction_settled_mock):
        """Test wait tx settle is ok."""
        wait_tx_settled("some", "some", timeout=4)

    @patch("aea.cli.transfer.LedgerApis.is_transaction_settled", return_value=False)
    def test_wait_tx_settled_timeout(self, is_transaction_settled_mock):
        """Test wait tx settle fails with timeout error."""
        with pytest.raises(TimeoutError):
            wait_tx_settled("some", "some", timeout=0.5)
