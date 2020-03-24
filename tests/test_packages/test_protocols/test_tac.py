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
from packages.fetchai.protocols.tac.serialization import TacSerializer


def test_tac_message_instantiation():
    """Test instantiation of the tac message."""
    assert TacMessage(performative=TacMessage.Performative.REGISTER, agent_name="some_name")
    assert TacMessage(performative=TacMessage.Performative.UNREGISTER)
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION,
        tx_id="some_id",
        tx_sender_addr="some_address",
        tx_counterparty_addr="some_other_address",
        amount_by_currency_id={"FET": 10},
        tx_sender_fee=10,
        tx_counterparty_fee=10,
        quantities_by_good_id={"good_1": 0, "good_2": 10},
        tx_nonce=1,
        tx_sender_signature=b"some_signature",
        tx_counterparty_signature=b"some_other_signature",
    )
    assert TacMessage(performative=TacMessage.Performative.GET_STATE_UPDATE)
    assert TacMessage(performative=TacMessage.Performative.CANCELLED)
    assert TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"FET": 10},
        exchange_params_by_currency_id={"FET": 10.0},
        quantities_by_good_id={"good_1": 20, "good_2": 15},
        utility_params_by_good_id={"good_1": 30.0, "good_2": 50.0},
        tx_fee=20,
        agent_addr_to_name={"agent_1": "Agent one", "agent_2": "Agent two"},
        good_id_to_name={"good_1": "First good", "good_2": "Second good"},
        version_id="game_version_1",
    )
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        tx_id="some_id",
        amount_by_currency_id={"FET": 10},
        quantities_by_good_id={"good_1": 20, "good_2": 15},
    )
    assert TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"msg": "This is info msg."},
    )
    assert str(TacMessage.Performative.REGISTER) == "register"


def test_tac_serialization():
    """Test that the serialization for the tac message works."""
    msg = TacMessage(performative=TacMessage.Performative.REGISTER, agent_name="some_name")
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(performative=TacMessage.Performative.UNREGISTER)
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
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
        quantities_by_good_id={"good_1": 0, "good_2": 10},
        tx_nonce=1,
        tx_sender_signature=b"some_signature",
        tx_counterparty_signature=b"some_other_signature",
    )
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(performative=TacMessage.Performative.GET_STATE_UPDATE)
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(performative=TacMessage.Performative.CANCELLED)
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"FET": 10},
        exchange_params_by_currency_id={"FET": 10.0},
        quantities_by_good_id={"good_1": 20, "good_2": 15},
        utility_params_by_good_id={"good_1": 30.0, "good_2": 50.0},
        tx_fee=20,
        agent_addr_to_name={"agent_1": "Agent one", "agent_2": "Agent two"},
        good_id_to_name={"good_1": "First good", "good_2": "Second good"},
        version_id="game_version_1",
    )
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        tx_id="some_id",
        amount_by_currency_id={"FET": 10},
        quantities_by_good_id={"good_1": 20, "good_2": 15},
    )
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    with pytest.raises(ValueError, match="Performative not valid: transaction_confirmation"):
        with mock.patch(
            "packages.fetchai.protocols.tac.message.TacMessage.Performative"
        ) as mocked_type:
            mocked_type.TRANSACTION_CONFIRMATION.value = "unknown"
            TacSerializer().encode(msg)

    msg = TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"msg": "This is info msg."},
    )
    msg_bytes = TacSerializer().encode(msg)
    actual_msg = TacSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg
