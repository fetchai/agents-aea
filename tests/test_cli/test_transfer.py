# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
from typing import List, Optional
from unittest.mock import patch

import pytest
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_fetchai import FetchAICrypto
from click.exceptions import ClickException

from aea.cli.transfer import wait_tx_settled
from aea.cli.utils.package_utils import try_get_balance
from aea.configurations.manager import AgentConfigManager
from aea.crypto.helpers import get_wallet_from_agent_config, private_key_verify
from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.common.utils import wait_for_condition
from tests.conftest import MAX_FLAKY_RERUNS


class TestCliTransferFetchAINetwork(AEATestCaseEmpty):
    """Test cli transfer command."""

    LEDGER_ID = FetchAICrypto.identifier
    ANOTHER_LEDGER_ID = CosmosCrypto.identifier
    PASSWORD: Optional[str] = None

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        super(TestCliTransferFetchAINetwork, cls).setup_class()
        cls.agent_name2 = "agent_" + "".join(
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
        password_options = cls.get_password_args(cls.PASSWORD)
        assert cls.run_cli_command(
            "generate-key",
            cls.LEDGER_ID,
            key_file,
            *password_options,
            cwd=cls._get_cwd(),
        )
        assert cls.run_cli_command(
            "add-key", cls.LEDGER_ID, key_file, *password_options, cwd=cls._get_cwd()
        )

    @classmethod
    def get_password_args(cls, password: Optional[str]) -> List[str]:
        """Get password arguments."""
        return [] if password is None else ["--password", password]

    def get_balance(self) -> int:
        """Get balance for current agent."""
        with cd(self._get_cwd()):
            agent_config = AgentConfigManager.verify_private_keys(
                Path("."),
                substitude_env_vars=False,
                private_key_helper=private_key_verify,
                password=self.PASSWORD,
            ).agent_config
            wallet = get_wallet_from_agent_config(agent_config, password=self.PASSWORD)
            return int(try_get_balance(agent_config, wallet, self.LEDGER_ID))

    @pytest.mark.skip  # wrong ledger_id
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_integration(self):
        """Perform integration tests of cli transfer command with real transfer."""
        self.set_agent_context(self.agent_name2)
        password_option = self.get_password_args(self.PASSWORD)
        agent2_original_balance = self.get_balance()
        agent2_address = self.get_address(self.LEDGER_ID, self.PASSWORD)

        self.set_agent_context(self.agent_name)
        agent1_original_balance = self.get_balance()
        self.generate_wealth(password=self.PASSWORD)

        wait_for_condition(
            lambda: self.get_balance() > agent1_original_balance, timeout=15, period=1
        )

        agent1_balance = self.get_balance()
        assert agent1_balance > agent1_original_balance

        amount = round(agent1_balance / 10)
        fee = round(agent1_balance / 20)

        self.invoke(
            "transfer",
            self.LEDGER_ID,
            agent2_address,
            str(amount),
            str(fee),
            "-y",
            *password_option,
        )

        wait_for_condition(
            lambda: self.get_balance() == (agent1_balance - amount - fee),
            timeout=15,
            period=1,
        )

        self.set_agent_context(self.agent_name2)
        wait_for_condition(
            lambda: self.get_balance() == (agent2_original_balance + amount),
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
        password_option = self.get_password_args(self.PASSWORD)
        self.invoke(
            "transfer",
            self.LEDGER_ID,
            self.get_address(self.LEDGER_ID, self.PASSWORD),
            "100000",
            "100",
            "-y",
            *password_option,
        )
        confirm_mock.assert_not_called()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_yes_option_disabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test yes option is disabled."""
        password_option = self.get_password_args(self.PASSWORD)
        self.invoke(
            "transfer",
            self.LEDGER_ID,
            self.get_address(self.LEDGER_ID, self.PASSWORD),
            "100000",
            "100",
            *password_option,
        )
        confirm_mock.assert_called_once()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_sync_option_enabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test sync option is enabled."""
        password_option = self.get_password_args(self.PASSWORD)
        self.invoke(
            "transfer",
            self.LEDGER_ID,
            self.get_address(self.LEDGER_ID, self.PASSWORD),
            "100000",
            "100",
            "-y",
            *password_option,
        )
        wait_tx_settled_mock.assert_not_called()

    @patch("aea.cli.transfer.do_transfer", return_value="some_digest")
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_sync_option_disabled(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test sync option is disabled."""
        password_option = self.get_password_args(self.PASSWORD)
        self.invoke(
            "transfer",
            self.LEDGER_ID,
            self.get_address(self.LEDGER_ID, self.PASSWORD),
            "100000",
            "100",
            "-y",
            "--sync",
            *password_option,
        )
        wait_tx_settled_mock.assert_called_once()

    @patch("aea.cli.transfer.do_transfer", return_value=None)
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_failed_on_send(self, wait_tx_settled_mock, confirm_mock, do_transfer_mock):
        """Test fail to send a transaction."""
        with pytest.raises(ClickException, match=r"Failed to send a transaction!"):
            password_option = self.get_password_args(self.PASSWORD)
            self.invoke(
                "transfer",
                self.LEDGER_ID,
                self.get_address(self.LEDGER_ID, self.PASSWORD),
                "100000",
                "100",
                *password_option,
            )

    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_no_wallet_registered(self, wait_tx_settled_mock, confirm_mock):
        """Test no wallet for crypto id registered."""
        password_option = self.get_password_args(self.PASSWORD)
        with pytest.raises(
            ClickException, match=r"No private key registered for `.*` in wallet!"
        ):
            self.invoke(
                "transfer",
                self.ANOTHER_LEDGER_ID,
                self.get_address(self.LEDGER_ID, self.PASSWORD),
                "100000",
                "100",
                *password_option,
            )

    @patch("aea.cli.transfer.try_get_balance", return_value=10)
    @patch("aea.cli.transfer.click.confirm", return_value=None)
    @patch("aea.cli.transfer.wait_tx_settled", return_value=None)
    def test_balance_too_low(
        self, wait_tx_settled_mock, confirm_mock, do_transfer_mock
    ):
        """Test balance too low exception."""
        password_option = self.get_password_args(self.PASSWORD)
        with pytest.raises(
            ClickException,
            match=r"Balance is not enough! Available=[0-9]+, required=[0-9]+!",
        ):
            self.invoke(
                "transfer",
                self.LEDGER_ID,
                self.get_address(self.LEDGER_ID, self.PASSWORD),
                "100000",
                "100",
                *password_option,
            )

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


class TestCliTransferFetchAINetworkWithPassword(TestCliTransferFetchAINetwork):
    """Test cli transfer command, with '--password' option."""

    PASSWORD = "fake-password"  # nosec
