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

"""This module contains the tests for the TAC protocol."""

import pytest

from aea.protocols.tac.message import TACMessage
from aea.protocols.tac.serialization import TACSerializer


def test_register_serialization():
    """Test that the serialization of the 'Register' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.REGISTER, agent_name="my_agent")
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_tac_message = TACSerializer().decode(tac_message_bytes)
    assert expected_tac_message == tac_message


def test_unregister_serialization():
    """Test that the serialization of the 'Unregister' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.UNREGISTER)
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_tac_message = TACSerializer().decode(tac_message_bytes)
    assert expected_tac_message == tac_message


def test_transaction_serialization():
    """Test that the serialization of the 'Transaction' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.TRANSACTION,
                             transaction_id="transaction_id",
                             is_sender_buyer=True,
                             counterparty="seller",
                             amount=10.0,
                             quantities_by_good_pbk={'tac_good_0_pbk': 1, 'tac_good_1_pbk': 1})
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


def test_get_state_update_serialization():
    """Test that the serialization of the 'GetStateUpdate' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.GET_STATE_UPDATE)
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


def test_cancelled_serialization():
    """Test that the serialization of the 'Cancelled' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.CANCELLED)
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


@pytest.mark.parametrize("error_code", list(TACMessage.ErrorCode))
def test_error_serialization(error_code):
    """Test that the serialization of the 'Error' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.TAC_ERROR,
                             error_code=error_code.value)
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


def test_game_data_serialization():
    """Test that the serialization of the 'GameData' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.GAME_DATA,
                             money=10.0,
                             endowment=[1, 1, 2],
                             utility_params=[0.04, 0.80, 0.16],
                             nb_agents=3,
                             nb_goods=3,
                             tx_fee=1.0,
                             agent_pbk_to_name={'tac_agent_0_pbk': 'tac_agent_0', 'tac_agent_1_pbk': 'tac_agent_1', 'tac_agent_2_pbk': 'tac_agent_2'},
                             good_pbk_to_name={'tag_good_0_pbk': 'tag_good_0', 'tag_good_1_pbk': 'tag_good_1', 'tag_good_2_pbk': 'tag_good_2'})
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


def test_transaction_confirmation_serialization():
    """Test that the serialization of the 'TransactionConfirmation' message works."""
    tac_message = TACMessage(tac_type=TACMessage.Type.TRANSACTION_CONFIRMATION, transaction_id="transaction_id")
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message


def test_state_update_serialization():
    """Test that the serialization of the 'StateUpdate' message works."""
    game_state = dict(
        money=10.0,
        endowment=[1, 1, 2],
        utility_params=[0.04, 0.80, 0.16],
        nb_agents=3,
        nb_goods=3,
        tx_fee=1.0,
        agent_pbk_to_name={'tac_agent_0_pbk': 'tac_agent_0', 'tac_agent_1_pbk': 'tac_agent_1', 'tac_agent_2_pbk': 'tac_agent_2'},
        good_pbk_to_name={'tag_good_0_pbk': 'tag_good_0', 'tag_good_1_pbk': 'tag_good_1', 'tag_good_2_pbk': 'tag_good_2'})

    transactions = [dict(
        transaction_id="transaction_id",
        is_sender_buyer=True,
        counterparty="seller",
        amount=10.0,
        quantities_by_good_pbk={"tac_good_0_pbk": 1}
    )]

    tac_message = TACMessage(tac_type=TACMessage.Type.STATE_UPDATE, initial_state=game_state, transactions=transactions)
    tac_message_bytes = TACSerializer().encode(tac_message)
    expected_msg = TACSerializer().decode(tac_message_bytes)

    assert expected_msg == tac_message
