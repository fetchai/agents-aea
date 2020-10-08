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
"""This module contains the tests of the handler classes of the generic buyer skill."""

import logging
from pathlib import Path
from typing import cast
from unittest import mock

import pytest

from aea.helpers.search.models import Description
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
)
from aea.protocols.default.message import DefaultMessage
from aea.protocols.dialogue.base import DialogueMessage
from aea.protocols.signing.message import SigningMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_NAME

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.generic_buyer.handlers import (
    GenericFipaHandler,
    GenericLedgerApiHandler,
    GenericOefSearchHandler,
    GenericSigningHandler,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


class TestGenericFipaHandler(BaseSkillTestCase):
    """Test fipa handler of generic buyer."""

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
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
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
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
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
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
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
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
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
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
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
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
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
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
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

    def test_fipa_handler_handle_invalid(self, caplog):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with caplog.at_level(logging.INFO):
            self.fipa_handler.handle(incoming_message)
        assert (
            f"cannot handle fipa message of performative={incoming_message.performative} in dialogue={fipa_dialogue}."
            in caplog.text
        )


class TestGenericOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            GenericOefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )

    def test_oef_search_handler_handle_unidentified_dialogue(self, caplog):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        )
        caplog.set_level(logging.INFO)

        # operation
        self.oef_search_handler.handle(incoming_message)

        # after
        assert (
            f"received invalid oef_search message={incoming_message}, unidentified dialogue."
            in caplog.text
        )

    def test_oef_search_handler_handle_error(self, caplog):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )
        caplog.set_level(logging.INFO)

        # operation
        self.oef_search_handler.handle(incoming_message)

        # after
        assert (
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}."
            in caplog.text
        )

    def test_oef_search_handler_handle_search_zero_agents(self, caplog):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=tuple(),
            agents_info=OefSearchMessage.AgentsInfo({}),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.oef_search_handler.handle(incoming_message)

        # after
        assert (
            f"found no agents in dialogue={oef_dialogue}, continue searching."
            in caplog.text
        )

    def test_oef_search_handler_handle_search(self, caplog):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        self.strategy._max_negotiations = 3
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        agents = ("agnt1", "agnt2")
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo(
                {"agent_1": {"key_1": "value_1"}, "agent_2": {"key_2": "value_2"}}
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.oef_search_handler.handle(incoming_message)

        # after
        assert f"found agents={list(agents)}, stopping search." in caplog.text
        assert not self.strategy.is_searching
        quantity = self.get_quantity_in_outbox()
        assert quantity == len(
            agents
        ), f"Invalid number of messages in outbox. Expected {len(agents)}. Found {quantity}."
        for agent in agents:
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agent,
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            assert f"sending CFP to agent={agent}" in caplog.text

    def test_oef_search_handler_handle_invalid(self, caplog):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            service_description="some_service_description",
        )
        caplog.set_level(logging.INFO)

        # operation
        self.oef_search_handler.handle(incoming_message)

        # after
        assert (
            f"cannot handle oef_search message of performative={invalid_performative} in dialogue={self.oef_dialogues.get_dialogue(incoming_message)}."
            in caplog.text
        )


