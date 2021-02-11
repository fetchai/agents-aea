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

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.contracts.oracle.contract import PUBLIC_ID as CONTRACT_PUBLIC_ID
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.simple_oracle.behaviours import SimpleOracleBehaviour
from packages.fetchai.skills.simple_oracle.dialogues import PrometheusDialogues
from packages.fetchai.skills.simple_oracle.strategy import Strategy

from tests.conftest import ROOT_DIR


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
        self.simple_oracle_behaviour.setup()
        self.assert_quantity_in_outbox(3)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())


        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        ), "Wrong message performative"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert msg.callable == "get_deploy_transaction", "Wrong callable"

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.ADD_METRIC
        ), "Wrong message performative"
        assert msg.type == "Gauge", "Wrong metric type"
        assert msg.title == "oracle_account_balance_ETH", "Wrong metric title"
        assert (
            msg.description == "Balance of oracle contract (ETH)"
        ), "Wrong metric description"
        assert msg.labels == {}, "Wrong labels"

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.ADD_METRIC
        ), "Wrong message performative"
        assert msg.type == "Gauge", "Wrong metric type"
        assert msg.title == "num_oracle_updates", "Wrong metric title"
        assert (
            msg.description == "Number of updates published to oracle contract"
        ), "Wrong metric description"
        assert msg.labels == {}, "Wrong labels"

    def test_setup_with_contract_config(self):
        """Test the setup method of the simple_oracle behaviour for existing contract."""
        prometheus_dialogues = cast(
            PrometheusDialogues,
            self.simple_oracle_behaviour.context.prometheus_dialogues,
        )
        prometheus_dialogues.enabled = False
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy.is_contract_deployed = True

        self.simple_oracle_behaviour.setup()
        self.assert_quantity_in_outbox(0)

    def test_act_pre_deploy(self):
        """Test the act method of the simple_oracle behaviour before contract is deployed."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == LedgerApiMessage.Performative.GET_BALANCE
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong metric type"
        assert msg.address == cast(
            str,
            self.simple_oracle_behaviour.context.agent_addresses.get(
                strategy.ledger_id
            ),
        ), "Wrong metric title"

    def test_act_grant_role(self):
        """Test the act method of the simple_oracle behaviour before role is granted."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy.is_contract_deployed = True
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(2)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == LedgerApiMessage.Performative.GET_BALANCE
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong metric type"
        assert msg.address == cast(
            str,
            self.simple_oracle_behaviour.context.agent_addresses.get(
                strategy.ledger_id
            ),
        ), "Wrong metric title"

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_RAW_TRANSACTION
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong ledger_id"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert (
            msg.contract_address == strategy.contract_address
        ), "Wrong contract address"
        assert msg.callable == "get_grant_role_transaction", "Wrong callable"

    def test_act_update(self):
        """Test the act method of the simple_oracle behaviour for normal updating."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS
        strategy.is_contract_deployed = True
        strategy.is_oracle_role_granted = True
        self.simple_oracle_behaviour.context.shared_state["oracle_data"] = {
            "some_key": "some_value"
        }
        self.simple_oracle_behaviour.act()
        self.assert_quantity_in_outbox(2)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == LedgerApiMessage.Performative.GET_BALANCE
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong metric type"
        assert msg.address == cast(
            str,
            self.simple_oracle_behaviour.context.agent_addresses.get(
                strategy.ledger_id
            ),
        ), "Wrong metric title"

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_RAW_TRANSACTION
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong ledger_id"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert (
            msg.contract_address == strategy.contract_address
        ), "Wrong contract address"
        assert msg.callable == "get_update_transaction", "Wrong callable"

    def test__request_contract_deploy_transaction(self):
        """Test that the _request_contract_deploy_transaction function sends the right message to the contract_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)

        self.simple_oracle_behaviour._request_contract_deploy_transaction()
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong ledger_id"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert msg.callable == "get_deploy_transaction", "Wrong callable"

    def test__request_grant_role_transaction(self):
        """Test that the _request_grant_role_transaction function sends the right message to the contract_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS

        self.simple_oracle_behaviour._request_grant_role_transaction()
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_RAW_TRANSACTION
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong ledger_id"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert (
            msg.contract_address == strategy.contract_address
        ), "Wrong contract address"
        assert msg.callable == "get_grant_role_transaction", "Wrong callable"

    def test__request_update_transaction(self):
        """Test that the _request_update_transaction function sends the right message to the contract_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.contract_address = DEFAULT_ADDRESS

        update_args = {"some": "args"}
        self.simple_oracle_behaviour._request_update_transaction(update_args)
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == ContractApiMessage.Performative.GET_RAW_TRANSACTION
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong ledger_id"
        assert msg.contract_id == str(CONTRACT_PUBLIC_ID), "Wrong contract_id"
        assert (
            msg.contract_address == strategy.contract_address
        ), "Wrong contract address"
        assert msg.callable == "get_update_transaction", "Wrong callable"

    def test__get_balance(self):
        """Test that the _get_balance function sends the right message to the ledger_api."""
        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        self.simple_oracle_behaviour.context.agent_addresses[
            strategy.ledger_id
        ] = "some_eth_address"

        self.simple_oracle_behaviour._get_balance()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == LedgerApiMessage.Performative.GET_BALANCE
        ), "Wrong message performative"
        assert msg.ledger_id == strategy.ledger_id, "Wrong metric type"
        assert msg.address == cast(
            str,
            self.simple_oracle_behaviour.context.agent_addresses.get(
                strategy.ledger_id
            ),
        ), "Wrong metric title"

    def test_add_prometheus_metric(self):
        """Test the send_http_request_message method of the simple_oracle behaviour."""
        self.simple_oracle_behaviour.add_prometheus_metric(
            "some_metric", "Gauge", "some_description", {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.ADD_METRIC
        ), "Wrong message performative"
        assert msg.type == "Gauge", "Wrong metric type"
        assert msg.title == "some_metric", "Wrong metric title"
        assert msg.description == "some_description", "Wrong metric description"
        assert msg.labels == {"label_key": "label_value"}, "Wrong labels"

    def test_update_prometheus_metric(self):
        """Test the test_update_prometheus_metric method of the simple_oracle behaviour."""
        self.simple_oracle_behaviour.update_prometheus_metric(
            "some_metric", "set", 0.0, {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.UPDATE_METRIC
        ), "Wrong message performative"
        assert msg.callable == "set", "Wrong metric callable"
        assert msg.title == "some_metric", "Wrong metric title"
        assert msg.value == 0.0, "Wrong metric value"
        assert msg.labels == {"label_key": "label_value"}, "Wrong labels"

    def test_teardown(self):
        """Test that the teardown method of the simple_oracle behaviour leaves no messages in the outbox."""
        assert self.simple_oracle_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
