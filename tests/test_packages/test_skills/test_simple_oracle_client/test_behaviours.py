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
"""This module contains the tests of the behaviour classes of the simple oracle client skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.contracts.fet_erc20.contract import PUBLIC_ID as ERC20_PUBLIC_ID
from packages.fetchai.contracts.oracle_client.contract import (
    PUBLIC_ID as CLIENT_CONTRACT_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.skills.simple_oracle_client.behaviours import (
    SimpleOracleClientBehaviour,
)
from packages.fetchai.skills.simple_oracle_client.strategy import Strategy

from tests.conftest import ROOT_DIR


DEFAULT_ADDRESS = "0x0000000000000000000000000000000000000000"
ETHEREUM_LEDGER_ID = "ethereum"
FETCHAI_LEDGER_ID = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of simple oracle client."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle_client"
    )

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.simple_oracle_client_behaviour = cast(
            SimpleOracleClientBehaviour,
            cls._skill.skill_context.behaviours.simple_oracle_client_behaviour,
        )

    def test_setup(self):
        """Test the setup method of the simple_oracle_client behaviour."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.oracle_contract_address = DEFAULT_ADDRESS
        strategy.erc20_address = DEFAULT_ADDRESS
        strategy.is_oracle_contract_set = True
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_client_behaviour.setup()

        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
        )
        assert has_attributes, error_str

    def test_setup_with_contract_set(self):
        """Test the setup method of the simple_oracle_client behaviour for existing contract."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.client_contract_address = DEFAULT_ADDRESS
        strategy.oracle_contract_address = DEFAULT_ADDRESS
        strategy.erc20_address = DEFAULT_ADDRESS
        strategy.is_client_contract_deployed = True
        strategy.is_oracle_contract_set = True
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        with patch.object(
            self.simple_oracle_client_behaviour.context.logger, "log"
        ) as mock_logger:
            self.simple_oracle_client_behaviour.setup()
        mock_logger.assert_any_call(
            logging.INFO, "Fetch oracle client contract address already added",
        )
        self.assert_quantity_in_outbox(0)

    def test_act_pre_deploy(self):
        """Test the act method of the simple_oracle_client behaviour before contract is deployed."""

        with patch.object(
            self.simple_oracle_client_behaviour.context.logger, "log"
        ) as mock_logger:
            self.simple_oracle_client_behaviour.act()
        mock_logger.assert_any_call(
            logging.INFO, "Oracle client contract not yet deployed",
        )
        self.assert_quantity_in_outbox(0)

    def test_act_approve_transactions(self):
        """Test the act method of the simple_oracle_client behaviour before transactions are approved."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.client_contract_address = DEFAULT_ADDRESS
        strategy.oracle_contract_address = DEFAULT_ADDRESS
        strategy.erc20_address = DEFAULT_ADDRESS
        strategy.is_client_contract_deployed = True
        strategy.is_oracle_contract_set = True
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_client_behaviour.act()
        self.assert_quantity_in_outbox(1)

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(ERC20_PUBLIC_ID),
            contract_address=strategy.client_contract_address,
            callable="get_approve_transaction",
        )
        assert has_attributes, error_str

    def test_act_query(self):
        """Test the act method of the simple_oracle_client behaviour for normal querying."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.client_contract_address = DEFAULT_ADDRESS
        strategy.oracle_contract_address = DEFAULT_ADDRESS
        strategy.erc20_address = DEFAULT_ADDRESS
        strategy.is_client_contract_deployed = True
        strategy.is_oracle_transaction_approved = True
        strategy.is_oracle_contract_set = True
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_client_behaviour.act()
        self.assert_quantity_in_outbox(1)
        assert strategy.is_oracle_contract_set

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            contract_address=strategy.client_contract_address,
            callable="get_query_transaction",
        )
        assert has_attributes, error_str

    def test__request_contract_deploy_transaction(self):
        """Test that the _request_contract_deploy_transaction function sends the right message to the contract_api for ethereum ledger."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.oracle_contract_address = "some_address"
        strategy._ledger_id = ETHEREUM_LEDGER_ID

        self.simple_oracle_client_behaviour._request_contract_deploy_transaction()
        self.assert_quantity_in_outbox(1)

        kwargs = strategy.get_deploy_kwargs()
        assert "fetchOracleContractAddress" in kwargs.body

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=kwargs,
        )
        assert has_attributes, error_str

    def test__request_contract_store_transaction(self):
        """Test that the _request_contract_deploy_transaction function sends the right message to the contract_api for fetchai ledger."""
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.oracle_contract_address = "some_address"
        strategy._ledger_id = FETCHAI_LEDGER_ID

        self.simple_oracle_client_behaviour._request_contract_deploy_transaction()
        self.assert_quantity_in_outbox(1)

        kwargs = strategy.get_deploy_kwargs()
        assert "fetchOracleContractAddress" not in kwargs.body

        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=kwargs,
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test that the teardown method of the simple_oracle_client behaviour leaves no messages in the outbox."""
        assert self.simple_oracle_client_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
