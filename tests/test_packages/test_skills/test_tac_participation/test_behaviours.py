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
"""This module contains the tests of the behaviour classes of the tac participation skill."""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.behaviours import (
    TacSearchBehaviour,
    TransactionProcessBehaviour,
)
from packages.fetchai.skills.tac_participation.dialogues import TacDialogues
from packages.fetchai.skills.tac_participation.game import Game, Phase

from tests.conftest import ROOT_DIR


class TestTacSearchBehaviour(BaseSkillTestCase):
    """Test tac behaviour of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")
    is_agent_to_agent_messages = True

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_search_behaviour = cast(
            TacSearchBehaviour, cls._skill.skill_context.behaviours.tac_search
        )
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.logger = cls.tac_search_behaviour.context.logger

    def test_setup(self):
        """Test the setup method of the tac_search behaviour."""
        assert self.tac_search_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the tac_search behaviour where phase is not PRE_GAME."""
        # setup
        self.game._phase = Phase.GAME

        # operation
        with patch.object(self.logger, "log"):
            self.tac_search_behaviour.act()

        # after
        assert self.game.phase == Phase.GAME
        self.assert_quantity_in_outbox(0)

    def test_act_ii(self):
        """Test the act method of the tac_search behaviour where phase is PRE_GAME."""
        # setup
        self.game._phase = Phase.PRE_GAME
        mocked_query = "some_query"

        # operation
        with patch.object(self.game, "get_game_query", return_value=mocked_query):
            with patch.object(self.logger, "log") as mock_logger:
                self.tac_search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _search_for_tac
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            query=mocked_query,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, f"searching for TAC, search_id={message.dialogue_reference}"
        )

    def test_teardown(self):
        """Test the teardown method of the tac_search behaviour."""
        assert self.tac_search_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestTransactionProcessBehaviour(BaseSkillTestCase):
    """Test tac behaviour of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.transaction_process_behaviour = cast(
            TransactionProcessBehaviour,
            cls._skill.skill_context.behaviours.transaction_processing,
        )
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.logger = cls.transaction_process_behaviour.context.logger

        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)

        cls.list_of_tac_messages = (
            DialogueMessage(
                TacMessage.Performative.REGISTER, {"agent_name": "some_agent_name"}
            ),
            DialogueMessage(
                TacMessage.Performative.GAME_DATA,
                {
                    "amount_by_currency_id": {"FET": 1},
                    "exchange_params_by_currency_id": {"FET": 1.0},
                    "quantities_by_good_id": {"2": 10},
                    "utility_params_by_good_id": {"2": 1.0},
                    "fee_by_currency_id": {"1": 1},
                    "agent_addr_to_name": {
                        COUNTERPARTY_AGENT_ADDRESS: "some_agent_name"
                    },
                    "currency_id_to_name": {"1": "FETCH"},
                    "good_id_to_name": {"2": "Good_1"},
                    "version_id": "v1",
                },
            ),
        )

        cls.tx_ids = ["tx_1", "tx_2"]
        cls.terms_1 = Terms(
            "some_ledger_id",
            "some_sender_address_1",
            "some_counterparty_address_1",
            {"1": 10},
            {"2": 5},
            "some_nonce_1",
            fee_by_currency_id={"1": 1},
        )
        cls.terms_2 = Terms(
            "some_ledger_id",
            "some_sender_address_2",
            "some_counterparty_address_2",
            {"1": 11},
            {"2": 6},
            "some_nonce_2",
            fee_by_currency_id={"1": 2},
        )
        cls.terms = [cls.terms_1, cls.terms_2]
        cls.sender_signatures = ["sender_signature_1", "sender_signature_2"]
        cls.counterparty_signatures = [
            "counterparty_signature_1",
            "counterparty_signature_2",
        ]

        cls.txs = OrderedDict(
            {
                cls.tx_ids[0]: {
                    "terms": cls.terms[0],
                    "sender_signature": cls.sender_signatures[0],
                    "counterparty_signature": cls.counterparty_signatures[0],
                },
                cls.tx_ids[1]: {
                    "terms": cls.terms[1],
                    "sender_signature": cls.sender_signatures[1],
                    "counterparty_signature": cls.counterparty_signatures[1],
                },
            }
        )

    def test_setup(self):
        """Test the setup method of the transaction_process behaviour."""
        assert self.transaction_process_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the transaction_process behaviour where phase is not GAME."""
        # setup
        self.game._phase = Phase.PRE_GAME

        # operation
        with patch.object(self.logger, "log"):
            self.transaction_process_behaviour.act()

        # after
        assert self.game.phase == Phase.PRE_GAME
        self.assert_quantity_in_outbox(0)

    def test_act_ii(self):
        """Test the act method of the transaction_process behaviour where phase is GAME."""
        # setup
        self.game._phase = Phase.GAME
        no_tx = len(self.txs)
        self.skill.skill_context._agent_context._shared_state = {
            "transactions": self.txs
        }
        tac_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_tac_messages,
        )
        self.game._tac_dialogue = tac_dialogue

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.transaction_process_behaviour.act()

        # after
        self.assert_quantity_in_outbox(no_tx)

        # _process_transactions
        count = 0
        while count != no_tx:
            message = self.get_message_from_outbox()
            mock_logger.assert_any_call(
                logging.INFO,
                f"sending transaction {self.tx_ids[count]} to controller, message={message}.",
            )
            has_attributes, error_str = self.message_has_attributes(
                actual_message=message,
                message_type=TacMessage,
                performative=TacMessage.Performative.TRANSACTION,
                to=COUNTERPARTY_AGENT_ADDRESS,
                sender=self.skill.skill_context.agent_address,
                transaction_id=self.tx_ids[count],
                ledger_id=self.terms[count].ledger_id,
                sender_address=self.terms[count].sender_address,
                counterparty_address=self.terms[count].counterparty_address,
                amount_by_currency_id=self.terms[count].amount_by_currency_id,
                fee_by_currency_id=self.terms[count].fee_by_currency_id,
                quantities_by_good_id=self.terms[count].quantities_by_good_id,
                sender_signature=self.sender_signatures[count],
                counterparty_signature=self.counterparty_signatures[count],
                nonce=self.terms[count].nonce,
            )
            assert has_attributes, error_str
            count += 1

    def test_process_transactions_tac_dialogue_is_empty(self):
        """Test the _process_transactions method of the transaction_process behaviour where last message of tac_dialogue is None."""
        # setup
        self.game._phase = Phase.GAME
        self.skill.skill_context._agent_context._shared_state = {
            "transactions": self.txs
        }

        tac_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_tac_messages,
        )

        tac_dialogue._incoming_messages = []
        tac_dialogue._outgoing_messages = []

        self.game._tac_dialogue = tac_dialogue

        # operation
        with pytest.raises(ValueError, match="No last message available."):
            self.transaction_process_behaviour.act()

    def test_process_transactions_invalid_tx(self):
        """Test the _process_transactions method of the transaction_process behaviour where transactions are None."""
        # setup
        self.game._phase = Phase.GAME
        self.skill.skill_context._agent_context._shared_state = {
            "transactions": {self.tx_ids[0]: None, self.tx_ids[1]: None}
        }

        tac_dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues, self.list_of_tac_messages,
        )
        self.game._tac_dialogue = tac_dialogue

        # operation
        with pytest.raises(ValueError, match=f"Tx for id={self.tx_ids[0]} not found."):
            self.transaction_process_behaviour.act()

    def test_teardown(self):
        """Test the teardown method of the transaction_process behaviour."""
        assert self.transaction_process_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
