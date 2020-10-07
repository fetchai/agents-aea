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
"""This module contains the tests of the behaviour classes of the generic buyer skill."""

import logging
from pathlib import Path
from typing import cast
from unittest import mock

from aea.helpers.search.models import Description
from aea.helpers.transaction.base import Terms
from aea.protocols.default.message import DefaultMessage
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_NAME

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_PUBLIC_ID
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.behaviours import GenericSearchBehaviour
from packages.fetchai.skills.generic_buyer.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.skills.generic_buyer.handlers import (
    GenericFipaHandler,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            GenericSearchBehaviour, cls._skill.skill_context.behaviours.search
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)

    def test_search_behaviour_setup_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is True."""
        # operation
        self.search_behaviour.setup()

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=str(LEDGER_PUBLIC_ID),
            sender=self.skill.skill_context.agent_address,
            ledger_id=FETCHAI,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

    def test_search_behaviour_setup_not_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False

        # before
        assert not self.strategy.is_searching

        # operation
        self.search_behaviour.setup()

        # after
        assert self.strategy.is_searching

    def test_search_behaviour_act_is_searching(self):
        """Test the act method of the search behaviour where is_searching is True."""
        # setup
        self.strategy._is_searching = True

        # operation
        self.search_behaviour.act()

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            query=self.skill.skill_context.strategy.get_location_and_service_query(),
        )
        assert has_attributes, error_str

    def test_search_behaviour_act_not_is_searching(self):
        """Test the act method of the search behaviour where is_searching is False."""
        # setup
        self.strategy._is_searching = False

        # operation
        self.search_behaviour.act()

        # after
        assert self.get_quantity_in_outbox() == 0


class TestSkillHandler(BaseSkillTestCase):
    """Test handlers of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.fipa_handler = cast(
            GenericFipaHandler, cls._skill.skill_context.handlers.fipa
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
        )

    def test_fipa_handler_handle_unidentified_dialogue(self, caplog):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert (
            f"received invalid fipa message={incoming_message}, unidentified dialogue."
            in caplog.text
        )

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_propose(self, caplog):
        """Test the _handle_propose method of the fipa handler."""
        # setup
        proposal = Description(
            {
                "ledger_id": self.strategy.ledger_id,
                "price": 100,
                "currency_id": "FET",
                "service_id": "some_service_id",
                "quantity": 1,
                "tx_nonce": "some_tx_nonce",
            }
        )
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )

        # operation
        with mock.patch.object(
            self.strategy, "is_acceptable_proposal", return_value=True,
        ):
            with mock.patch.object(
                self.strategy, "is_affordable_proposal", return_value=True,
            ):
                with caplog.at_level(logging.INFO):
                    self.fipa_handler.handle(incoming_message)
        assert (
            f"received proposal={incoming_message.proposal.values} from sender={COUNTERPARTY_NAME[-5:]}"
            in caplog.text
        )
        assert (
            f"accepting the proposal from sender={COUNTERPARTY_NAME[-5:]}"
            in caplog.text
        )

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.ACCEPT,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_decline_decline_cfp(self, caplog):
        """Test the _handle_decline method of the fipa handler where the end state is decline_cfp."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert f"received DECLINE from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        # after
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_CFP:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_decline_decline_accept(self, caplog):
        """Test the _handle_decline method of the fipa handler where the end state is decline_accept."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert f"received DECLINE from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        # after
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_ACCEPT:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_match_accept_is_ledger_tx(self, caplog):
        """Test the _handle_match_accept method of the fipa handler where is_ledger_tx is True."""
        # setup
        self.strategy._is_ledger_tx = True

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:3],
        )
        fipa_dialogue.terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"info": {"address": "some_term_sender_address"}},
        )

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert (
            f"received MATCH_ACCEPT_W_INFORM from sender={COUNTERPARTY_NAME[-5:]} with info={incoming_message.info}"
            in caplog.text
        )
        assert "requesting transfer transaction from ledger api..." in caplog.text

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            terms=fipa_dialogue.terms,
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_match_accept_not_is_ledger_tx(self, caplog):
        """Test the _handle_match_accept method of the fipa handler where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"info": {"address": "some_term_sender_address"}},
        )

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert (
            f"received MATCH_ACCEPT_W_INFORM from sender={COUNTERPARTY_NAME[-5:]} with info={incoming_message.info}"
            in caplog.text
        )
        assert (
            f"informing counterparty={COUNTERPARTY_NAME[-5:]} of payment."
            in caplog.text
        )

        # after
        assert self.get_quantity_in_outbox() == 1, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            info={"Done": "Sending payment via bank transfer"},
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_inform_with_data(self, caplog):
        """Test the _handle_inform method of the fipa handler where info has data."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages,
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={"data_name": "data"},
        )

        # before
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert "received the following data={'data_name': 'data'}" in caplog.text

        # after
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.SUCCESSFUL:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_inform_without_data(self, caplog):
        """Test the _handle_inform method of the fipa handler where info has NO data."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages,
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={},
        )

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert f"received no data from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
