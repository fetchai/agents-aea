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
import logging
from pathlib import Path
from typing import Deque, Tuple, cast
from unittest.mock import Mock, patch

import pytest

from aea.decision_maker.gop import GoalPursuitReadiness, OwnershipState, Preferences
from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.skills.tac_negotiation.dialogues import FipaDialogue
from packages.fetchai.skills.tac_negotiation.transactions import Transactions

from tests.conftest import ROOT_DIR


class TestTransactions(BaseSkillTestCase):
    """Test Transactions class of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        tac_dm_context_kwargs = {
            "goal_pursuit_readiness": GoalPursuitReadiness(),
            "ownership_state": OwnershipState(),
            "preferences": Preferences(),
        }
        super().setup(dm_context_kwargs=tac_dm_context_kwargs)
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
            ("", ""),
            COUNTERPARTY_AGENT_ADDRESS,
            cls._skill.skill_context.agent_address,
        )
        cls.proposal_id = 5
        cls.transaction_id = "some_transaction_id"

    def test_simple_properties(self):
        """Test the properties of Transactions class."""
        assert self.transactions.pending_proposals == {}
        assert self.transactions.pending_initial_acceptances == {}

    def test_get_next_nonce(self):
        """Test the get_next_nonce method of the Transactions class."""
        assert self.transactions.get_next_nonce() == "1"
        assert self.transactions._nonce == 1

    def test_update_confirmed_transactions(self):
        """Test the update_confirmed_transactions method of the Transactions class."""
        # setup
        self.skill.skill_context._get_agent_context().shared_state[
            "confirmed_tx_ids"
        ] = [self.transaction_id]
        self.transactions._locked_txs[self.transaction_id] = self.terms
        self.transactions._locked_txs_as_buyer[self.transaction_id] = self.terms
        self.transactions._locked_txs_as_seller[self.transaction_id] = self.terms

        # operation
        self.transactions.update_confirmed_transactions()

        # after
        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

    def test_cleanup_pending_transactions_i(self):
        """Test the cleanup_pending_transactions method of the Transactions class where _last_update_for_transactions is NOT empty."""
        # setup
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        with patch("datetime.datetime", new=datetime_mock):
            self.transactions._register_transaction_with_time(self.transaction_id)

        self.transactions._locked_txs[self.transaction_id] = self.terms
        self.transactions._locked_txs_as_buyer[self.transaction_id] = self.terms
        self.transactions._locked_txs_as_seller[self.transaction_id] = self.terms

        # operation
        with patch.object(self.skill.skill_context.logger, "log") as mock_logger:
            self.transactions.cleanup_pending_transactions()

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"removing transaction from pending list: {self.transaction_id}",
        )
        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

    def test_cleanup_pending_transactions_ii(self):
        """Test the cleanup_pending_transactions method of the Transactions class where _last_update_for_transactions is empty."""
        # setup
        cast(
            Deque[Tuple[datetime.datetime, str]],
            self.transactions._last_update_for_transactions,
        )

        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

        # operation
        self.transactions.cleanup_pending_transactions()

        # after
        assert self.transactions._locked_txs == {}
        assert self.transactions._locked_txs_as_buyer == {}
        assert self.transactions._locked_txs_as_seller == {}

    def test_add_pending_proposal_i(self):
        """Test the add_pending_proposal method of the Transactions class."""
        # before
        assert self.dialogue_label not in self.transactions._pending_proposals

        # operation
        self.transactions.add_pending_proposal(
            self.dialogue_label, self.proposal_id, self.terms
        )

        # after
        assert (
            self.transactions._pending_proposals[self.dialogue_label][self.proposal_id]
            == self.terms
        )

    def test_add_pending_proposal_ii(self):
        """Test the add_pending_proposal method of the Transactions class where dialogue_label IS in _pending_proposals."""
        # setup
        self.transactions._pending_proposals[self.dialogue_label] = {1: self.terms}

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Proposal is already in the list of pending proposals.",
        ):
            self.transactions.add_pending_proposal(
                self.dialogue_label, self.proposal_id, self.terms
            )

    def test_add_pending_proposal_iii(self):
        """Test the add_pending_proposal method of the Transactions class where proposal_id IS in _pending_proposals."""
        # setup
        self.transactions._pending_proposals[self.dialogue_label][
            self.proposal_id
        ] = self.terms

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Proposal is already in the list of pending proposals.",
        ):
            self.transactions.add_pending_proposal(
                self.dialogue_label, self.proposal_id, self.terms
            )

    def test_pop_pending_proposal_i(self):
        """Test the pop_pending_proposal method of the Transactions class."""
        # setup
        self.transactions.add_pending_proposal(
            self.dialogue_label, self.proposal_id, self.terms
        )

        # operation
        actual_terms = self.transactions.pop_pending_proposal(
            self.dialogue_label, self.proposal_id
        )

        # after
        assert actual_terms == self.terms
        assert (
            self.proposal_id
            not in self.transactions._pending_proposals[self.dialogue_label]
        )

    def test_pop_pending_proposal_ii(self):
        """Test the pop_pending_proposal method of the Transactions class where dialogue_label IS in _pending_proposals."""
        # setup
        self.transactions.add_pending_proposal(
            self.dialogue_label, self.proposal_id, self.terms
        )
        self.transactions._pending_proposals = {}

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Cannot find the proposal in the list of pending proposals.",
        ):
            assert self.transactions.pop_pending_proposal(
                self.dialogue_label, self.proposal_id
            )

    def test_pop_pending_proposal_iii(self):
        """Test the pop_pending_proposal method of the Transactions class where dialogue_label and proposal_id IS in _pending_proposals."""
        # setup
        self.transactions.add_pending_proposal(
            self.dialogue_label, self.proposal_id, self.terms
        )
        self.transactions._pending_proposals[self.dialogue_label] = {1: self.terms}

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Cannot find the proposal in the list of pending proposals.",
        ):
            assert self.transactions.pop_pending_proposal(
                self.dialogue_label, self.proposal_id
            )

    def test_add_pending_initial_acceptance_i(self):
        """Test the add_pending_initial_acceptance method of the Transactions class."""
        # before
        assert self.transactions._pending_initial_acceptances == {}

        # operation
        self.transactions.add_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id, self.terms,
        )

        # after
        assert (
            self.transactions._pending_initial_acceptances[self.dialogue_label][
                self.proposal_id
            ]
            == self.terms
        )

    def test_add_pending_initial_acceptance_ii(self):
        """Test the add_pending_initial_acceptance method of the Transactions class where dialogue_label IS in _pending_initial_acceptances."""
        # setup
        self.transactions._pending_initial_acceptances[self.dialogue_label] = {
            1: self.terms
        }

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Initial acceptance is already in the list of pending initial acceptances.",
        ):
            self.transactions.add_pending_initial_acceptance(
                self.dialogue_label, self.proposal_id, self.terms,
            )

    def test_add_pending_initial_acceptance_iii(self):
        """Test the add_pending_initial_acceptance method of the Transactions class where dialogue_label and proposal_id IS in _pending_initial_acceptances."""
        # setup
        self.transactions._pending_initial_acceptances[self.dialogue_label] = {
            self.proposal_id: self.terms
        }

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Initial acceptance is already in the list of pending initial acceptances.",
        ):
            self.transactions.add_pending_initial_acceptance(
                self.dialogue_label, self.proposal_id, self.terms,
            )

    def test_pop_pending_initial_acceptance_i(self):
        """Test the pop_pending_initial_acceptance method of the Transactions class."""
        # setup
        self.transactions.add_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id, self.terms,
        )

        # operation
        actual_terms = self.transactions.pop_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id
        )

        # after
        assert actual_terms == self.terms
        assert (
            self.proposal_id
            not in self.transactions._pending_proposals[self.dialogue_label]
        )

    def test_pop_pending_initial_acceptance_ii(self):
        """Test the pop_pending_initial_acceptance method of the Transactions class where dialogue_label IS in _pending_initial_acceptances."""
        # setup
        self.transactions.add_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id, self.terms,
        )
        self.transactions._pending_initial_acceptances = {}

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Cannot find the initial acceptance in the list of pending initial acceptances.",
        ):
            assert self.transactions.pop_pending_initial_acceptance(
                self.dialogue_label, self.proposal_id
            )

    def test_pop_pending_initial_acceptance_iii(self):
        """Test the pop_pending_initial_acceptance method of the Transactions class where dialogue_label and proposal_id IS in _pending_initial_acceptances."""
        # setup
        self.transactions.add_pending_initial_acceptance(
            self.dialogue_label, self.proposal_id, self.terms,
        )
        self.transactions._pending_initial_acceptances[self.dialogue_label] = {
            1: self.terms
        }

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Cannot find the initial acceptance in the list of pending initial acceptances.",
        ):
            assert self.transactions.pop_pending_initial_acceptance(
                self.dialogue_label, self.proposal_id
            )

    def test_register_transaction_with_time(self):
        """Test the _register_transaction_with_time method of the Transactions class."""
        # setup
        datetime_mock = Mock(wraps=datetime.datetime)
        mocked_now = datetime.datetime.strptime("01 01 2020  00:03", "%d %m %Y %H:%M")
        datetime_mock.now.return_value = mocked_now

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            self.transactions._register_transaction_with_time(self.transaction_id)

        # after
        assert (mocked_now, self.transaction_id,)[
            1
        ] == self.transactions._last_update_for_transactions[0][1]

    def test_add_locked_tx_seller(self):
        """Test the add_locked_tx method of the Transactions class as Seller."""
        # setup
        datetime_mock = Mock(wraps=datetime.datetime)
        mocked_now = datetime.datetime.strptime("01 01 2020  00:03", "%d %m %Y %H:%M")
        datetime_mock.now.return_value = mocked_now

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.SELLER)

        # after
        assert (mocked_now, self.terms.id,)[
            1
        ] == self.transactions._last_update_for_transactions[0][1]
        assert self.transactions._locked_txs[self.terms.id] == self.terms
        assert self.transactions._locked_txs_as_seller[self.terms.id] == self.terms
        assert self.terms.id not in self.transactions._locked_txs_as_buyer

    def test_add_locked_tx_buyer(self):
        """Test the add_locked_tx method of the Transactions class as Seller."""
        # setup
        datetime_mock = Mock(wraps=datetime.datetime)
        mocked_now = datetime.datetime.strptime("01 01 2020  00:03", "%d %m %Y %H:%M")
        datetime_mock.now.return_value = mocked_now

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.BUYER)

        # after
        assert (mocked_now, self.terms.id,)[
            1
        ] == self.transactions._last_update_for_transactions[0][1]
        assert self.transactions._locked_txs[self.terms.id] == self.terms
        assert self.transactions._locked_txs_as_buyer[self.terms.id] == self.terms
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_add_locked_tx_fails(self):
        """Test the add_locked_tx method of the Transactions class where transaction_id IS in _locked_txs."""
        # setup
        self.transactions._locked_txs[self.terms.id] = self.terms

        datetime_mock = Mock(wraps=datetime.datetime)
        mocked_now = datetime.datetime.strptime("01 01 2020  00:03", "%d %m %Y %H:%M")
        datetime_mock.now.return_value = mocked_now

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with pytest.raises(
                AEAEnforceError,
                match="This transaction is already a locked transaction.",
            ):
                self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.BUYER)

        # after
        assert (
            mocked_now,
            self.terms.id,
        ) not in self.transactions._last_update_for_transactions
        assert self.terms.id not in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_pop_locked_tx(self):
        """Test the pop_locked_tx method of the Transactions class."""
        # setup
        self.transactions.add_locked_tx(self.terms, FipaDialogue.Role.BUYER)

        # before
        assert self.terms.id in self.transactions._locked_txs
        assert self.terms.id in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

        # operation
        actual_terms = self.transactions.pop_locked_tx(self.terms)

        # after
        assert actual_terms == self.terms

        assert self.terms.id not in self.transactions._locked_txs
        assert self.terms.id not in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_pop_locked_tx_fails(self):
        """Test the pop_locked_tx method of the Transactions class where terms.id is NOT in _locked_txs."""
        # before
        assert self.terms.id not in self.transactions._locked_txs
        assert self.terms.id not in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

        # operation
        with pytest.raises(
            AEAEnforceError,
            match="Cannot find this transaction in the list of locked transactions.",
        ):
            self.transactions.pop_locked_tx(self.terms)

        # after
        assert self.terms.id not in self.transactions._locked_txs
        assert self.terms.id not in self.transactions._locked_txs_as_buyer
        assert self.terms.id not in self.transactions._locked_txs_as_seller

    def test_ownership_state_after_locks(self):
        """Test the ownership_state_after_locks method of the Transactions class."""
        # setup
        is_seller = True
        self.transactions._locked_txs_as_seller[self.transaction_id] = self.terms
        expected_apply_transactions_argument = [self.terms]
        expected_ownership_state = OwnershipState()

        # operation
        with patch.object(
            self.skill.skill_context.decision_maker_handler_context.ownership_state,
            "apply_transactions",
            return_value=expected_ownership_state,
        ) as mock_apply_transactions:
            actual_ownership_states = self.transactions.ownership_state_after_locks(
                is_seller
            )

        # after
        mock_apply_transactions.assert_any_call(expected_apply_transactions_argument)
        assert actual_ownership_states == expected_ownership_state
