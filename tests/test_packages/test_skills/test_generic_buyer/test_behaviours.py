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
from typing import Tuple, cast
from unittest.mock import patch

import pytest

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_PUBLIC_ID
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.behaviours import (
    GenericSearchBehaviour,
    GenericTransactionBehaviour,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestSearchBehaviour(BaseSkillTestCase):
    """Test Search behaviour of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            GenericSearchBehaviour, cls._skill.skill_context.behaviours.search
        )
        cls.tx_behaviour = cast(
            GenericTransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)

        cls.logger = cls._skill.skill_context.logger

    def test_setup_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is True."""
        # operation
        self.search_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=str(LEDGER_PUBLIC_ID),
            sender=str(self.skill.public_id),
            ledger_id=FETCHAI,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

    def test_setup_not_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False

        # before
        assert not self.strategy.is_searching

        # operation
        self.search_behaviour.setup()

        # after
        assert self.strategy.is_searching

    def test_act_is_searching(self):
        """Test the act method of the search behaviour where is_searching is True."""
        # setup
        self.strategy._is_searching = True

        # operation
        self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.public_id),
            query=self.skill.skill_context.strategy.get_location_and_service_query(),
        )
        assert has_attributes, error_str

    def test_act_not_is_searching(self):
        """Test the act method of the search behaviour where is_searching is False."""
        # setup
        self.strategy._is_searching = False

        # operation
        self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_remaining_transactions(self):
        """Test the act method of the search behaviour where remaining_transactions_count > 0."""
        # setup
        self.strategy._is_searching = True
        self.tx_behaviour.waiting = ["some_dialogue"]

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        mock_logger.assert_any_call(
            logging.INFO,
            f"Transaction behaviour has {len(self.tx_behaviour.waiting)} transactions remaining. Skipping search!",
        )

    def test_teardown(self):
        """Test the teardown method of the search behaviour."""
        assert self.search_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestTransactionBehaviour(BaseSkillTestCase):
    """Test transaction behaviour of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.transaction_behaviour = cast(
            GenericTransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
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

    @staticmethod
    def _check_start_processing_effects(self_, fipa_dialogue, mock_logger) -> None:
        """Perform checks related to running _start_processing."""
        # _start_processing
        mock_logger.assert_any_call(
            logging.INFO,
            f"Processing transaction, {len(self_.transaction_behaviour.waiting)} transactions remaining",
        )

        message = self_.get_message_from_outbox()
        has_attributes, error_str = self_.message_has_attributes(
            actual_message=message,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self_.skill.public_id),
            terms=fipa_dialogue.terms,
        )
        assert has_attributes, error_str

        ledger_api_dialogue = cast(
            LedgerApiDialogue, self_.ledger_api_dialogues.get_dialogue(message)
        )
        assert ledger_api_dialogue.associated_fipa_dialogue == fipa_dialogue

        assert self_.transaction_behaviour.processing_time == 0.0

        assert self_.transaction_behaviour.processing == ledger_api_dialogue

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting transfer transaction from ledger api for message={message}...",
        )

    @staticmethod
    def _setup_fipa_ledger_api_dialogues(
        self_,
    ) -> Tuple[LedgerApiDialogue, FipaDialogue]:
        """Setup fipa and ledger_api dialogues for some of the following tests."""
        fipa_dialogue = cast(
            FipaDialogue,
            self_.prepare_skill_dialogue(
                dialogues=self_.fipa_dialogues, messages=self_.list_of_messages,
            ),
        )
        fipa_dialogue.terms = "terms"  # type: ignore

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self_.prepare_skill_dialogue(
                dialogues=self_.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        return ledger_api_dialogue, fipa_dialogue

    def test_setup(self):
        """Test the setup method of the transaction behaviour."""
        assert self.transaction_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the transaction behaviour where processing IS None and len(self.waiting) is NOT 0."""
        # setup
        _, fipa_dialogue = self._setup_fipa_ledger_api_dialogues(self)

        processing_time = 5.0
        max_processing = 120
        self.transaction_behaviour.processing = None
        self.transaction_behaviour.max_processing = max_processing
        self.transaction_behaviour.processing_time = processing_time
        self.transaction_behaviour.waiting = [fipa_dialogue]

        # before
        assert self.transaction_behaviour.processing_time == processing_time
        assert self.transaction_behaviour.processing is None

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _start_processing
        self._check_start_processing_effects(self, fipa_dialogue, mock_logger)

    def test_act_ii(self):
        """Test the act method of the transaction behaviour where processing is NOT None and processing_time < max_processing."""
        # setup
        processing_time = 5.0
        self.transaction_behaviour.processing = "some_dialogue"
        self.transaction_behaviour.max_processing = 120
        self.transaction_behaviour.processing_time = processing_time

        # operation
        self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert (
            self.transaction_behaviour.processing_time
            == processing_time + self.transaction_behaviour.tick_interval
        )

    def test_act_iii(self):
        """Test the act method of the transaction behaviour where processing is NOT None and processing_time > max_processing."""
        # setup
        ledger_api_dialogue, fipa_dialogue = self._setup_fipa_ledger_api_dialogues(self)

        processing_time = 121.0
        self.transaction_behaviour.processing = ledger_api_dialogue
        self.transaction_behaviour.max_processing = 120
        self.transaction_behaviour.processing_time = processing_time

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _timeout_processing
        assert ledger_api_dialogue.dialogue_label in self.transaction_behaviour.timedout
        # below is overridden in _start_processing
        # assert fipa_dialogue in self.transaction_behaviour.waiting
        assert self.transaction_behaviour.processing_time == 0.0
        # below is overridden in _start_processing
        # assert self.transaction_behaviour.processing is None

        # _start_processing
        self._check_start_processing_effects(self, fipa_dialogue, mock_logger)

    def test_timeout_processing(self):
        """Test the _timeout_processing method of the transaction behaviour where self.processing IS None."""
        # setup
        self.transaction_behaviour.processing_time = None

        # operation
        self.transaction_behaviour._timeout_processing()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_iv(self):
        """Test the act method of the transaction behaviour where len(waiting) == 0."""
        # setup
        self.transaction_behaviour.processing = None
        self.transaction_behaviour.waiting = []

        # operation
        self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_failed_processing(self):
        """Test the failed_processing method of the transaction behaviour."""
        # setup
        ledger_api_dialogue, fipa_dialogue = self._setup_fipa_ledger_api_dialogues(self)

        self.transaction_behaviour.timedout.add(ledger_api_dialogue.dialogue_label)

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_behaviour.failed_processing(ledger_api_dialogue)

        # after
        self.assert_quantity_in_outbox(0)

        # finish_processing
        assert self.transaction_behaviour.timedout == set()

        mock_logger.assert_any_call(
            logging.DEBUG,
            f"Timeout dialogue in transaction processing: {ledger_api_dialogue}",
        )

        # failed_processing
        assert fipa_dialogue in self.transaction_behaviour.waiting

    def test_finish_processing_i(self):
        """Test the finish_processing method of the transaction behaviour where self.processing == ledger_api_dialogue."""
        # setup
        ledger_api_dialogue, fipa_dialogue = self._setup_fipa_ledger_api_dialogues(self)
        self.transaction_behaviour.processing = ledger_api_dialogue

        # operation
        self.transaction_behaviour.failed_processing(ledger_api_dialogue)

        # after
        assert self.transaction_behaviour.processing_time == 0.0
        assert self.transaction_behaviour.processing is None

    def test_finish_processing_ii(self):
        """Test the finish_processing method of the transaction behaviour where ledger_api_dialogue's dialogue_label is NOT in self.timedout."""
        # setup
        ledger_api_dialogue, fipa_dialogue = self._setup_fipa_ledger_api_dialogues(self)

        # operation
        with pytest.raises(ValueError) as err:
            self.transaction_behaviour.finish_processing(ledger_api_dialogue)

        # after
        assert (
            err.value.args[0]
            == f"Non-matching dialogues in transaction behaviour: {self.transaction_behaviour.processing} and {ledger_api_dialogue}"
        )

    def test_teardown(self):
        """Test the teardown method of the transaction behaviour."""
        assert self.transaction_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
