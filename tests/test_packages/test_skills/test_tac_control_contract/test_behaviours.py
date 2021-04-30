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
"""This module contains the tests of the behaviour classes of the tac control contract skill."""

import datetime
import logging
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

from aea.helpers.search.models import Description
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.skills.tac_control_contract.behaviours import (
    LEDGER_API_ADDRESS,
    TacBehaviour,
)
from packages.fetchai.skills.tac_control_contract.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    TacDialogues,
)
from packages.fetchai.skills.tac_control_contract.game import (
    AgentState,
    Configuration,
    Game,
    Phase,
)
from packages.fetchai.skills.tac_control_contract.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test tac behaviour of tac_control_contract."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "tac_control_contract"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_behaviour = cast(TacBehaviour, cls._skill.skill_context.behaviours.tac)
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.parameters = cast(Parameters, cls._skill.skill_context.parameters)
        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.logger = cls.tac_behaviour.context.logger

        cls.mocked_reg_start_time = cls._time("00:02")
        cls.mocked_reg_end_time = cls._time("00:04")
        cls.mocked_start_time = cls._time("00:06")
        cls.mocked_end_time = cls._time("00:08")

        cls.parameters._registration_start_time = cls.mocked_reg_start_time
        cls.parameters._registration_end_time = cls.mocked_reg_end_time
        cls.parameters._start_time = cls.mocked_start_time
        cls.parameters._end_time = cls.mocked_end_time

        cls.mocked_description = Description({"foo1": 1, "bar1": 2})

        cls.agent_1_address = "agent_address_1"
        cls.agent_1_name = "agent_name_1"
        cls.agent_2_address = "agent_address_2"
        cls.agent_2_name = "agent_name_2"

        cls.amount_by_currency_id = {"1": 10}
        cls.exchange_params_by_currency_id = {"1": 1.0}
        cls.quantities_by_good_id = {"2": 1, "3": 2}
        cls.utility_params_by_good_id = {"2": 1.0, "3": 1.5}

        cls.agent_1_state = AgentState(
            cls.agent_1_address,
            cls.amount_by_currency_id,
            cls.exchange_params_by_currency_id,
            cls.quantities_by_good_id,
            cls.utility_params_by_good_id,
        )
        cls.agent_2_state = AgentState(
            cls.agent_2_address,
            cls.amount_by_currency_id,
            cls.exchange_params_by_currency_id,
            cls.quantities_by_good_id,
            cls.utility_params_by_good_id,
        )

    def test_setup(self):
        """Test the setup method of the tac behaviour."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_behaviour.setup()

        # after
        assert self.game.phase == Phase.CONTRACT_DEPLOYMENT_PROPOSAL

        self.assert_quantity_in_outbox(2)

        # first message is produced in superclass (from tac_control skill) which has its own unit tests
        self.drop_messages_from_outbox(1)

        # _request_contract_deploy_transaction
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.parameters.ledger_id,
            contract_id=self.parameters.contract_id,
            callable=ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "gas": 5000000,
                }
            ),
        )
        assert has_attributes, error_str
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).terms
            == self.parameters.get_deploy_terms()
        )
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).callable
            == ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        mock_logger.assert_any_call(
            logging.INFO, "requesting contract deployment transaction..."
        )

    @staticmethod
    def _time(time: str):
        date_time = "01 01 2020  " + time
        return datetime.datetime.strptime(date_time, "%d %m %Y %H:%M")

    @staticmethod
    def _mock_time(time: str) -> Mock:
        mocked_now_time = TestSkillBehaviour._time(time)

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time
        return datetime_mock

    def test_act_i(self):
        """Test the act method of the tac behaviour where phase is contract_deployed and reg_start_time < now < reg_end_time."""
        # setup
        self.game._phase = Phase.CONTRACT_DEPLOYED

        mocked_now = self._mock_time("00:03")

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(self.tac_behaviour, "_register_tac") as mock_register_tac:
                with patch.object(self.logger, "log") as mock_logger:
                    self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.GAME_REGISTRATION

        # _register_tac is a superclass method with its own unit test in test_tac_control
        mock_register_tac.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO, f"TAC open for registration until: {self.mocked_reg_end_time}"
        )

    def test_act_ii(self):
        """Test the act method of the tac behaviour where phase is game_registration and reg_end_time < now < start_time and nb_agent < min_nb_agents."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now = self._mock_time("00:05")

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(
            COUNTERPARTY_AGENT_ADDRESS, self.agent_1_name
        )

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(self.tac_behaviour, "_cancel_tac") as mock_cancel_tac:
                with patch.object(
                    self.tac_behaviour, "_unregister_tac"
                ) as mock_unregister_tac:
                    with patch.object(self.logger, "log") as mock_logger:
                        self.tac_behaviour.act()

        # after
        mock_logger.assert_any_call(logging.INFO, "closing registration!")
        mock_logger.assert_any_call(
            logging.INFO,
            f"registered agents={1}, minimum agents required={self.parameters._min_nb_agents}",
        )

        # _cancel_tac is a superclass method with its own unit test in test_tac_control
        mock_cancel_tac.assert_called_with(self.game)

        assert self.game.phase == Phase.POST_GAME

        # _unregister_tac is a superclass method with its own unit test in test_tac_control
        mock_unregister_tac.assert_called_once()

        assert self.skill.skill_context.is_active is False

    def test_act_iii(self):
        """Test the act method of the tac behaviour where phase is game_registration and reg_end_time < now < start_time and nb_agent >= min_nb_agents."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now = self._mock_time("00:05")

        self.parameters._contract_address = "some_contract_address"

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(
                self.tac_behaviour, "_unregister_tac"
            ) as mock_unregister_tac:
                with patch.object(self.logger, "log") as mock_logger:
                    self.tac_behaviour.act()

        # after
        mock_logger.assert_any_call(logging.INFO, "closing registration!")
        assert self.game.phase == Phase.GAME_SETUP
        assert self.game.conf.contract_address == self.parameters.contract_address

        # _unregister_tac is a superclass method with its own unit test in test_tac_control
        mock_unregister_tac.assert_called_once()

    def test_act_iv(self):
        """Test the act method of the tac behaviour where phase is GAME_SETUP and reg_end_time < now < start_time."""
        # setup
        self.game._phase = Phase.GAME_SETUP

        mocked_now = self._mock_time("00:05")

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        self.game._conf = Configuration(
            "v1",
            1,
            self.game.registration.agent_addr_to_name,
            {"1": "currency_name"},
            {"2": "good_1", "3": "good_2"},
        )

        self.parameters._contract_address = "some_contract_address"

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(self.logger, "log") as mock_logger:
                self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.TOKENS_CREATION_PROPOSAL

        # _request_create_items_transaction
        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.parameters.ledger_id,
            contract_id=self.parameters.contract_id,
            contract_address=self.parameters.contract_address,
            callable=ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "token_ids": [2, 3, 1],
                    "gas": 5000000,
                }
            ),
        )
        assert has_attributes, error_str
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).terms
            == self.parameters.get_create_token_terms()
        )
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).callable
            == ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION
        )
        mock_logger.assert_any_call(
            logging.INFO, "requesting create items transaction..."
        )

    def test_act_v(self):
        """Test the act method of the tac behaviour where phase is TOKENS_CREATED."""
        # setup
        self.game._phase = Phase.TOKENS_CREATED

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        self.game._initial_agent_states = {
            self.agent_1_address: self.agent_1_state,
            self.agent_2_address: self.agent_2_state,
        }

        self.parameters._contract_address = "some_contract_address"

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.TOKENS_MINTING_PROPOSAL

        # _request_mint_items_transaction
        assert self.game.is_allowed_to_mint is False

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting mint_items transactions for agent={self.agent_1_name}.",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.parameters.ledger_id,
            contract_id=self.parameters.contract_id,
            contract_address=self.parameters.contract_address,
            callable=ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "recipient_address": self.agent_1_address,
                    "token_ids": [2, 3, 1],
                    "mint_quantities": [1, 2, 10],
                    "gas": 5000000,
                }
            ),
        )
        assert has_attributes, error_str

        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).terms
            == self.parameters.get_mint_token_terms()
        )
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).callable
            == ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
        )

    def test_request_mint_items_transaction_not_allowed_to_mint(self):
        """Test the _request_mint_items_transaction method of the tac behaviour where is_allowed_to_mint is False."""
        # setup
        self.game._phase = Phase.TOKENS_CREATED
        self.game.is_allowed_to_mint = False

        # operation
        self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.TOKENS_MINTING_PROPOSAL

        # _request_mint_items_transaction
        self.assert_quantity_in_outbox(0)

    def test_request_mint_items_transaction_agent_state_is_none(self):
        """Test the _request_mint_items_transaction method of the tac behaviour where agent_state is None."""
        # setup
        self.game._phase = Phase.TOKENS_CREATED
        self.game._initial_agent_states = {self.agent_1_address: None}

        # operation
        self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.TOKENS_MINTING_PROPOSAL

        # _request_mint_items_transaction
        assert self.game.is_allowed_to_mint is False
        self.assert_quantity_in_outbox(0)

    def test_act_vi(self):
        """Test the act method of the tac behaviour where phase is TOKENS_MINTING_PROPOSAL."""
        # setup
        self.game._phase = Phase.TOKENS_MINTING_PROPOSAL

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        self.game._initial_agent_states = {
            self.agent_1_address: self.agent_1_state,
            self.agent_2_address: self.agent_2_state,
        }

        self.parameters._contract_address = "some_contract_address"

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.TOKENS_MINTING_PROPOSAL

        # _request_mint_items_transaction
        assert self.game.is_allowed_to_mint is False

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting mint_items transactions for agent={self.agent_1_name}.",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.parameters.ledger_id,
            contract_id=self.parameters.contract_id,
            contract_address=self.parameters.contract_address,
            callable=ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "recipient_address": self.agent_1_address,
                    "token_ids": [2, 3, 1],
                    "mint_quantities": [1, 2, 10],
                    "gas": 5000000,
                }
            ),
        )
        assert has_attributes, error_str

        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).terms
            == self.parameters.get_mint_token_terms()
        )
        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).callable
            == ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
        )

    def test_act_vii(self):
        """Test the act method of the tac behaviour where phase is TOKENS_MINTED and start_time < now < end_time."""
        # setup
        self.game._phase = Phase.TOKENS_MINTED

        mocked_now = self._mock_time("00:07")

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(self.tac_behaviour, "_start_tac") as mock_start_tac:
                with patch.object(self.logger, "log"):
                    self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.GAME

        # _start_tac is a superclass method with its own unit test in test_tac_control
        mock_start_tac.assert_called_with(self.game)

    def test_act_viii(self):
        """Test the act method of the tac behaviour where phase is GAME and end_time < now."""
        # setup
        self.game._phase = Phase.GAME

        mocked_now = self._mock_time("00:09")

        # operation
        with patch("datetime.datetime", new=mocked_now):
            with patch.object(self.tac_behaviour, "_cancel_tac") as mock_cancel_tac:
                with patch.object(self.logger, "log"):
                    self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.POST_GAME

        # _cancel_tac is a superclass method with its own unit test in test_tac_control
        mock_cancel_tac.assert_called_with(self.game)

        assert self.skill.skill_context.is_active is False
