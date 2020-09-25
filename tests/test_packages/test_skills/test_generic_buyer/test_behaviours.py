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
"""This module contains test case classes based on pytest for AEA end-to-end testing."""

from pathlib import Path
from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.protocols.default.message import DefaultMessage
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_PUBLIC_ID
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.behaviours import GenericSearchBehaviour
from packages.fetchai.skills.generic_buyer.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.skills.generic_buyer.handlers import GenericFipaHandler
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    def test_search_behaviour_setup_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is True."""
        # setup
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )
        expected_performative = LedgerApiMessage.Performative.GET_BALANCE
        expected_counterparty = str(LEDGER_PUBLIC_ID)
        expected_ledger_id = FETCHAI
        expected_address = self.skill.skill_context.agent_address

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        search_behaviour.setup()

        # after
        assert self.get_quantity_in_outbox() == 1
        actual_message = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert type(actual_message) == LedgerApiMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.ledger_id == expected_ledger_id
        assert actual_message.address == expected_address

    def test_search_behaviour_setup_not_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is False."""
        # setup
        strategy = cast(GenericStrategy, self.skill.skill_context.strategy)
        strategy._is_ledger_tx = False
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )

        # before
        assert not strategy.is_searching

        # operation
        search_behaviour.setup()

        # after
        assert strategy.is_searching

    def test_search_behaviour_act_is_searching(self):
        """Test the act method of the search behaviour where is_searching is True."""
        # setup
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )
        strategy = cast(GenericStrategy, self.skill.skill_context.strategy)
        strategy._is_searching = True
        expected_performative = OefSearchMessage.Performative.SEARCH_SERVICES
        expected_counterparty = "dummy_search_service_address"
        expected_query = (
            self.skill.skill_context.strategy.get_location_and_service_query()
        )

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        search_behaviour.act()

        # after
        assert self.get_quantity_in_outbox() == 1
        actual_message = cast(LedgerApiMessage, self.get_message_from_outbox())
        assert type(actual_message) == OefSearchMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.query == expected_query

    def test_search_behaviour_act_not_is_searching(self):
        """Test the act method of the search behaviour where is_searching is False."""
        # setup
        strategy = cast(GenericStrategy, self.skill.skill_context.strategy)
        strategy._is_searching = False
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        search_behaviour.act()

        # after
        assert self.get_quantity_in_outbox() == 0


