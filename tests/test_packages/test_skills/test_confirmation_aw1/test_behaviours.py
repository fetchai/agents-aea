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
"""This module contains the tests of the behaviour classes of the confirmation aw1 skill."""

import logging
from pathlib import Path
from typing import Tuple, cast
from unittest.mock import patch

import pytest

from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.skills.confirmation_aw1.behaviours import (
    LEDGER_API_ADDRESS,
    TransactionBehaviour,
)
from packages.fetchai.skills.confirmation_aw1.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
    RegisterDialogue,
    RegisterDialogues,
)
from packages.fetchai.skills.confirmation_aw1.strategy import Strategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestTransactionBehaviour(BaseSkillTestCase):
    """Test transaction behaviour of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.transaction_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.register_dialogues = cast(
            RegisterDialogues, cls._skill.skill_context.register_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.list_of_registration_messages = (
            DialogueMessage(
                RegisterMessage.Performative.REGISTER,
                {"info": {"some_key": "some_value"}},
            ),
        )

    @staticmethod
    def _check_start_processing_effects(self_, register_dialogue, mock_logger) -> None:
        """Perform checks related to running _start_processing."""
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
            sender=str(self_.skill.skill_context.skill_id),
            terms=register_dialogue.terms,
        )
        assert has_attributes, error_str

        ledger_api_dialogue = cast(
            LedgerApiDialogue, self_.ledger_api_dialogues.get_dialogue(message)
        )
        assert ledger_api_dialogue.associated_register_dialogue == register_dialogue

        assert self_.transaction_behaviour.processing_time == 0.0

        assert self_.transaction_behaviour.processing == ledger_api_dialogue

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting transfer transaction from ledger api for message={message}...",
        )

    @staticmethod
    def _setup_register_ledger_api_dialogues(
        self_,
    ) -> Tuple[LedgerApiDialogue, RegisterDialogue]:
        """Setup register and ledger_api dialogues for some of the following tests."""
        register_dialogue = cast(
            RegisterDialogue,
            self_.prepare_skill_dialogue(
                dialogues=self_.register_dialogues,
                messages=self_.list_of_registration_messages,
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue.terms = Terms(
            ledger_id="some_ledger_id",
            sender_address="some_sender_address",
            counterparty_address="some_counterparty",
            amount_by_currency_id={"1": -10},
            quantities_by_good_id={},
            is_sender_payable_tx_fee=True,
            nonce="some_none",
            fee_by_currency_id={"1": 100},
        )

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
        ledger_api_dialogue.associated_register_dialogue = register_dialogue

        return ledger_api_dialogue, register_dialogue

    def test_setup(self):
        """Test the setup method of the transaction behaviour."""
        assert self.transaction_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the transaction behaviour where processing IS None and len(self.waiting) is NOT 0."""
        # setup
        _, register_dialogue = self._setup_register_ledger_api_dialogues(self)

        processing_time = 5.0
        max_processing = 120
        self.transaction_behaviour.processing = None
        self.transaction_behaviour.max_processing = max_processing
        self.transaction_behaviour.processing_time = processing_time
        self.transaction_behaviour.waiting = [register_dialogue]

        # before
        assert self.transaction_behaviour.processing_time == processing_time
        assert self.transaction_behaviour.processing is None

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _start_processing
        self._check_start_processing_effects(self, register_dialogue, mock_logger)

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
        (
            ledger_api_dialogue,
            register_dialogue,
        ) = self._setup_register_ledger_api_dialogues(self)

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
        # assert register_dialogue in self.transaction_behaviour.waiting
        assert self.transaction_behaviour.processing_time == 0.0
        # below is overridden in _start_processing
        # assert self.transaction_behaviour.processing is None

        # _start_processing
        self._check_start_processing_effects(self, register_dialogue, mock_logger)

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
        (
            ledger_api_dialogue,
            register_dialogue,
        ) = self._setup_register_ledger_api_dialogues(self)

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
        assert register_dialogue in self.transaction_behaviour.waiting

    def test_finish_processing_i(self):
        """Test the finish_processing method of the transaction behaviour where self.processing == ledger_api_dialogue."""
        # setup
        (
            ledger_api_dialogue,
            register_dialogue,
        ) = self._setup_register_ledger_api_dialogues(self)
        self.transaction_behaviour.processing = ledger_api_dialogue

        # operation
        self.transaction_behaviour.failed_processing(ledger_api_dialogue)

        # after
        assert self.transaction_behaviour.processing_time == 0.0
        assert self.transaction_behaviour.processing is None

    def test_finish_processing_ii(self):
        """Test the finish_processing method of the transaction behaviour where ledger_api_dialogue's dialogue_label is NOT in self.timedout."""
        # setup
        (
            ledger_api_dialogue,
            register_dialogue,
        ) = self._setup_register_ledger_api_dialogues(self)

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
