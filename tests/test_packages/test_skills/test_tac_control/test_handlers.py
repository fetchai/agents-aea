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
"""This module contains the tests of the handler classes of the tac control skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import PropertyMock, patch

import pytest

from aea.helpers.search.models import Attribute, DataModel, Description, Location
from aea.protocols.dialogue.base import DialogueMessage, Dialogues
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.behaviours import TacBehaviour
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogues,
    TacDialogues,
)
from packages.fetchai.skills.tac_control.game import (
    Configuration,
    Game,
    Phase,
    Transaction,
)
from packages.fetchai.skills.tac_control.handlers import OefSearchHandler, TacHandler
from packages.fetchai.skills.tac_control.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestTacHandler(BaseSkillTestCase):
    """Test tac handler of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_handler = cast(TacHandler, cls._skill.skill_context.handlers.tac)
        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.parameters = cast(Parameters, cls._skill.skill_context.parameters)

        cls.agent_name = "some_agent_name"
        cls.list_of_messages = (
            DialogueMessage(
                TacMessage.Performative.REGISTER, {"agent_name": cls.agent_name}, True
            ),
            DialogueMessage(
                TacMessage.Performative.GAME_DATA,
                {
                    "amount_by_currency_id": {"FET": 1},
                    "exchange_params_by_currency_id": {"FET": 1.0},
                    "quantities_by_good_id": {"G1": 10},
                    "utility_params_by_good_id": {"G1": 1.0},
                    "fee_by_currency_id": {"FET": 1},
                    "agent_addr_to_name": {COUNTERPARTY_AGENT_ADDRESS: "some_name"},
                    "currency_id_to_name": {"FET": "FETCH"},
                    "good_id_to_name": {"G1": "Good_1"},
                    "version_id": "v1",
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the fipa handler."""
        assert self.tac_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=TacMessage.Performative.CANCELLED,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid tac message={incoming_message}, unidentified dialogue (reference={incoming_message.dialogue_reference}).",
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"tac_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_on_register_not_pre_reg_phase(self):
        """Test the _on_register method of the tac handler where phase is NOT pre_registration."""
        # setup
        self.game._phase = Phase.PRE_GAME

        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            agent_name=self.agent_name,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received registration outside of game registration phase: '{incoming_message}'",
        )

    def test_on_register_agent_not_in_whitelist(self):
        """Test the _on_register method of the tac handler where the agent is NOT in the whitelist."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.parameters._whitelist = ["some_other_agent", "yet_another_agent"]

        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            agent_name=self.agent_name,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING, f"agent name not in whitelist: '{self.agent_name}'"
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            error_code=TacMessage.ErrorCode.AGENT_NAME_NOT_IN_WHITELIST,
        )
        assert has_attributes, error_str

    def test_on_register_agent_address_already_exists(self):
        """Test the _on_register method of the tac handler where the agent address of the sender is already registered."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._registration.register_agent(
            COUNTERPARTY_AGENT_ADDRESS, self.agent_name
        )

        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            agent_name="some_name",
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING, f"agent already registered: '{self.agent_name}'"
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            error_code=TacMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED,
        )
        assert has_attributes, error_str

    def test_on_register_agent_name_already_exists(self):
        """Test the _on_register method of the tac handler where the agent name of the sender is already registered."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._registration.register_agent("some_address", self.agent_name)

        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            agent_name=self.agent_name,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"agent with this name already registered: '{self.agent_name}'",
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            error_code=TacMessage.ErrorCode.AGENT_NAME_ALREADY_REGISTERED,
        )
        assert has_attributes, error_str

    def test_on_register(self):
        """Test the _on_register method of the tac handler, the successful case."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        incoming_message = self.build_incoming_message(
            message_type=TacMessage,
            performative=TacMessage.Performative.REGISTER,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            agent_name=self.agent_name,
        )

        # before
        assert self.game.registration.nb_agents == 0

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"agent '{incoming_message.sender}' registered as '{self.agent_name}'",
        )
        assert self.game.registration.nb_agents == 1

    def test_on_unregister_not_pre_reg_phase(self):
        """Test the _on_unregister method of the tac handler where phase is NOT pre_registration."""
        # setup
        self.game._phase = Phase.PRE_GAME

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue, performative=TacMessage.Performative.UNREGISTER,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received unregister outside of game registration phase: '{incoming_message}'",
        )

    def test_on_unregister_agent_address_not_registered(self):
        """Test the _on_unregister method of the tac handler where the agent address of the sender is not registered."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue, performative=TacMessage.Performative.UNREGISTER,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING, f"agent not registered: '{COUNTERPARTY_AGENT_ADDRESS}'"
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            error_code=TacMessage.ErrorCode.AGENT_NOT_REGISTERED,
        )
        assert has_attributes, error_str

    def test_on_unregister(self):
        """Test the _on_unregister method of the tac handler: successful."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION
        self.game._registration.register_agent(
            COUNTERPARTY_AGENT_ADDRESS, self.agent_name
        )
        self.game._registration.register_agent("address_2", "name_2")
        self.game._conf = Configuration(
            "v1",
            1,
            self.game.registration.agent_addr_to_name,
            {"key_1": "v_1"},
            {"k_1": "v_1", "k_2": "v_2"},
        )

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:1]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue, performative=TacMessage.Performative.UNREGISTER,
        )

        # before
        assert self.game.registration.nb_agents == 2

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG, f"agent unregistered: '{self.agent_name}'"
        )
        assert self.game.registration.nb_agents == 1

    def test_on_transaction(self):
        """Test the _on_transaction method of the tac handler where phase is NOT GAME."""
        # setup
        self.game._phase = Phase.PRE_GAME
        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=TacMessage.Performative.TRANSACTION,
            transaction_id="some_id",
            ledger_id="some_ledger",
            sender_address=COUNTERPARTY_AGENT_ADDRESS,
            counterparty_address=self.skill.skill_context.agent_address,
            amount_by_currency_id={"FET": 1},
            fee_by_currency_id={"FET": 2},
            quantities_by_good_id={"G1": 1},
            nonce="some_nonce",
            sender_signature="some_signature",
            counterparty_signature="some_other_signature",
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received transaction outside of game phase: '{incoming_message}'",
        )

    def test_on_transaction_valid(self):
        """Test the _on_transaction method of the tac handler where the transaction is valid."""
        # setup
        self.game._phase = Phase.GAME

        tac_participant_sender = COUNTERPARTY_AGENT_ADDRESS
        tac_participant_counterparty = "counterparties_counterparty"

        counterparty_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2], tac_participant_counterparty
        )
        self_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2],
        )

        ledger_id = "some_ledger"
        good_ids = ["G1"]
        nonce = "some_nonce"
        amount_by_currency_id = {"FET": 1}
        quantities_by_good_id = {"G1": 1}
        tx_id = Transaction.get_hash(
            ledger_id=ledger_id,
            sender_address=tac_participant_sender,
            counterparty_address=tac_participant_counterparty,
            good_ids=good_ids,
            sender_supplied_quantities=[1],
            counterparty_supplied_quantities=[0],
            sender_payable_amount=0,
            counterparty_payable_amount=1,
            nonce=nonce,
        )
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=self_dialogue,
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id=tx_id,
                ledger_id=ledger_id,
                sender_address=tac_participant_sender,
                counterparty_address=tac_participant_counterparty,
                amount_by_currency_id=amount_by_currency_id,
                fee_by_currency_id={"FET": 2},
                quantities_by_good_id=quantities_by_good_id,
                nonce=nonce,
                sender_signature="some_signature",
                counterparty_signature="some_other_signature",
            ),
        )
        tx = Transaction.from_message(incoming_message)

        mocked_holdings_summary = "some_holdings_summary"

        # operation
        with patch.object(
            type(self.game),
            "holdings_summary",
            new_callable=PropertyMock,
            return_value=mocked_holdings_summary,
        ):
            with patch.object(self.game, "is_transaction_valid", return_value=True):
                with patch.object(self.game, "settle_transaction"):
                    with patch.object(
                        self.tac_handler.context.logger, "log"
                    ) as mock_logger:
                        self.tac_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(2)

        # _on_transaction
        mock_logger.assert_any_call(logging.DEBUG, f"handling transaction: {tx}")

        # _handle_valid_transaction
        mock_logger.assert_any_call(
            logging.INFO, f"handling valid transaction: {tx_id[-10:]}"
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            to=tac_participant_sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            transaction_id=tx_id,
            amount_by_currency_id=amount_by_currency_id,
            quantities_by_good_id=quantities_by_good_id,
        )
        assert has_attributes, error_str

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            to=tac_participant_counterparty,
            sender=self.skill.skill_context.agent_address,
            # in this case message_id is negative so previous  negative id is  id + 1
            target=counterparty_dialogue.last_message.message_id + 1,
            transaction_id=tx.counterparty_hash,
            amount_by_currency_id=amount_by_currency_id,
            quantities_by_good_id=quantities_by_good_id,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction '{tx_id[-10:]}' between '{self.skill.skill_context.agent_address}' and '{self.skill.skill_context.agent_address}' settled successfully.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"total number of transactions settled: {len(self.game.transactions.confirmed)}",
        )
        mock_logger.assert_any_call(
            logging.INFO, f"current state:\n{mocked_holdings_summary}"
        )

    def test_handle_valid_transaction_recovered_tac_dialogue_not_1(self):
        """Test the _handle_valid_transaction method of the tac handler where the number of recivered tac dialogues is 0."""
        # setup
        self.game._phase = Phase.GAME

        tac_participant_sender = COUNTERPARTY_AGENT_ADDRESS
        tac_participant_counterparty = "counterparties_counterparty"

        self_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2],
        )

        ledger_id = "some_ledger"
        good_ids = ["G1"]
        nonce = "some_nonce"
        amount_by_currency_id = {"FET": 1}
        quantities_by_good_id = {"G1": 1}
        tx_id = Transaction.get_hash(
            ledger_id=ledger_id,
            sender_address=tac_participant_sender,
            counterparty_address=tac_participant_counterparty,
            good_ids=good_ids,
            sender_supplied_quantities=[1],
            counterparty_supplied_quantities=[0],
            sender_payable_amount=0,
            counterparty_payable_amount=1,
            nonce=nonce,
        )
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=self_dialogue,
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id=tx_id,
                ledger_id=ledger_id,
                sender_address=tac_participant_sender,
                counterparty_address=tac_participant_counterparty,
                amount_by_currency_id=amount_by_currency_id,
                fee_by_currency_id={"FET": 2},
                quantities_by_good_id=quantities_by_good_id,
                nonce=nonce,
                sender_signature="some_signature",
                counterparty_signature="some_other_signature",
            ),
        )
        tx = Transaction.from_message(incoming_message)

        mocked_holdings_summary = "some_holdings_summary"

        # operation
        with patch.object(
            type(self.game),
            "holdings_summary",
            new_callable=PropertyMock,
            return_value=mocked_holdings_summary,
        ):
            with patch.object(self.game, "is_transaction_valid", return_value=True):
                with patch.object(self.game, "settle_transaction"):
                    with patch.object(
                        self.tac_handler.context.logger, "log"
                    ) as mock_logger:
                        with pytest.raises(
                            ValueError, match="Error when retrieving dialogue."
                        ):
                            self.tac_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        # _on_transaction
        mock_logger.assert_any_call(logging.DEBUG, f"handling transaction: {tx}")

        # _handle_valid_transaction
        mock_logger.assert_any_call(
            logging.INFO, f"handling valid transaction: {tx_id[-10:]}"
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            to=tac_participant_sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            transaction_id=tx_id,
            amount_by_currency_id=amount_by_currency_id,
            quantities_by_good_id=quantities_by_good_id,
        )
        assert has_attributes, error_str

    def test_handle_valid_transaction_no_last_message(self):
        """Test the _handle_valid_transaction method of the tac handler where the recovered dialogue is empty."""
        # setup
        self.game._phase = Phase.GAME

        tac_participant_sender = COUNTERPARTY_AGENT_ADDRESS
        tac_participant_counterparty = "counterparties_counterparty"

        counterparty_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2], tac_participant_counterparty
        )
        self_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2],
        )
        counterparty_dialogue._incoming_messages = []
        counterparty_dialogue._outgoing_messages = []

        ledger_id = "some_ledger"
        good_ids = ["G1"]
        nonce = "some_nonce"
        amount_by_currency_id = {"FET": 1}
        quantities_by_good_id = {"G1": 1}
        tx_id = Transaction.get_hash(
            ledger_id=ledger_id,
            sender_address=tac_participant_sender,
            counterparty_address=tac_participant_counterparty,
            good_ids=good_ids,
            sender_supplied_quantities=[1],
            counterparty_supplied_quantities=[0],
            sender_payable_amount=0,
            counterparty_payable_amount=1,
            nonce=nonce,
        )
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=self_dialogue,
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id=tx_id,
                ledger_id=ledger_id,
                sender_address=tac_participant_sender,
                counterparty_address=tac_participant_counterparty,
                amount_by_currency_id=amount_by_currency_id,
                fee_by_currency_id={"FET": 2},
                quantities_by_good_id=quantities_by_good_id,
                nonce=nonce,
                sender_signature="some_signature",
                counterparty_signature="some_other_signature",
            ),
        )
        tx = Transaction.from_message(incoming_message)

        mocked_holdings_summary = "some_holdings_summary"

        # operation
        with patch.object(
            type(self.game),
            "holdings_summary",
            new_callable=PropertyMock,
            return_value=mocked_holdings_summary,
        ):
            with patch.object(self.game, "is_transaction_valid", return_value=True):
                with patch.object(self.game, "settle_transaction"):
                    with patch.object(
                        self.tac_handler.context.logger, "log"
                    ) as mock_logger:
                        with pytest.raises(
                            ValueError, match="Error when retrieving last message."
                        ):
                            self.tac_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        # _on_transaction
        mock_logger.assert_any_call(logging.DEBUG, f"handling transaction: {tx}")

        # _handle_valid_transaction
        mock_logger.assert_any_call(
            logging.INFO, f"handling valid transaction: {tx_id[-10:]}"
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            to=tac_participant_sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            transaction_id=tx_id,
            amount_by_currency_id=amount_by_currency_id,
            quantities_by_good_id=quantities_by_good_id,
        )
        assert has_attributes, error_str

    def test_on_transaction_invalid(self):
        """Test the _on_transaction method of the tac handler where the transaction is invalid."""
        # setup
        self.game._phase = Phase.GAME

        tac_participant_sender = COUNTERPARTY_AGENT_ADDRESS
        tac_participant_counterparty = "counterparties_counterparty"

        self_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_messages[:2],
        )

        ledger_id = "some_ledger"
        good_ids = ["G1"]
        nonce = "some_nonce"
        amount_by_currency_id = {"FET": 1}
        quantities_by_good_id = {"G1": 1}
        tx_id = Transaction.get_hash(
            ledger_id=ledger_id,
            sender_address=tac_participant_sender,
            counterparty_address=tac_participant_counterparty,
            good_ids=good_ids,
            sender_supplied_quantities=[1],
            counterparty_supplied_quantities=[0],
            sender_payable_amount=0,
            counterparty_payable_amount=1,
            nonce=nonce,
        )
        incoming_message = cast(
            TacMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=self_dialogue,
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id=tx_id,
                ledger_id=ledger_id,
                sender_address=tac_participant_sender,
                counterparty_address=tac_participant_counterparty,
                amount_by_currency_id=amount_by_currency_id,
                fee_by_currency_id={"FET": 2},
                quantities_by_good_id=quantities_by_good_id,
                nonce=nonce,
                sender_signature="some_signature",
                counterparty_signature="some_other_signature",
            ),
        )
        tx = Transaction.from_message(incoming_message)

        # operation
        with patch.object(self.game, "is_transaction_valid", return_value=False):
            with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
                self.tac_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        # _on_transaction
        mock_logger.assert_any_call(logging.DEBUG, f"handling transaction: {tx}")

        # _handle_invalid_transaction
        mock_logger.assert_any_call(
            logging.INFO,
            f"handling invalid transaction: {tx_id}, tac_msg={incoming_message}",
        )

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.TAC_ERROR,
            to=tac_participant_sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            error_code=TacMessage.ErrorCode.TRANSACTION_NOT_VALID,
            info={"transaction_id": tx_id},
        )
        assert has_attributes, error_str

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        tac_dialogue = self.prepare_skill_dialogue(
            dialogues=self.tac_dialogues, messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=tac_dialogue, performative=TacMessage.Performative.CANCELLED,
        )

        # operation
        with patch.object(self.tac_handler.context.logger, "log") as mock_logger:
            self.tac_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle tac message of performative={incoming_message.performative} in dialogue={tac_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.tac_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef
        )
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.service_registration_behaviour = cast(
            TacBehaviour, cls._skill.skill_context.behaviours.tac,
        )
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )

        cls.register_location_description = Description(
            {"location": Location(51.5194, 0.1270)},
            data_model=DataModel(
                "location_agent", [Attribute("location", Location, True)]
            ),
        )
        cls.list_of_messages_register_location = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_location_description},
                is_incoming=False,
            ),
        )

        cls.register_service_description = Description(
            {"key": "some_key", "value": "some_value"},
            data_model=DataModel(
                "set_service_key",
                [Attribute("key", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_service = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_service_description},
                is_incoming=False,
            ),
        )

        cls.register_genus_description = Description(
            {"piece": "genus", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_genus = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_genus_description},
                is_incoming=False,
            ),
        )

        cls.register_classification_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_classification = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_classification_description},
                is_incoming=False,
            ),
        )

        cls.register_invalid_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "some_different_name",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_invalid = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_invalid_description},
                is_incoming=False,
            ),
        )

        cls.unregister_description = Description(
            {"key": "seller_service"},
            data_model=DataModel("remove", [Attribute("key", str, True)]),
        )
        cls.list_of_messages_unregister = (
            DialogueMessage(
                OefSearchMessage.Performative.UNREGISTER_SERVICE,
                {"service_description": cls.unregister_description},
                is_incoming=False,
            ),
        )

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
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_success_i(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH location_agent data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.game.is_registered_agent is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_genus",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()
        assert self.game.is_registered_agent is False

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and genus value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_genus[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.game.is_registered_agent is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_classification",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()
        assert self.game.is_registered_agent is False

    def test_handle_success_iii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and classification value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_classification[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.game.is_registered_agent is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            "the agent, with its genus and classification, is successfully registered on the SOEF.",
        )
        assert self.game.is_registered_agent is True

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef successtargets unregister_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_invalid[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.game.is_registered_agent is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received soef SUCCESS message as a reply to the following unexpected message: {oef_dialogue.get_message_by_id(incoming_message.target)}",
        )
        assert self.game.is_registered_agent is False

    def test_handle_error_i(self):
        """Test the _handle_error method of the oef_search handler where the oef error targets register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )
        assert (
            self.service_registration_behaviour.failed_registration_msg
            == oef_dialogue.get_message_by_id(incoming_message.target)
        )

    def test_handle_error_ii(self):
        """Test the _handle_error method of the oef_search handler where the oef error does NOT target register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages_unregister[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )

        assert self.service_registration_behaviour.failed_registration_msg is None

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
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
