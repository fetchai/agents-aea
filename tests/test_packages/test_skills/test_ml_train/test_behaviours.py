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
"""This module contains the tests of the behaviour classes of the ml_train skill."""

import logging
import uuid
from multiprocessing.pool import ApplyResult
from pathlib import Path
from typing import Tuple, cast
from unittest.mock import Mock, patch

import pytest

from aea.helpers.search.models import Description
from aea.protocols.dialogue.base import DialogueMessage
from aea.skills.tasks import TaskManager
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.skills.ml_train.behaviours import (
    GenericSearchBehaviour,
    LEDGER_API_ADDRESS,
    SearchBehaviour,
    TransactionBehaviour,
)
from packages.fetchai.skills.ml_train.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
)
from packages.fetchai.skills.ml_train.strategy import Strategy

from tests.conftest import ROOT_DIR


class TestSearchBehaviour(BaseSkillTestCase):
    """Test Search behaviour of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            SearchBehaviour, cls._skill.skill_context.behaviours.search
        )
        cls.tx_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.task_manager = cast(TaskManager, cls._skill.skill_context.task_manager)

        cls.logger = cls._skill.skill_context.logger

        cls._skill.skill_context.task_manager.start()

    def test_act_no_task(self):
        """Test the act method of the search behaviour where current_task_id is None."""
        # setup
        self.strategy._current_task_id = None

        # operation
        with patch.object(GenericSearchBehaviour, "act") as mock_generic_act:
            self.search_behaviour.act()

        # after
        mock_generic_act.assert_called_once()

    def test_act_task_not_ready(self):
        """Test the act method of the search behaviour where task isn't ready."""
        # setup
        self.strategy._current_task_id = 1

        mock_task_result = Mock(wraps=ApplyResult)
        mock_task_result.ready.return_value = False

        # operation
        with patch.object(
            self.task_manager, "get_task_result", return_value=mock_task_result
        ):
            self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.strategy._current_task_id == 1

    def test_act_task_not_successful(self):
        """Test the act method of the search behaviour where task isn't successful."""
        # setup
        self.strategy._current_task_id = 1

        mock_task_result = Mock(wraps=ApplyResult)
        mock_task_result.ready.return_value = True
        mock_task_result.successful.return_value = False

        # operation
        with patch.object(
            self.task_manager, "get_task_result", return_value=mock_task_result
        ):
            self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.strategy._current_task_id == 1

    def test_act_task_ready_and_successful(self):
        """Test the act method of the search behaviour where task is ready and successful."""
        # setup
        self.strategy._current_task_id = 1
        mocked_weights = "some_weights"

        mock_task_result = Mock(wraps=ApplyResult)
        mock_task_result.ready.return_value = True
        mock_task_result.successful.return_value = True
        mock_task_result.get.return_value = mocked_weights

        # operation
        with patch.object(
            self.task_manager, "get_task_result", return_value=mock_task_result
        ):
            with patch.object(GenericSearchBehaviour, "act") as mock_generic_act:
                self.search_behaviour.act()

        # after
        assert self.strategy._current_task_id is None
        assert self.strategy._weights == mocked_weights
        mock_generic_act.assert_called_once()

    def test_act_data_exists(self):
        """Test the act method of the search behaviour where no task is running and there is strategy.data is not empty."""
        # setup
        self.strategy._current_task_id = None

        mocked_data = ([], [])
        self.strategy.data = [mocked_data]

        mocked_task_id = 1

        # operation
        with patch.object(
            self.task_manager, "enqueue_task", return_value=mocked_task_id
        ) as mocked_enqueue_task:
            self.search_behaviour.act()

        # after
        assert self.strategy.data == []
        mocked_enqueue_task.assert_called_once()
        assert self.strategy._current_task_id == mocked_task_id

    @classmethod
    def teardown(cls):
        """Tears down the test class."""
        cls._skill.skill_context.task_manager.stop()