class TestGenericSigningHandler(BaseSkillTestCase):
    """Test signing handler of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            GenericSigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
            ),
        )
        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": cls.terms,
                    "raw_transaction": SigningMessage.RawTransaction(
                        "some_ledger_id", "some_body"
                    ),
                },
            ),
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.TRANSACTION_DIGEST, {}),
        )

    def test_signing_handler_handle_unidentified_dialogue(self, caplog):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=SigningMessage.Performative.ERROR,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
            to=str(self.skill.skill_context.skill_id),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.signing_handler.handle(incoming_message)

        # after
        assert (
            f"received invalid signing message={incoming_message}, unidentified dialogue."
            in caplog.text
        )

    def test_signing_handler_handle_signed_transaction_last_ledger_api_message_is_none(
        self, caplog
    ):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:4],
            ),
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        signing_dialogue.associated_fipa_dialogue.associated_ledger_api_dialogue._incoming_messages = (
            []
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=signing_dialogue,
            performative=SigningMessage.Performative.SIGNED_TRANSACTION,
            signed_transaction=SigningMessage.SignedTransaction(
                "some_ledger_id", "some_body"
            ),
        )

        # operation
        with pytest.raises(
            ValueError, match="Could not retrieve last message in ledger api dialogue"
        ):
            self.signing_handler.handle(incoming_message)

        # after
        assert "transaction signing was successful." in caplog.text

    def test_signing_handler_handle_signed_transaction_last_ledger_api_message_is_not_none(
        self, caplog
    ):
        """Test the _handle_signed_transaction method of the signing handler where the last ledger_api message is not None."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:4],
            ),
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SigningMessage.SignedTransaction(
                    "some_ledger_id", "some_body"
                ),
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.signing_handler.handle(incoming_message)

        # after
        assert "transaction signing was successful." in caplog.text
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected {1}. Found {quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str
        assert "sending transaction to ledger." in caplog.text

    def test_signing_handler_handle_error(self, caplog):
        """Test the _handle_error method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = self.prepare_skill_dialogue(
            dialogues=self.signing_dialogues,
            messages=self.list_of_signing_messages[:1],
            counterparty=signing_counterparty,
        )
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.signing_handler.handle(incoming_message)

        # after
        assert (
            f"transaction signing was not successful. Error_code={incoming_message.error_code} in dialogue={signing_dialogue}"
            in caplog.text
        )

    def test_signing_handler_handle_invalid(self, caplog):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = SigningMessage.Performative.SIGN_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            terms=self.terms,
            raw_transaction=SigningMessage.RawTransaction(
                "some_ledger_id", "some_body"
            ),
            to=str(self.skill.skill_context.skill_id),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.signing_handler.handle(incoming_message)

        # after
        assert (
            f"cannot handle signing message of performative={invalid_performative} in dialogue={self.signing_dialogues.get_dialogue(incoming_message)}."
            in caplog.text
        )


class TestGenericLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            GenericLedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
            ),
        )
        cls.raw_transaction = RawTransaction("some_ledger_id", "some_body")
        cls.signed_transaction = SignedTransaction("some_ledger_id", "some_body")
        cls.transaction_digest = TransactionDigest("some_ledger_id", "some_body")
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {"terms": cls.terms}
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                {"raw_transaction": cls.raw_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": cls.signed_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                {"transaction_digest": cls.transaction_digest},
            ),
        )

    def test_ledger_api_handler_handle_unidentified_dialogue(self, caplog):
        """Test the _handle_unidentified_dialogue method of the ledger_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue."
            in caplog.text
        )

    def test_ledger_api_handler_handle_balance_positive_balance(self, caplog):
        """Test the _handle_balance method of the ledger_api handler where balance is positive."""
        # setup
        balance = 10
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id="some-Ledger_id",
                balance=balance,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"starting balance on {self.strategy.ledger_id} ledger={incoming_message.balance}."
            in caplog.text
        )
        assert self.strategy.balance == balance
        assert self.strategy.is_searching

    def test_ledger_api_handler_handle_balance_zero_balance(self, caplog):
        """Test the _handle_balance method of the ledger_api handler where balance is zero."""
        # setup
        balance = 0
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id="some-Ledger_id",
                balance=balance,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"you have no starting balance on {self.strategy.ledger_id} ledger!"
            in caplog.text
        )
        assert not self.skill.skill_context.is_active

    def test_ledger_api_handler_handle_raw_transaction(self, caplog):
        """Test the _handle_raw_transaction method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:1],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:4],
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=self.raw_transaction,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert f"received raw transaction={incoming_message}" in caplog.text
        assert self.get_quantity_in_decision_maker_outbox() == 1
        assert (
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
            in caplog.text
        )

    def test_ledger_api_handler_handle_transaction_digest_last_fipa_message_is_none(
        self, caplog
    ):
        """Test the _handle_transaction_digest method of the ledger_api handler where the last incoming fipa message os None."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:3],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:4],
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        ledger_api_dialogue.associated_fipa_dialogue._incoming_messages = []
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=self.transaction_digest,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        with pytest.raises(ValueError, match="Could not retrieve fipa message"):
            self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"transaction was successfully submitted. Transaction digest={incoming_message.transaction_digest}"
            in caplog.text
        )

    def test_ledger_api_handler_handle_transaction_digest(self, caplog):
        """Test the _handle_transaction_digest method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:3],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:4],
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=self.transaction_digest,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"transaction was successfully submitted. Transaction digest={incoming_message.transaction_digest}"
            in caplog.text
        )
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected {1}. Found {quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=COUNTERPARTY_NAME,
            sender=self.skill.skill_context.agent_address,
            info={"transaction_digest": incoming_message.transaction_digest.body},
        )
        assert has_attributes, error_str
        assert (
            f"informing counterparty={COUNTERPARTY_NAME[-5:]} of transaction digest."
            in caplog.text
        )

    def test_ledger_api_handler_handle_error(self, caplog):
        """Test the _handle_error method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ledger_api_dialogues,
            messages=self.list_of_ledger_api_messages[:1],
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.ERROR,
                code=1,
            ),
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"received ledger_api error message={incoming_message} in dialogue={ledger_api_dialogue}"
            in caplog.text
        )

    def test_ledger_api_handler_handle_invalid(self, caplog):
        """Test the _handle_invalid method of the ledger_api handler."""
        # setup
        invalid_performative = LedgerApiMessage.Performative.GET_BALANCE
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id="some_ledger_id",
            address="some_address",
            to=self.skill.skill_context.agent_address,
        )
        caplog.set_level(logging.INFO)

        # operation
        self.ledger_api_handler.handle(incoming_message)

        # after
        assert (
            f"cannot handle ledger_api message of performative={invalid_performative} in dialogue={self.ledger_api_dialogues.get_dialogue(incoming_message)}."
            in caplog.text
        )
