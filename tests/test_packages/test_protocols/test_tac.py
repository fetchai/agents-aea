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

"""This module contains the tests of the messages module."""

from unittest import mock

import pytest

from packages.fetchai.protocols.tac.message import TacMessage


def test_tac_message_instantiation():
    """Test instantiation of the tac message."""
    assert TacMessage(
        performative=TacMessage.Performative.REGISTER, agent_name="some_name"
    )
    assert TacMessage(performative=TacMessage.Performative.UNREGISTER)
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION,
        tx_id="some_id",
        tx_sender_addr="some_address",
        tx_counterparty_addr="some_other_address",
        amount_by_currency_id={"FET": 10},
        tx_sender_fee=10,
        tx_counterparty_fee=10,
        quantities_by_good_id={"123": 0, "1234": 10},
        tx_nonce=1,
        tx_sender_signature="some_signature",
        tx_counterparty_signature="some_other_signature",
    )
    assert TacMessage(performative=TacMessage.Performative.CANCELLED)
    assert TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"FET": 10},
        exchange_params_by_currency_id={"FET": 10.0},
        quantities_by_good_id={"123": 20, "1234": 15},
        utility_params_by_good_id={"123": 30.0, "1234": 50.0},
        tx_fee=20,
        agent_addr_to_name={"agent_1": "Agent one", "agent_2": "Agent two"},
        currency_id_to_name={"FET": "currency_name"},
        good_id_to_name={"123": "First good", "1234": "Second good"},
        version_id="game_version_1",
    )
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        tx_id="some_id",
        amount_by_currency_id={"FET": 10},
        quantities_by_good_id={"123": 20, "1234": 15},
    )
    assert TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"msg": "This is info msg."},
    )
    assert str(TacMessage.Performative.REGISTER) == "register"


def test_tac_serialization():
    """Test that the serialization for the tac message works."""
    msg = TacMessage(
        performative=TacMessage.Performative.REGISTER, agent_name="some_name"
    )
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(performative=TacMessage.Performative.UNREGISTER)
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(
        performative=TacMessage.Performative.TRANSACTION,
        tx_id="some_id",
        tx_sender_addr="some_address",
        tx_counterparty_addr="some_other_address",
        amount_by_currency_id={"FET": -10},
        tx_sender_fee=10,
        tx_counterparty_fee=10,
        quantities_by_good_id={"123": 0, "1234": 10},
        tx_nonce=1,
        tx_sender_signature="some_signature",
        tx_counterparty_signature="some_other_signature",
    )
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(performative=TacMessage.Performative.CANCELLED)
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"FET": 10},
        exchange_params_by_currency_id={"FET": 10.0},
        quantities_by_good_id={"123": 20, "1234": 15},
        utility_params_by_good_id={"123": 30.0, "1234": 50.0},
        tx_fee=20,
        agent_addr_to_name={"agent_1": "Agent one", "agent_2": "Agent two"},
        currency_id_to_name={"FET": "currency_name"},
        good_id_to_name={"123": "First good", "1234": "Second good"},
        version_id="game_version_1",
    )
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        tx_id="some_id",
        amount_by_currency_id={"FET": 10},
        quantities_by_good_id={"123": 20, "1234": 15},
    )
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    with pytest.raises(
        ValueError, match="Performative not valid: transaction_confirmation"
    ):
        with mock.patch.object(TacMessage, "Performative") as mocked_type:
            mocked_type.TRANSACTION_CONFIRMATION.value = "unknown"
            TacMessage.serializer.encode(msg)

    msg = TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"msg": "This is info msg."},
    )
    msg_bytes = TacMessage.serializer.encode(msg)
    actual_msg = TacMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg
