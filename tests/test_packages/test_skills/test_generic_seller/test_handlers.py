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
"""This module contains the tests of the handler classes of the generic seller skill."""

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
from aea.protocols.dialogue.base import DialogueMessage, Dialogues
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_NAME

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.handlers import (
    GenericFipaHandler,
    GenericLedgerApiHandler,
    GenericOefSearchHandler,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


class TestGenericFipaHandler(BaseSkillTestCase):
    """Test fipa handler of generic seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_seller")

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
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}, True),
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
        self.fipa_handler.handle(incoming_message)

        # after
        assert (
            f"received invalid fipa message={incoming_message}, unidentified dialogue."
            in caplog.text
        )
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

    def test_fipa_handler_handle_cfp_is_matching_supply(self, caplog):
        """Test the _handle_cfp method of the fipa handler where is_matching_supply is True."""
        # setup
        proposal = Description(
            {
                "ledger_id": "some_ledger_id",
                "price": 100,
                "currency_id": "FET",
                "service_id": "some_service_id",
                "quantity": 1,
                "tx_nonce": "some_tx_nonce",
            }
        )
        terms = "some_terms"
        data = {"data_type": "data"}

        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            query="some_query",
        )

        # operation
        with mock.patch.object(
            self.strategy, "is_matching_supply", return_value=True,
        ):
            with mock.patch.object(
                self.strategy, "generate_proposal_terms_and_data", return_value=(proposal, terms, data),
            ):
                self.fipa_handler.handle(incoming_message)

        # after
        assert f"received CFP from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
        assert f"sending a PROPOSE with proposal={proposal.values} to sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        quantity = self.get_quantity_in_outbox()
        assert quantity == 1, f"Invalid number of messages in outbox. Expected 1. Found {quantity}."

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.PROPOSE,
            to=COUNTERPARTY_NAME,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            proposal=proposal,
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_cfp_not_is_matching_supply(self, caplog):
        """Test the _handle_cfp method of the fipa handler where is_matching_supply is False."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            query="some_query",
        )

        # operation
        with mock.patch.object(self.strategy, "is_matching_supply", return_value=False):
            self.fipa_handler.handle(incoming_message)

        # after
        assert f"declined the CFP from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=COUNTERPARTY_NAME,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_decline(self, caplog):
        """Test the _handle_decline method of the fipa handler."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        for end_state_numbers in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for end_state_numbers in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert f"received DECLINE from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        for end_state_numbers in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_PROPOSE:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_fipa_handler_handle_accept(self, caplog):
        """Test the _handle_accept method of the fipa handler."""
        # setup
        fipa_dialogue = cast(FipaDialogue, self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
        ))
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
            performative=FipaMessage.Performative.ACCEPT,
        )
        info = {"address": fipa_dialogue.terms.sender_address}

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert f"received ACCEPT from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            to=COUNTERPARTY_NAME,
            sender=self.skill.skill_context.agent_address,
            info=info,
        )
        assert has_attributes, error_str
        assert f"sending MATCH_ACCEPT_W_INFORM to sender={COUNTERPARTY_NAME[-5:]} with info={info}" in caplog.text

    def test_fipa_handler_handle_inform_is_ledger_tx_and_with_tx_digest(self, caplog):
        """Test the _handle_inform method of the fipa handler where is_ledger_tx is True and info contains transaction_digest."""
        # setup
        self.strategy._is_ledger_tx = True
        tx_digest = "some_transaction_digest_body"
        ledger_id = "some_ledger_id"

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
        )
        fipa_dialogue.terms = Terms(
            ledger_id,
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={"transaction_digest": tx_digest},
        )

        # operation
        self.fipa_handler.handle(incoming_message)
        incoming_message = cast(FipaMessage, incoming_message)

        # after
        assert f"received INFORM from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
        assert f"checking whether transaction={incoming_message.info['transaction_digest']} has been received ..." in caplog.text

        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            to=LEDGER_API_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=0,
            transaction_digest=TransactionDigest(ledger_id, tx_digest),
        )
        assert has_attributes, error_str

    def test_fipa_handler_handle_inform_is_ledger_tx_and_no_tx_digest(self, caplog):
        """Test the _handle_inform method of the fipa handler where is_ledger_tx is True and info does not have a transaction_digest."""
        # setup
        self.strategy._is_ledger_tx = True

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
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
            performative=FipaMessage.Performative.INFORM,
            info={},
        )

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert f"received INFORM from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
        assert f"did not receive transaction digest from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

    def test_fipa_handler_handle_inform_not_is_ledger_tx_and_with_done(self, caplog):
        """Test the _handle_inform method of the fipa handler where is_ledger_tx is False and info contains done."""
        # setup
        self.strategy._is_ledger_tx = False
        data = {
            "data_type_1": "data_1",
            "data_type_2": "data_2",
        }

        fipa_dialogue = cast(FipaDialogue, self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
        ))
        fipa_dialogue.data_for_sale = data
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={"Done": "Sending payment via bank transfer"},
        )

        # before
        for end_state_numbers in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for end_state_numbers in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert f"received INFORM from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

        # check outgoing message
        quantity = self.get_quantity_in_outbox()
        assert (
            quantity == 1
        ), f"Invalid number of messages in outbox. Expected 1. Found {quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=COUNTERPARTY_NAME,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            info=fipa_dialogue.data_for_sale,
        )
        assert has_attributes, error_str

        # check updated end_state
        for end_state_numbers in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.items():
            if end_state == FipaDialogue.EndState.SUCCESSFUL:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

        # check logger output
        assert f"transaction confirmed, sending data={data} to buyer={COUNTERPARTY_NAME[-5:]}" in caplog.text

    def test_fipa_handler_handle_inform_not_is_ledger_tx_and_nothin_in_info(self, caplog):
        """Test the _handle_inform method of the fipa handler where is_ledger_tx is False and info does not contain done or transaction_digest."""
        # setup
        self.strategy._is_ledger_tx = False

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={},
        )

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert f"received INFORM from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text
        assert f"did not receive transaction confirmation from sender={COUNTERPARTY_NAME[-5:]}" in caplog.text

    def test_fipa_handler_handle_invalid(self, caplog):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={},
        )

        # operation
        self.fipa_handler.handle(incoming_message)

        # after
        assert (
            f"cannot handle fipa message of performative={incoming_message.performative} in dialogue={fipa_dialogue}."
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
        assert self.get_quantity_in_decision_maker_inbox() == 1
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
