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
from unittest.mock import patch

import pytest

import aea
from aea.helpers.search.models import Attribute, DataModel, Description, Location
from aea.helpers.transaction.base import Terms, TransactionDigest, TransactionReceipt
from aea.protocols.dialogue.base import DialogueMessage, Dialogues
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.behaviours import (
    GenericServiceRegistrationBehaviour,
)
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
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": "some_query"}, True
            ),
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

    def test_setup(self):
        """Test the setup method of the fipa handler."""
        assert self.fipa_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid fipa message={incoming_message}, unidentified dialogue.",
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
            error_data={"fipa_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_cfp_is_matching_supply(self):
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
        with patch.object(
            self.strategy, "is_matching_supply", return_value=True,
        ):
            with patch.object(
                self.strategy,
                "generate_proposal_terms_and_data",
                return_value=(proposal, terms, data),
            ):
                with patch.object(
                    self.fipa_handler.context.logger, "log"
                ) as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received CFP from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}"
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"sending a PROPOSE with proposal={proposal.values} to sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.PROPOSE,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            proposal=proposal,
        )
        assert has_attributes, error_str

    def test_handle_cfp_not_is_matching_supply(self):
        """Test the _handle_cfp method of the fipa handler where is_matching_supply is False."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            query="some_query",
        )

        # operation
        with patch.object(self.strategy, "is_matching_supply", return_value=False):
            with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received CFP from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}"
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"declined the CFP from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

    def test_handle_decline(self):
        """Test the _handle_decline method of the fipa handler."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received DECLINE from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_PROPOSE:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_handle_accept(self):
        """Test the _handle_accept method of the fipa handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_messages[:2],
            ),
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
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )
        info = {"address": fipa_dialogue.terms.sender_address}

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ACCEPT from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"sending MATCH_ACCEPT_W_INFORM to sender={COUNTERPARTY_AGENT_ADDRESS[-5:]} with info={info}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            info=info,
        )
        assert has_attributes, error_str

    def test_handle_inform_is_ledger_tx_and_with_tx_digest(self):
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)
        incoming_message = cast(FipaMessage, incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"checking whether transaction={incoming_message.info['transaction_digest']} has been received ...",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            target=0,
            transaction_digest=TransactionDigest(ledger_id, tx_digest),
        )
        assert has_attributes, error_str

    def test_handle_inform_is_ledger_tx_and_no_tx_digest(self):
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"did not receive transaction digest from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )

    def test_handle_inform_not_is_ledger_tx_and_with_done(self):
        """Test the _handle_inform method of the fipa handler where is_ledger_tx is False and info contains done."""
        # setup
        self.strategy._is_ledger_tx = False
        data = {
            "data_type_1": "data_1",
            "data_type_2": "data_2",
        }

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_messages[:4],
            ),
        )
        fipa_dialogue.data_for_sale = data
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={"Done": "Sending payment via bank transfer"},
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        # check outgoing message
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            info=fipa_dialogue.data_for_sale,
        )
        assert has_attributes, error_str

        # check updated end_state
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
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
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction confirmed, sending data={data} to buyer={COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )

    def test_handle_inform_not_is_ledger_tx_and_nothin_in_info(self):
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"did not receive transaction confirmation from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )

    def test_handle_invalid(self):
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
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle fipa message of performative={incoming_message.performative} in dialogue={fipa_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.fipa_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestGenericLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of generic seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_seller")
    is_agent_to_agent_messages = False

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
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": "some_query"}, True
            ),
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
        cls.transaction_digest = TransactionDigest("some_ledger_id", "some_body")
        cls.transaction_receipt = TransactionReceipt(
            "some_ledger_id", {"some_key": "some_value"}, {"some_key": "some_value"}
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": cls.transaction_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": cls.transaction_receipt},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
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

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_balance(self):
        """Test the _handle_balance method of the ledger_api handler."""
        # setup
        ledger_id = "some_Ledger_id"
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
                ledger_id=ledger_id,
                balance=10,
            ),
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"starting balance on {ledger_id} ledger={incoming_message.balance}.",
        )

    def test_handle_transaction_receipt_is_settled_and_is_valid_last_incoming_fipa_message_is_none(
        self,
    ):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_settled and is_valid are True and the last incoming FipaMessage is None."""
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
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:5],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        fipa_dialogue.data_for_sale = {"data_type_1": "data_1"}
        fipa_dialogue._incoming_messages = []
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            aea.crypto.ledger_apis.LedgerApis,
            "is_transaction_settled",
            return_value=True,
        ):
            with patch.object(
                aea.crypto.ledger_apis.LedgerApis,
                "is_transaction_valid",
                return_value=True,
            ):
                with pytest.raises(
                    ValueError, match="Cannot retrieve last fipa message."
                ):
                    self.ledger_api_handler.handle(incoming_message)

    def test_handle_transaction_receipt_is_settled_and_is_valid(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_settled and is_valid are True."""
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
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:5],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        fipa_dialogue.data_for_sale = {"data_type_1": "data_1"}
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # before
        for end_state_numbers in list(
            self.fipa_dialogues.dialogue_stats.self_initiated.values()
        ) + list(self.fipa_dialogues.dialogue_stats.other_initiated.values()):
            assert end_state_numbers == 0

        # operation
        with patch.object(
            aea.crypto.ledger_apis.LedgerApis,
            "is_transaction_settled",
            return_value=True,
        ):
            with patch.object(
                aea.crypto.ledger_apis.LedgerApis,
                "is_transaction_valid",
                return_value=True,
            ):
                with patch.object(
                    self.ledger_api_handler.context.logger, "log"
                ) as mock_logger:
                    self.ledger_api_handler.handle(incoming_message)

        # after

        # check outgoing message
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=fipa_dialogue.last_incoming_message.message_id,
            info=fipa_dialogue.data_for_sale,
        )
        assert has_attributes, error_str

        # check updated end_state
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
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
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction confirmed, sending data={fipa_dialogue.data_for_sale} to buyer={COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )

    def test_handle_transaction_receipt_not_is_settled_or_not_is_valid(self,):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_settled or is_valid is False."""
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
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:5],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            aea.crypto.ledger_apis.LedgerApis,
            "is_transaction_settled",
            return_value=True,
        ):
            with patch.object(
                aea.crypto.ledger_apis.LedgerApis,
                "is_transaction_valid",
                return_value=False,
            ):
                with patch.object(
                    self.ledger_api_handler.context.logger, "log"
                ) as mock_logger:
                    self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction_receipt={self.transaction_receipt} not settled or not valid, aborting",
        )

    def test_handle_error(self):
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

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ledger_api error message={incoming_message} in dialogue={ledger_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the ledger_api handler."""
        # setup
        invalid_performative = LedgerApiMessage.Performative.GET_BALANCE
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id="some_ledger_id",
            address="some_address",
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ledger_api message of performative={invalid_performative} in dialogue={self.ledger_api_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestGenericOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of generic seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_seller")
    is_agent_to_agent_messages = False

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
        cls.service_registration_behaviour = cast(
            GenericServiceRegistrationBehaviour,
            cls._skill.skill_context.behaviours.service_registration,
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
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
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

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_service",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH set_service_key data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_service[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

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

    def test_handle_success_iii(self):
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

    def test_handle_success_iv(self):
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
            "the agent, with its genus and classification, and its service are successfully registered on the SOEF.",
        )

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets unregister_service."""
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
        """Test the _handle_invalid method of the oef_search handler."""
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
