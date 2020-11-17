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
"""This module contains the tests of the Transactions class of the tac negotiation skill."""

import datetime
from pathlib import Path

import pytest

from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_ADDRESS

from packages.fetchai.skills.tac_negotiation.dialogues import FipaDialogue
from packages.fetchai.skills.tac_negotiation.transactions import Transactions

from tests.conftest import ROOT_DIR


class TestTransactions(BaseSkillTestCase):
    """Test Transactions class of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.pending_transaction_timeout = 30
        cls.transactions = Transactions(
            pending_transaction_timeout=cls.pending_transaction_timeout,
            name="transactions",
            skill_context=cls._skill.skill_context,
        )

        cls.nonce = "125"
        cls.sender = "some_sender_address"
        cls.counterparty = "some_counterparty_address"
        cls.ledger_id = "some_ledger_id"
        cls.terms = Terms(
            ledger_id=cls.ledger_id,
            sender_address=cls.sender,
            counterparty_address=cls.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=True,
            nonce=cls.nonce,
            fee_by_currency_id={"1": 1},
        )
        cls.dialogue_label = DialogueLabel(
            ("", ""), COUNTERPARTY_ADDRESS, cls._skill.skill_context.agent_address,
        )
        cls.proposal_id = 5

    def test_simple_properties(self):
        """Test the properties of Transactions class."""
        assert self.transactions.pending_proposals == {}
        assert self.transactions.pending_initial_acceptances == {}

    def test_get_next_nonce(self):
        """Test the get_next_nonce method of the Transactions class."""
        assert self.transactions.get_next_nonce() == 1

    def test_update_confirmed_transactions(self):
        """Test the update_confirmed_transactions method of the Transactions class."""
        self.transactions.update_confirmed_transactions()
        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

    def test_cleanup_pending_transactions(self):
        """Test the cleanup_pending_transactions method of the Transactions class."""
        self.transactions.cleanup_pending_transactions()
        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

    def test_add_pending_proposal(self):
        """Test the add_pending_proposal method of the Transactions class."""
        self.transactions.add_pending_proposal(
            self.dialogue_label, self.proposal_id, self.terms
        )
        assert (
            self.transactions._pending_proposals[self.dialogue_label][self.proposal_id]
            == self.terms
        )

    def test_pop_pending_proposal(self):
        """Test the pop_pending_proposal method of the Transactions class."""
        actual_terms = self.transactions.pop_pending_proposal(
            self.dialogue_label, self.proposal_id
        )
        assert actual_terms == self.terms
        assert (
            self.proposal_id
            not in self.transactions._pending_proposals[self.dialogue_label]
        )

    def test_add_pending_initial_acceptance(self):
        """Test the add_pending_initial_acceptance method of the Transactions class."""
        self.transactions.add_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id, self.terms,
        )
        assert (
            self.transactions._pending_initial_acceptances[self.dialogue_label][
                self.proposal_id
            ]
            == self.terms
        )

    def test_pop_pending_initial_acceptance(self):
        """Test the pop_pending_initial_acceptance method of the Transactions class."""
        actual_terms = self.transactions.pop_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id
        )
        assert actual_terms == self.terms
        assert (
            self.proposal_id
            not in self.transactions._pending_proposals[self.dialogue_label]
        )

    def test_register_transaction_with_time(self):
        """Test the _register_transaction_with_time method of the Transactions class."""
        transaction_id = "5"
        self.transactions._register_transaction_with_time(transaction_id)
        assert (
            datetime.datetime.now(),
            transaction_id,
        ) in self.transactions._last_update_for_transactions

    def test_add_locked_tx_seller(self):
        """Test the add_locked_tx method of the Transactions class as Seller."""
        self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.SELLER)
        assert (
            datetime.datetime.now(),
            self.terms.id,
        ) in self.transactions._last_update_for_transactions
        assert self.transactions._locked_txs[self.terms.id] == self.terms
        assert self.transactions._locked_txs_as_seller[self.terms.id] == self.terms
        assert self.terms.id not in self.transactions._locked_txs_as_buyer

    def test_add_locked_tx_buyer(self):
        """Test the add_locked_tx method of the Transactions class as Seller."""
        self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.BUYER)
        assert (
            datetime.datetime.now(),
            self.terms.id,
        ) in self.transactions._last_update_for_transactions
        assert self.transactions._locked_txs[self.terms.id] == self.terms
        assert self.transactions._locked_txs_as_buyer[self.terms.id] == self.terms
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_pop_locked_tx(self):
        """Test the pop_locked_tx method of the Transactions class."""
        actual_terms = self.transactions.pop_locked_tx(self.terms)
        assert actual_terms == self.terms
        assert self.terms.id not in self.transactions._locked_txs
        assert self.terms.id not in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_ownership_state_after_locks(self):
        """Test the ownership_state_after_locks method of the Transactions class."""
        # ToDo incomplete
        pytest.skip("incomplete")
        is_seller = True
        actual_ownership_state = self.transactions.ownership_state_after_locks(
            is_seller
        )
        assert actual_ownership_state
