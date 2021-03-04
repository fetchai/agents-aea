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

"""This module contains tests for decision_maker."""

import pytest
from aea_ledger_ethereum import EthereumCrypto

from aea.decision_maker.gop import OwnershipState
from aea.helpers.transaction.base import Terms


def test_non_initialized_ownership_state_raises_exception():
    """Test that non-initialized ownership state raises exception."""
    ownership_state = OwnershipState()

    with pytest.raises(ValueError):
        ownership_state.amount_by_currency_id

    with pytest.raises(ValueError):
        ownership_state.quantities_by_good_id


def test_initialisation():
    """Test the initialisation of the ownership_state."""
    currency_endowment = {"FET": 100}
    good_endowment = {"good_id": 2}
    ownership_state = OwnershipState()
    ownership_state.set(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    assert ownership_state.amount_by_currency_id is not None
    assert ownership_state.quantities_by_good_id is not None
    assert ownership_state.is_initialized


def test_is_affordable_for_uninitialized():
    """Test the initialisation of the ownership_state."""
    ownership_state = OwnershipState()
    buyer_terms = Terms(
        ledger_id=EthereumCrypto.identifier,
        sender_address="pk1",
        counterparty_address="pk2",
        amount_by_currency_id={"FET": -1},
        is_sender_payable_tx_fee=True,
        quantities_by_good_id={"good_id": 10},
        nonce="transaction nonce",
    )
    assert ownership_state.is_affordable(
        terms=buyer_terms
    ), "Any transaction should be classed as affordable."


class TestOwnershipState:
    """Test the OwnershipState module."""

    @classmethod
    def setup_class(cls):
        """Setup class for test case."""
        cls.buyer_terms = Terms(
            ledger_id=EthereumCrypto.identifier,
            sender_address="pk1",
            counterparty_address="pk2",
            amount_by_currency_id={"FET": -1},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": 10},
            nonce="transaction nonce",
        )
        cls.neutral_terms = Terms(
            ledger_id=EthereumCrypto.identifier,
            sender_address="pk1",
            counterparty_address="pk2",
            amount_by_currency_id={"FET": 0},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": 0},
            nonce="transaction nonce",
        )
        cls.malformed_terms = Terms(
            ledger_id=EthereumCrypto.identifier,
            sender_address="pk1",
            counterparty_address="pk2",
            amount_by_currency_id={"FET": -10},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": 10},
            nonce="transaction nonce",
        )
        cls.malformed_terms._amount_by_currency_id = {"FET": 10}
        cls.seller_terms = Terms(
            ledger_id=EthereumCrypto.identifier,
            sender_address="pk1",
            counterparty_address="pk2",
            amount_by_currency_id={"FET": 1},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": -10},
            nonce="transaction nonce",
        )

    def test_transaction_is_affordable_agent_is_buyer(self):
        """Check if the agent has the money to cover the sender_amount (the agent=sender is the buyer)."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert ownership_state.is_affordable(
            terms=self.buyer_terms
        ), "We should have the money for the transaction!"

    def test_transaction_is_affordable_there_is_no_wealth(self):
        """Reject the transaction when there is no wealth exchange."""
        currency_endowment = {"FET": 0}
        good_endowment = {"good_id": 0}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert not ownership_state.is_affordable_transaction(
            terms=self.buyer_terms
        ), "We must reject the transaction."

    def test_transaction_is_affordable_neutral(self):
        """Reject the transaction when there is no wealth exchange."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert not ownership_state.is_affordable_transaction(
            terms=self.neutral_terms
        ), "We must reject the transaction."

    def test_transaction_is_affordable_malformed(self):
        """Reject the transaction when there is no wealth exchange."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert not ownership_state.is_affordable_transaction(
            terms=self.malformed_terms
        ), "We must reject the transaction."

    def test_transaction_is_affordable_agent_is_seller(self):
        """Check if the agent has the goods (the agent=sender is the seller)."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert ownership_state.is_affordable_transaction(
            terms=self.seller_terms
        ), "We must reject the transaction."

    def test_apply(self):
        """Test the apply function."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 2}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        list_of_terms = [self.buyer_terms]
        state = ownership_state
        new_state = ownership_state.apply_transactions(list_of_terms=list_of_terms)
        assert (
            state != new_state
        ), "after applying a list_of_terms must have a different state!"

    def test_transaction_update(self):
        """Test the transaction update when sending tokens."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert ownership_state.amount_by_currency_id == currency_endowment
        assert ownership_state.quantities_by_good_id == good_endowment
        ownership_state.update(terms=self.buyer_terms)
        expected_amount_by_currency_id = {"FET": 99}
        expected_quantities_by_good_id = {"good_id": 30}
        assert ownership_state.amount_by_currency_id == expected_amount_by_currency_id
        assert ownership_state.quantities_by_good_id == expected_quantities_by_good_id

    def test_transaction_update_receive(self):
        """Test the transaction update when receiving tokens."""
        currency_endowment = {"FET": 100}
        good_endowment = {"good_id": 20}
        ownership_state = OwnershipState()
        ownership_state.set(
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
        )
        assert ownership_state.amount_by_currency_id == currency_endowment
        assert ownership_state.quantities_by_good_id == good_endowment
        ownership_state.update(terms=self.seller_terms)
        expected_amount_by_currency_id = {"FET": 101}
        expected_quantities_by_good_id = {"good_id": 10}
        assert ownership_state.amount_by_currency_id == expected_amount_by_currency_id
        assert ownership_state.quantities_by_good_id == expected_quantities_by_good_id