class TestSkillHandler(BaseSkillTestCase):
    """Test handlers of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    def test_fipa_handler_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        fipa_handler = cast(GenericFipaHandler, self.skill.skill_context.handlers.fipa)

        incoming_message = FipaMessage(
            dialogue_reference=("1", "0"),
            message_id=1,
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        incoming_message.sender = "counterparty"
        incoming_message.to = "me"

        expected_performative = DefaultMessage.Performative.ERROR
        expected_counterparty = incoming_message.sender
        expected_error_code = DefaultMessage.ErrorCode.INVALID_DIALOGUE
        expected_error_msg = "Invalid dialogue."
        expected_error_data = {"fipa_message": incoming_message.encode()}

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        fipa_handler._handle_unidentified_dialogue(incoming_message)

        # after
        assert self.get_quantity_in_outbox() == 1
        actual_message = cast(DefaultMessage, self.get_message_from_outbox())
        assert type(actual_message) == DefaultMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.error_code == expected_error_code
        assert actual_message.error_msg == expected_error_msg
        assert actual_message.error_data == expected_error_data

    def test_fipa_handler_handle_propose(self):
        """Test the _handle_propose method of the fipa handler."""
        # ToDo need to mock affordable and acceptable values
        # setup
        fipa_handler = cast(GenericFipaHandler, self.skill.skill_context.handlers.fipa)

        proposal = Description(
            {
                "ledger_id": "some_ledger_id",
                "price": "some_price",
                "currency_id": "some_currency_id",
                "service_id": "some_service_id",
                "quantity": "some_quantity",
                "tx_nonce": "some_tx_nonce",
            }
        )

        incoming_message = FipaMessage(
            dialogue_reference=("1", "0"),
            message_id=2,
            target=1,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )
        incoming_message.sender = "counterparty"
        incoming_message.to = "me"

        expected_performative = FipaMessage.Performative.ACCEPT
        expected_counterparty = incoming_message.sender
        expected_target = 1

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        fipa_handler._handle_propose(
            incoming_message,
            FipaDialogue(
                DialogueLabel(("1", "1"), "counterparty", "me"),
                "me",
                FipaDialogue.Role.BUYER,
            ),
        )

        # after
        assert self.get_quantity_in_outbox() == 1
        actual_message = cast(FipaMessage, self.get_message_from_outbox())
        assert type(actual_message) == FipaMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.target == expected_target

    def test_fipa_handler_handle_decline_decline_cfp(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_cfp."""
        # setup
        fipa_handler = cast(GenericFipaHandler, self.skill.skill_context.handlers.fipa)

        incoming_message = FipaMessage(
            dialogue_reference=("1", "1"),
            message_id=2,
            target=1,
            performative=FipaMessage.Performative.DECLINE,
        )
        incoming_message.sender = "counterparty"
        incoming_message.to = "me"
        fipa_dialogue = FipaDialogue(
            DialogueLabel(("1", "1"), "counterparty", "me"),
            "me",
            FipaDialogue.Role.BUYER,
        )
        fipa_dialogues = self.skill.skill_context.fipa_dialogues

        # before
        for end_state_numbers in fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for end_state_numbers in fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        fipa_handler._handle_decline(incoming_message, fipa_dialogue, fipa_dialogues)

        # after
        for end_state_numbers in fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_CFP:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_decline_decline_accept(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_accept."""
        # setup
        fipa_handler = cast(GenericFipaHandler, self.skill.skill_context.handlers.fipa)

        incoming_message = FipaMessage(
            dialogue_reference=("1", "1"),
            message_id=4,
            target=3,
            performative=FipaMessage.Performative.DECLINE,
        )
        incoming_message.sender = "counterparty"
        incoming_message.to = "me"
        fipa_dialogue = FipaDialogue(
            DialogueLabel(("1", "1"), "counterparty", "me"),
            "me",
            FipaDialogue.Role.BUYER,
        )
        fipa_dialogues = self.skill.skill_context.fipa_dialogues

        # before
        for end_state_numbers in fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for end_state_numbers in fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        fipa_handler._handle_decline(incoming_message, fipa_dialogue, fipa_dialogues)

        # after
        for end_state_numbers in fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_ACCEPT:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_match_accept(self):
        """Test the _handle_match_accept method of the fipa handler."""
        # ToDo does not work; fails on dialogues.update(). Investigate why.
        # setup
        fipa_handler = cast(GenericFipaHandler, self.skill.skill_context.handlers.fipa)
        strategy = cast(GenericStrategy, self.skill.skill_context.strategy)
        strategy._is_ledger_tx = False

        info = {"address": "some_term_sender_address"}
        counterparty_address = "counterparty"
        my_address = self.skill.skill_context.agent_address
        incoming_message = FipaMessage(
            dialogue_reference=("1", "1"),
            message_id=2,
            target=1,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info=info,
        )
        incoming_message.sender = my_address
        incoming_message.to = my_address

        fipa_dialogues = cast(FipaDialogues, self.skill.skill_context.fipa_dialogues)
        _, fipa_dialogue = fipa_dialogues.create(
            counterparty=my_address,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("foo", ConstraintType("==", "bar"))], model=None),
        )
        proposal_msg = FipaMessage(
            dialogue_reference=(
                fipa_dialogue.dialogue_label.dialogue_starter_reference,
                FipaDialogues._generate_dialogue_nonce(),
            ),
            message_id=2,
            target=1,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description(
                {
                    "ledger_id": "some_ledger_id",
                    "price": "some_price",
                    "currency_id": "some_currency_id",
                    "service_id": "some_service_id",
                    "quantity": "some_quantity",
                    "tx_nonce": "some_tx_nonce",
                }
            ),
        )
        proposal_msg.sender = counterparty_address
        proposal_msg.to = my_address
        fipa_dialogue = fipa_dialogues.update(proposal_msg)
        assert fipa_dialogue is not None
        fipa_dialogue.reply(
            performative=FipaMessage.Performative.ACCEPT, target_message=proposal_msg,
        )

        expected_performative = FipaMessage.Performative.INFORM
        expected_counterparty = incoming_message.sender
        expected_target = incoming_message.message_id
        expected_info = {"Done": "Sending payment via bank transfer"}

        # before
        assert self.get_quantity_in_outbox() == 0

        # operation
        fipa_handler._handle_match_accept(
            incoming_message, cast(FipaDialogue, fipa_dialogue)
        )

        # after
        assert self.get_quantity_in_outbox() == 1
        actual_message = cast(FipaMessage, self.get_message_from_outbox())
        assert type(actual_message) == FipaMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.target == expected_target
        assert actual_message.info == expected_info
