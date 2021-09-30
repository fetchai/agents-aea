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
"""This module contains the tests of the handler classes of the tac participation skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.state_update.message import StateUpdateMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    OefSearchDialogues,
    StateUpdateDialogue,
    StateUpdateDialogues,
    TacDialogues,
)
from packages.fetchai.skills.tac_participation.game import Game, Phase
from packages.fetchai.skills.tac_participation.handlers import (
    OefSearchHandler,
    TacHandler,
)

from tests.conftest import ROOT_DIR


class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef
        )
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )
        cls.controller_address = "some_controller_address"

    def test_setup(self):
        """Test the setup method of the oef handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                to=str(self.skill.skill_context.skill_id),
                oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received OEF Search error: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference}, oef_error_operation={incoming_message.oef_error_operation}",
        )

    def test_on_search_result(self):
        """Test the _on_search_result method of the oef handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=(self.controller_address,),
            ),
        )
        self.game._phase = Phase.PRE_GAME

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        # _on_search_result
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"on search result: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference} agents={incoming_message.agents}",
        )

        # _on_controller_search_result
        mock_logger.assert_any_call(
            logging.INFO, "found the TAC controller. Registering...",
        )

        # _register_to_tac
        assert self.game._expected_controller_addr == self.controller_address
        assert self.game.phase == Phase.GAME_REGISTRATION

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            to=self.controller_address,
            sender=self.skill.skill_context.agent_address,
            agent_name=self.skill.skill_context.agent_name,
        )
        assert has_attributes, error_str

        assert self.game._tac_dialogue is not None
        assert self.skill.skill_context.behaviours.tac_search.is_active is False
        assert (
            self.skill.skill_context.shared_state.get("tac_version_id", None)
            == self.game.expected_version_id
        )

    def test_on_controller_search_result_i(self):
        """Test the _on_controller_search_result method of the oef handler where phase is not PRE_GAME."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=("agent_1", "agent_2"),
            ),
        )
        self.game._phase = Phase.GAME

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        # _on_search_result
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"on search result: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference} agents={incoming_message.agents}",
        )

        # _on_controller_search_result
        mock_logger.assert_any_call(
            logging.DEBUG,
            "ignoring controller search result, the agent is already competing.",
        )

    def test_on_controller_search_result_ii(self):
        """Test the _on_controller_search_result method of the oef handler where list of agent addresses is empty."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=tuple(),
            ),
        )
        self.game._phase = Phase.PRE_GAME

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        # _on_search_result
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"on search result: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference} agents={incoming_message.agents}",
        )

        # _on_controller_search_result
        mock_logger.assert_any_call(
            logging.INFO, "couldn't find the TAC controller. Retrying...",
        )

    def test_on_controller_search_result_more_than_one_agents(self):
        """Test the _on_controller_search_result method of the oef handler where list of agents contains more than one agents."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=("agent_1", "agent_2"),
            ),
        )
        self.game._phase = Phase.PRE_GAME

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        # _on_search_result
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"on search result: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference} agents={incoming_message.agents}",
        )

        # _on_controller_search_result
        mock_logger.assert_any_call(
            logging.WARNING, "found more than one TAC controller. Retrying...",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            to=str(self.skill.skill_context.skill_id),
            service_description="some_service_description",
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={invalid_performative} in dialogue={self.oef_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestTacHandler(BaseSkillTestCase):
    """Test tac handler of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_handler = cast(TacHandler, cls._skill.skill_context.handlers.tac)
        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)
        cls.state_update_dialogues = cast(
            StateUpdateDialogues, cls._skill.skill_context.state_update_dialogues
        )
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.logger = cls.tac_handler.context.logger

        cls.agent_name = "some_agent_name"
        cls.amount_by_currency_id = {"1": 10}
        cls.exchange_params_by_currency_id = {"1": 1.0}
        cls.quantities_by_good_id = {"2": 10}
        cls.utility_params_by_good_id = {"2": 1.0}
        cls.fee_by_currency_id = {"1": 1}
        cls.agent_addr_to_name = {COUNTERPARTY_AGENT_ADDRESS: "some_name"}
        cls.currency_id_to_name = {"1": "FETCH"}
        cls.good_id_to_name = {"2": "Good_1"}
        cls.version_id = "v1"
        cls.list_of_messages = (
            DialogueMessage(
                TacMessage.Performative.REGISTER, {"agent_name": cls.agent_name}, True
            ),
            DialogueMessage(
                TacMessage.Performative.GAME_DATA,
                {
                    "amount_by_currency_id": cls.amount_by_currency_id,
                    "exchange_params_by_currency_id": cls.exchange_params_by_currency_id,
                    "quantities_by_good_id": cls.quantities_by_good_id,
                    "utility_params_by_good_id": cls.utility_params_by_good_id,
                    "fee_by_currency_id": cls.fee_by_currency_id,
                    "agent_addr_to_name": cls.agent_addr_to_name,
                    "currency_id_to_name": cls.currency_id_to_name,
                    "good_id_to_name": cls.good_id_to_name,
                    "version_id": cls.version_id,
                },
            ),
            DialogueMessage(
                TacMessage.Performative.TRANSACTION,
                {
                    "transaction_id": "some_transaction_id",
                    "ledger_id": "some_ledger_id",
                    "sender_address": "some_sender_address",
                    "counterparty_address": "some_counterparty_address",
                    "amount_by_currency_id": {"1": 5},
                    "fee_by_currency_id": {"1": 1},
                    "quantities_by_good_id": {"2": -5},
                    "nonce": "some_nonce",
                    "sender_signature": "some_sender_signature",
                    "counterparty_signature": "some_counterparty_signature",
                },
            ),
        )

        cls.list_of_state_update_messages = (
            DialogueMessage(
                StateUpdateMessage.Performative.INITIALIZE,
                {
                    "amount_by_currency_id": cls.amount_by_currency_id,
                    "quantities_by_good_id": cls.quantities_by_good_id,
                },
            ),
        )

        cls.game._expected_controller_addr = COUNTERPARTY_AGENT_ADDRESS

    def test_setup(self):
        """Test the setup method of the tac handler."""
        assert self.tac_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_sender_not_equal_to_expected_controller(self):
        """Test the handle method of the tac handler where message sender is NOT equal to the expected controller."""
        # setup
        self.game._expected_controller_addr = "some_different_controller_address"

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            error_code=TacMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(
                ValueError,
                match="The sender of the message is not the controller agent we registered with.",
            ):
                self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"handling controller response. performative={incoming_message.performative}",
        )

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the tac handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=TacMessage.Performative.CANCELLED,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received invalid tac message={incoming_message}, unidentified dialogue.",
        )

    def test_on_tac_error_code_i(self):
        """Test the _on_tac_error method of the tac handler where error_code is NOT TRANSACTION_NOT_VALID."""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        error_code = TacMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            error_code=error_code,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received error from the controller in dialogue={dialogue}. error_msg={TacMessage.ErrorCode.to_msg(error_code.value)}",
        )

    def test_on_tac_error_code_ii(self):
        """Test the _on_tac_error method of the tac handler where error_code is TRANSACTION_NOT_VALID."""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        tx_id = "some_tx_id"
        error_code = TacMessage.ErrorCode.TRANSACTION_NOT_VALID
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            error_code=error_code,
            info={"transaction_id": tx_id},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received error from the controller in dialogue={dialogue}. error_msg={TacMessage.ErrorCode.to_msg(error_code.value)}",
        )
        mock_logger.assert_any_call(
            logging.WARNING, f"received error on transaction id: {tx_id[-10:]}",
        )

    def test_on_start_i(self):
        """Test the _on_start method of the tac handler."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._is_using_contract = False

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id=self.amount_by_currency_id,
                exchange_params_by_currency_id=self.exchange_params_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
                utility_params_by_good_id=self.utility_params_by_good_id,
                fee_by_currency_id=self.fee_by_currency_id,
                agent_addr_to_name=self.agent_addr_to_name,
                currency_id_to_name=self.currency_id_to_name,
                good_id_to_name=self.good_id_to_name,
                version_id=self.version_id,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.game, "init"):
                self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received start event from the controller. Starting to compete...",
        )

        self.assert_quantity_in_decision_making_queue(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_decision_maker_inbox(),
            message_type=StateUpdateMessage,
            performative=StateUpdateMessage.Performative.INITIALIZE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            amount_by_currency_id=incoming_message.amount_by_currency_id,
            quantities_by_good_id=incoming_message.quantities_by_good_id,
            exchange_params_by_currency_id=incoming_message.exchange_params_by_currency_id,
            utility_params_by_good_id=incoming_message.utility_params_by_good_id,
        )
        assert has_attributes, error_str
        assert (
            self.skill.skill_context.shared_state["fee_by_currency_id"]
            == incoming_message.fee_by_currency_id
        )
        assert self.game.state_update_dialogue is not None

    def test_on_start_ii(self):
        """Test the _on_start method of the tac handler where phase is NOT GAME_REGISTRATION."""
        # setup
        self.game._phase = Phase.PRE_GAME
        self.game._is_using_contract = False

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            message_type=TacMessage,
            performative=TacMessage.Performative.GAME_DATA,
            amount_by_currency_id=self.amount_by_currency_id,
            exchange_params_by_currency_id=self.exchange_params_by_currency_id,
            quantities_by_good_id=self.quantities_by_good_id,
            utility_params_by_good_id=self.utility_params_by_good_id,
            fee_by_currency_id=self.fee_by_currency_id,
            agent_addr_to_name=self.agent_addr_to_name,
            currency_id_to_name=self.currency_id_to_name,
            good_id_to_name=self.good_id_to_name,
            version_id=self.version_id,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"we do not expect a start message in game phase={self.game.phase.value}",
        )

    def test_on_start_iii(self):
        """Test the _on_start method of the tac handler where game uses contract."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._is_using_contract = True

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        contract_address = "some_contract_address"
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id=self.amount_by_currency_id,
                exchange_params_by_currency_id=self.exchange_params_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
                utility_params_by_good_id=self.utility_params_by_good_id,
                fee_by_currency_id=self.fee_by_currency_id,
                agent_addr_to_name=self.agent_addr_to_name,
                currency_id_to_name=self.currency_id_to_name,
                good_id_to_name=self.good_id_to_name,
                version_id=self.version_id,
                info={"contract_address": contract_address},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.game, "init"):
                with patch.object(
                    self.tac_handler, "_update_ownership_and_preferences"
                ) as mocked_uoap:
                    self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received start event from the controller. Starting to compete...",
        )
        assert self.game.contract_address == contract_address
        assert (
            self.skill.skill_context.shared_state["erc1155_contract_address"]
            == contract_address
        )
        mock_logger.assert_any_call(
            logging.INFO, f"received a contract address: {contract_address}",
        )
        mocked_uoap.assert_called_once()

    def test_on_start_iv(self):
        """Test the _on_start method of the tac handler where game uses contract."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._is_using_contract = True

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id=self.amount_by_currency_id,
                exchange_params_by_currency_id=self.exchange_params_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
                utility_params_by_good_id=self.utility_params_by_good_id,
                fee_by_currency_id=self.fee_by_currency_id,
                agent_addr_to_name=self.agent_addr_to_name,
                currency_id_to_name=self.currency_id_to_name,
                good_id_to_name=self.good_id_to_name,
                version_id=self.version_id,
                info={"contract_address": None},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.game, "init"):
                with patch.object(
                    self.tac_handler, "_update_ownership_and_preferences"
                ) as mocked_uoap:
                    self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received start event from the controller. Starting to compete...",
        )
        mock_logger.assert_any_call(
            logging.WARNING, "did not receive a contract address!",
        )
        mocked_uoap.assert_not_called()

    def test_on_cancelled_i(self):
        """Test the _on_cancelled method of the tac handler where phase is GAME_REGISTRATION."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.CANCELLED,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, "received cancellation from the controller.",
        )
        assert self.game.phase == Phase.POST_GAME
        assert self.skill.skill_context.is_active is False
        assert self.skill.skill_context.shared_state["is_game_finished"] is True

    def test_on_cancelled_ii(self):
        """Test the _on_cancelled method of the tac handler where phase is GAME."""
        # setup
        self.game._phase = Phase.GAME

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.CANCELLED,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, "received cancellation from the controller.",
        )
        assert self.game.phase == Phase.POST_GAME
        assert self.skill.skill_context.is_active is False
        assert self.skill.skill_context.shared_state["is_game_finished"] is True

    def test_on_cancelled_iii(self):
        """Test the _on_cancelled method of the tac handler where phase is NOT GAME_REGISTRATION nor GAME."""
        # setup
        self.game._phase = Phase.PRE_GAME

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )

        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.CANCELLED,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"we do not expect a message in game phase={self.game.phase.value}, received msg={incoming_message}",
        )

    def test_on_transaction_confirmed_i(self):
        """Test the _on_transaction_confirmed method of the tac handler."""
        # setup
        self.game._phase = Phase.GAME

        state_update_dialogue = cast(
            StateUpdateDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.state_update_dialogues,
                messages=self.list_of_state_update_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        self.game._state_update_dialogue = state_update_dialogue

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:3]
        )

        transaction_id = "some_transaction_id"
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
                transaction_id=transaction_id,
                amount_by_currency_id=self.amount_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received transaction confirmation from the controller: transaction_id={transaction_id}",
        )

        self.assert_quantity_in_decision_making_queue(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_decision_maker_inbox(),
            message_type=StateUpdateMessage,
            performative=StateUpdateMessage.Performative.APPLY,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            amount_by_currency_id=incoming_message.amount_by_currency_id,
            quantities_by_good_id=incoming_message.quantities_by_good_id,
        )
        assert has_attributes, error_str
        assert (
            incoming_message.transaction_id
            in self.skill.skill_context.shared_state["confirmed_tx_ids"]
        )

    def test_on_transaction_confirmed_ii(self):
        """Test the _on_transaction_confirmed method of the tac handler where phase is not GAME."""
        # setup
        self.game._phase = Phase.PRE_GAME

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:3]
        )

        transaction_id = "some_transaction_id"
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
                transaction_id=transaction_id,
                amount_by_currency_id=self.amount_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"we do not expect a transaction in game phase={self.game.phase.value}, received msg={incoming_message}",
        )

    def test_on_transaction_confirmed_iii(self):
        """Test the _on_transaction_confirmed method of the tac handler where state_update dialogue is empty."""
        # setup
        self.game._phase = Phase.GAME

        state_update_dialogue = cast(
            StateUpdateDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.state_update_dialogues,
                messages=self.list_of_state_update_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        state_update_dialogue._incoming_messages = []
        state_update_dialogue._outgoing_messages = []
        self.game._state_update_dialogue = state_update_dialogue

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:3]
        )

        transaction_id = "some_transaction_id"
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                message_type=TacMessage,
                performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
                transaction_id=transaction_id,
                amount_by_currency_id=self.amount_by_currency_id,
                quantities_by_good_id=self.quantities_by_good_id,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(ValueError, match="Could not retrieve last message."):
                self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received transaction confirmation from the controller: transaction_id={transaction_id}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the tac handler."""
        # setup
        tac_dialogue = self.prepare_skill_dialogue(
            dialogues=self.tac_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=tac_dialogue,
            performative=TacMessage.Performative.UNREGISTER,
            sender=COUNTERPARTY_AGENT_ADDRESS,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle tac message of performative={incoming_message.performative} in dialogue={tac_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the tac handler."""
        assert self.tac_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
