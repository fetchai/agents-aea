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

from aea.configurations.base import PublicId
from aea.decision_maker.base import OwnershipState
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.transaction import TransactionMessage


def test_non_initialized_ownership_state_raises_exception():
    """Test that non-initialized ownership state raises exception."""
    ownership_state = OwnershipState()

    with pytest.raises(AssertionError):
        ownership_state.amount_by_currency_id

    with pytest.raises(AssertionError):
        ownership_state.quantities_by_good_id


def test_initialisation():
    """Test the initialisation of the ownership_state."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 100}
    good_endowment = {"good_id": 2}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    assert ownership_state.amount_by_currency_id is not None
    assert ownership_state.quantities_by_good_id is not None
    assert ownership_state.is_initialized


def test_body():
    """Test the setter for the body."""
    msg = InternalMessage()
    msg.body = {"test_key": "test_value"}

    other_msg = InternalMessage(body={"test_key": "test_value"})
    assert msg == other_msg, "Messages should be equal."
    assert str(msg) == "InternalMessage(test_key=test_value)"
    assert msg._body is not None
    msg.body = {"Test": "My_test"}
    assert msg._body == {
        "Test": "My_test"
    }, "Message body must be equal with the above dictionary."
    msg.set("Test", 2)
    assert msg._body["Test"] == 2, "body['Test'] should be equal to 2."
    msg.unset("Test")
    assert "Test" not in msg._body.keys(), "Test should not exist."


def test_transaction_is_affordable_agent_is_buyer():
    """Check if the agent has the money to cover the sender_amount (the agent=sender is the buyer)."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 100}
    good_endowment = {"good_id": 20}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": -1},
        tx_sender_fee=0,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 10},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )

    assert ownership_state.is_affordable_transaction(
        tx_message=tx_message
    ), "We should have the money for the transaction!"


def test_transaction_is_affordable_there_is_no_wealth():
    """Reject the transaction when there is no wealth exchange."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 0}
    good_endowment = {"good_id": 0}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": 0},
        tx_sender_fee=0,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 0},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )

    assert not ownership_state.is_affordable_transaction(
        tx_message=tx_message
    ), "We must reject the transaction."


def tests_transaction_is_affordable_agent_is_the_seller():
    """Check if the agent has the goods (the agent=sender is the seller)."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 0}
    good_endowment = {"good_id": 0}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": 10},
        tx_sender_fee=0,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 0},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )

    assert ownership_state.is_affordable_transaction(
        tx_message=tx_message
    ), "We must reject the transaction."


def tests_transaction_is_affordable_else_statement():
    """Check that the function returns false if we cannot satisfy any if/elif statements."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 0}
    good_endowment = {"good_id": 0}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": 10},
        tx_sender_fee=0,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 50},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )

    assert not ownership_state.is_affordable_transaction(
        tx_message=tx_message
    ), "We must reject the transaction."


def test_apply():
    """Test the apply function."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 100}
    good_endowment = {"good_id": 2}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": -20},
        tx_sender_fee=5,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 10},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )
    list_of_transactions = [tx_message]
    state = ownership_state
    new_state = ownership_state.apply_transactions(transactions=list_of_transactions)
    assert (
        state != new_state
    ), "after applying a list_of_transactions must have a different state!"


def test_transaction_update():
    """Test the transaction update when sending tokens."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 100}
    good_endowment = {"good_id": 20}

    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    assert ownership_state.amount_by_currency_id == currency_endowment
    assert ownership_state.quantities_by_good_id == good_endowment
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": -20},
        tx_sender_fee=5,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": 10},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )
    ownership_state._update(tx_message=tx_message)
    expected_amount_by_currency_id = {"FET": 75}
    expected_quantities_by_good_id = {"good_id": 30}
    assert ownership_state.amount_by_currency_id == expected_amount_by_currency_id
    assert ownership_state.quantities_by_good_id == expected_quantities_by_good_id


def test_transaction_update_receive():
    """Test the transaction update when receiving tokens."""
    ownership_state = OwnershipState()
    currency_endowment = {"FET": 75}
    good_endowment = {"good_id": 30}
    ownership_state.init(
        amount_by_currency_id=currency_endowment, quantities_by_good_id=good_endowment,
    )
    assert ownership_state.amount_by_currency_id == currency_endowment
    assert ownership_state.quantities_by_good_id == good_endowment
    tx_message = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("author", "a_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr="agent_1",
        tx_counterparty_addr="pk",
        tx_amount_by_currency_id={"FET": 20},
        tx_sender_fee=5,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={"good_id": -10},
        info={"some_info_key": "some_info_value"},
        ledger_id="fetchai",
        tx_nonce="transaction nonce",
    )
    ownership_state._update(tx_message=tx_message)
    expected_amount_by_currency_id = {"FET": 90}
    expected_quantities_by_good_id = {"good_id": 20}
    assert ownership_state.amount_by_currency_id == expected_amount_by_currency_id
    assert ownership_state.quantities_by_good_id == expected_quantities_by_good_id
