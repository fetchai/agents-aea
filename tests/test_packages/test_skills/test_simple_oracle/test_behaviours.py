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
"""This module contains the tests of the behaviour classes of the simple oracle skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.contracts.oracle.contract import PUBLIC_ID as CONTRACT_PUBLIC_ID
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.simple_oracle.behaviours import SimpleOracleBehaviour
from packages.fetchai.skills.simple_oracle.dialogues import PrometheusDialogues
from packages.fetchai.skills.simple_oracle.strategy import Strategy

from tests.conftest import ROOT_DIR


ETHEREUM_LEDGER_ID = "ethereum"
FETCHAI_LEDGER_ID = "fetchai"
AGENT_ADDRESS = "some_eth_address"
DEFAULT_ADDRESS = "0x0000000000000000000000000000000000000000"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of simple oracle."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle")

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.simple_oracle_behaviour = cast(
            SimpleOracleBehaviour,
            cls._skill.skill_context.behaviours.simple_oracle_behaviour,
        )

    def test_setup(self):
        """Test the setup method of the simple_oracle behaviour."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_behaviour.setup()
        self.assert_quantity_in_outbox(3)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
        )
        assert has_attributes, error_str

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="oracle_account_balance_ETH",
            description="Balance of oracle contract (ETH)",
        )
        assert has_attributes, error_str

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="num_oracle_updates",
            description="Number of updates published to oracle contract",
        )
        assert has_attributes, error_str

    def test_setup_with_contract_set(self):
        """Test the setup method of the simple_oracle behaviour for existing contract."""
        prometheus_dialogues = cast(
            PrometheusDialogues,
            self.simple_oracle_behaviour.context.prometheus_dialogues,
        )
        prometheus_dialogues.enabled = False
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy.is_contract_deployed = True

        with patch.object(
            self.simple_oracle_behaviour.context.logger, "log"
        ) as mock_logger:
            self.simple_oracle_behaviour.setup()
        mock_logger.assert_any_call(
            logging.INFO, "Fetch oracle contract address already added",
        )
        self.assert_quantity_in_outbox(0)

    def test_setup_with_contract_set_and_oracle_role_granted(self):
        """Test the setup method of the simple_oracle behaviour for existing contract and oracle role."""
        prometheus_dialogues = cast(
            PrometheusDialogues,
            self.simple_oracle_behaviour.context.prometheus_dialogues,
        )
        prometheus_dialogues.enabled = False
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy.is_contract_deployed = True
        strategy.is_oracle_role_granted = True

        assert strategy.erc20_address == DEFAULT_ADDRESS

        with patch.object(
            self.simple_oracle_behaviour.context.logger, "log"
        ) as mock_logger:
            self.simple_oracle_behaviour.setup()
        mock_logger.assert_any_call(
            logging.INFO, "Oracle role already granted",
        )

        self.assert_quantity_in_outbox(0)

    def test_act_pre_deploy(self):
        """Test the act method of the simple_oracle behaviour before contract is deployed."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_behaviour.context.agent_addresses[
            ETHEREUM_LEDGER_ID
        ] = "AGENT_ADDRESS"
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ETHEREUM_LEDGER_ID,
            address=cast(
                str,
                self.simple_oracle_behaviour.context.agent_addresses.get(
                    ETHEREUM_LEDGER_ID
                ),
            ),
        )
        assert has_attributes, error_str

    def test_act_grant_role(self):
        """Test the act method of the simple_oracle behaviour before role is granted."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy._ledger_id = ETHEREUM_LEDGER_ID
        strategy.is_contract_deployed = True
        self.simple_oracle_behaviour.context.agent_addresses[
            ETHEREUM_LEDGER_ID
        ] = "AGENT_ADDRESS"
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(2)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ETHEREUM_LEDGER_ID,
            address=cast(
                str,
                self.simple_oracle_behaviour.context.agent_addresses.get(
                    ETHEREUM_LEDGER_ID
                ),
            ),
        )
        assert has_attributes, error_str

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_grant_role_transaction",
        )
        assert has_attributes, error_str

    def test_act_update(self):
        """Test the act method of the simple_oracle behaviour for normal updating."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy._ledger_id = ETHEREUM_LEDGER_ID
        strategy.is_contract_deployed = True
        strategy.is_oracle_role_granted = True
        strategy._oracle_value_name = "oracle_value"
        self.simple_oracle_behaviour.context.shared_state["oracle_value"] = {
            "some_key": "some_value"
        }
        self.simple_oracle_behaviour.context.agent_addresses[
            ETHEREUM_LEDGER_ID
        ] = "AGENT_ADDRESS"
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(2)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ETHEREUM_LEDGER_ID,
            address=cast(
                str,
                self.simple_oracle_behaviour.context.agent_addresses.get(
                    ETHEREUM_LEDGER_ID
                ),
            ),
        )
        assert has_attributes, error_str

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_update_transaction",
        )
        assert has_attributes, error_str

    def test_act_no_oracle_value(self):
        """Test the act method of the simple_oracle behaviour when no oracle value is present."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy._ledger_id = ETHEREUM_LEDGER_ID
        strategy.is_contract_deployed = True
        strategy.is_oracle_role_granted = True
        self.simple_oracle_behaviour.context.agent_addresses[
            ETHEREUM_LEDGER_ID
        ] = "AGENT_ADDRESS"
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ETHEREUM_LEDGER_ID,
            address=cast(
                str,
                self.simple_oracle_behaviour.context.agent_addresses.get(
                    ETHEREUM_LEDGER_ID
                ),
            ),
        )
        assert has_attributes, error_str

    def test__request_contract_deploy_transaction(self):
        """Test that the _request_contract_deploy_transaction function sends the right message to the contract_api for ethereum ledger."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_behaviour._request_contract_deploy_transaction()
        self.assert_quantity_in_outbox(1)

        kwargs = strategy.get_deploy_kwargs()
        assert "ERC20Address" in kwargs.body
        assert "initialFee" in kwargs.body

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=kwargs,
        )
        assert has_attributes, error_str

    def test__request_contract_store_transaction(self):
        """Test that the _request_contract_deploy_transaction function sends the right message to the contract_api for fetchai ledger."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy._ledger_id = FETCHAI_LEDGER_ID

        self.simple_oracle_behaviour._request_contract_deploy_transaction()
        self.assert_quantity_in_outbox(1)

        kwargs = strategy.get_deploy_kwargs()
        assert "ERC20Address" not in kwargs.body
        assert "initialFee" not in kwargs.body

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=kwargs,
        )
        assert has_attributes, error_str

    def test__request_grant_role_transaction(self):
        """Test that the _request_grant_role_transaction function sends the right message to the contract_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_behaviour._request_grant_role_transaction()
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_grant_role_transaction",
        )
        assert has_attributes, error_str

    def test__request_update_transaction(self):
        """Test that the _request_update_transaction function sends the right message to the contract_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        update_args = {"some": "args"}
        self.simple_oracle_behaviour._request_update_transaction(update_args)
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_update_transaction",
        )
        assert has_attributes, error_str

    def test__get_balance(self):
        """Test that the _get_balance function sends the right message to the ledger_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy._ledger_id = ETHEREUM_LEDGER_ID
        self.simple_oracle_behaviour.context.agent_addresses[
            ETHEREUM_LEDGER_ID
        ] = "AGENT_ADDRESS"

        self.simple_oracle_behaviour._get_balance()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=ETHEREUM_LEDGER_ID,
            address=cast(
                str,
                self.simple_oracle_behaviour.context.agent_addresses.get(
                    ETHEREUM_LEDGER_ID
                ),
            ),
        )
        assert has_attributes, error_str

    def test_add_prometheus_metric(self):
        """Test the send_http_request_message method of the simple_oracle behaviour."""
        self.simple_oracle_behaviour.add_prometheus_metric(
            "some_metric", "Gauge", "some_description", {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="some_metric",
            description="some_description",
            labels={"label_key": "label_value"},
        )
        assert has_attributes, error_str

    def test_update_prometheus_metric(self):
        """Test the test_update_prometheus_metric method of the simple_oracle behaviour."""
        self.simple_oracle_behaviour.update_prometheus_metric(
            "some_metric", "set", 0.0, {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            callable="set",
            title="some_metric",
            value=0.0,
            labels={"label_key": "label_value"},
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test that the teardown method of the simple_oracle behaviour leaves no messages in the outbox."""
        assert self.simple_oracle_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