class TestTransactionBehaviour(BaseSkillTestCase):
    """Test transaction behaviour of ml_train buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.transaction_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

        cls.terms = Description(
            {
                "batch_size": cls.batch_size,
                "price": cls.price_per_data_batch,
                "seller_tx_fee": cls.seller_tx_fee,
                "buyer_tx_fee": cls.buyer_tx_fee,
                "currency_id": cls.currency_id,
                "ledger_id": cls.ledger_id,
                "address": cls._skill.skill_context.agent_address,
                "service_id": cls.service_id,
                "nonce": uuid.uuid4().hex,
            }
        )

        cls.list_of_messages = (
            DialogueMessage(MlTradeMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(MlTradeMessage.Performative.TERMS, {"terms": cls.terms}),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT,
                {"terms": cls.terms, "tx_digest": "some_tx_digest"},
            ),
        )

    @staticmethod
    def _check_start_processing_effects(self_, ml_dialogue, mock_logger) -> None:
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
            terms=ml_dialogue.terms,
        )
        assert has_attributes, error_str

        ledger_api_dialogue = cast(
            LedgerApiDialogue, self_.ledger_api_dialogues.get_dialogue(message)
        )
        assert ledger_api_dialogue.associated_ml_trade_dialogue == ml_dialogue

        assert self_.transaction_behaviour.processing_time == 0.0

        assert self_.transaction_behaviour.processing == ledger_api_dialogue

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting transfer transaction from ledger api for message={message}...",
        )

    @staticmethod
    def _setup_ml_ledger_api_dialogues(
        self_,
    ) -> Tuple[LedgerApiDialogue, MlTradeDialogue]:
        """Setup ml_trade and ledger_api dialogues for some of the following tests."""
        ml_dialogue = cast(
            MlTradeDialogue,
            self_.prepare_skill_dialogue(
                dialogues=self_.ml_dialogues, messages=self_.list_of_messages,
            ),
        )
        ml_dialogue.terms = self_.terms

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
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue

        return ledger_api_dialogue, ml_dialogue

    def test_setup(self):
        """Test the setup method of the transaction behaviour."""
        assert self.transaction_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the transaction behaviour where processing IS None and len(self.waiting) is NOT 0."""
        # setup
        _, ml_dialogue = self._setup_ml_ledger_api_dialogues(self)

        processing_time = 5.0
        max_processing = 120
        self.transaction_behaviour.processing = None
        self.transaction_behaviour.max_processing = max_processing
        self.transaction_behaviour.processing_time = processing_time
        self.transaction_behaviour.waiting = [ml_dialogue]

        # before
        assert self.transaction_behaviour.processing_time == processing_time
        assert self.transaction_behaviour.processing is None

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _start_processing
        self._check_start_processing_effects(self, ml_dialogue, mock_logger)

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
        ledger_api_dialogue, ml_dialogue = self._setup_ml_ledger_api_dialogues(self)

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
        # assert ml_dialogue in self.transaction_behaviour.waiting
        assert self.transaction_behaviour.processing_time == 0.0
        # below is overridden in _start_processing
        # assert self.transaction_behaviour.processing is None

        # _start_processing
        self._check_start_processing_effects(self, ml_dialogue, mock_logger)

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
        ledger_api_dialogue, ml_dialogue = self._setup_ml_ledger_api_dialogues(self)

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
        assert ml_dialogue in self.transaction_behaviour.waiting

    def test_finish_processing_i(self):
        """Test the finish_processing method of the transaction behaviour where self.processing == ledger_api_dialogue."""
        # setup
        ledger_api_dialogue, ml_dialogue = self._setup_ml_ledger_api_dialogues(self)
        self.transaction_behaviour.processing = ledger_api_dialogue

        # operation
        self.transaction_behaviour.failed_processing(ledger_api_dialogue)

        # after
        assert self.transaction_behaviour.processing_time == 0.0
        assert self.transaction_behaviour.processing is None

    def test_finish_processing_ii(self):
        """Test the finish_processing method of the transaction behaviour where ledger_api_dialogue's dialogue_label is NOT in self.timedout."""
        # setup
        ledger_api_dialogue, ml_dialogue = self._setup_ml_ledger_api_dialogues(self)

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
