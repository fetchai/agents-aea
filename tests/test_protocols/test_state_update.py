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

"""This module contains tests for transaction."""
from unittest.mock import patch

import pytest

import aea
from aea.protocols.state_update.message import StateUpdateMessage


class TestStateUpdateMessage:
    """Test the StateUpdateMessage."""

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"FET": 10.0}
        utility_params = {"a_good": 20.0}
        assert StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
        )
        currency_change = {"FET": 10}
        good_change = {"a_good": 1}
        stum = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_change,
            quantities_by_good_id=good_change,
        )
        assert stum._is_consistent()
        assert len(stum.valid_performatives) == 2

    def test_message_inconsistency(self):
        """Test for an error in consistency of a message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"UNKNOWN": 10.0}
        utility_params = {"a_good": 20.0}
        tx_fee = 10
        stum = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
            tx_fee=tx_fee,
        )
        assert not stum._is_consistent()


class TestSerialization:
    """Test state update message serialization."""

    def test_serialization_initialize(self):
        """Test serialization of initialize message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"FET": 10.0}
        utility_params = {"a_good": 20.0}
        msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
        )
        encoded_msg = msg.serializer.encode(msg)
        decoded_msg = msg.serializer.decode(encoded_msg)
        assert msg == decoded_msg

    def test_serialization_apply(self):
        """Test serialization of apply message."""
        currency_change = {"FET": 10}
        good_change = {"a_good": 1}
        msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_change,
            quantities_by_good_id=good_change,
        )
        assert msg._is_consistent()
        assert len(msg.valid_performatives) == 2
        encoded_msg = msg.serializer.encode(msg)
        decoded_msg = msg.serializer.decode(encoded_msg)
        assert msg == decoded_msg


def test_serialization_negative():
    """Test serialization when performative is not recognized."""
    currency_change = {"FET": 10}
    good_change = {"a_good": 1}
    msg = StateUpdateMessage(
        performative=StateUpdateMessage.Performative.APPLY,
        amount_by_currency_id=currency_change,
        quantities_by_good_id=good_change,
    )

    with patch.object(StateUpdateMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {msg.performative}"
        ):
            msg.serializer.encode(msg)

    encoded_tx_bytes = msg.serializer.encode(msg)
    with patch.object(StateUpdateMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {msg.performative}"
        ):
            msg.serializer.decode(encoded_tx_bytes)


def test_performative_str():
    """Test performative __str__."""
    assert str(StateUpdateMessage.Performative.INITIALIZE) == "initialize"
    assert str(StateUpdateMessage.Performative.APPLY) == "apply"


def test_light_protocol_rule_3_target_less_than_message_id():
    """Test that if message_id is not 1, target must be > message_id"""
    with patch.object(
        aea.protocols.state_update.message.logger, "error"
    ) as mock_logger:
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"FET": 10.0}
        utility_params = {"a_good": 20.0}
        message_id = 2
        target = 2
        assert StateUpdateMessage(
            message_id=message_id,
            target=target,
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
        )

        mock_logger.assert_any_call(
            f"Invalid 'target'. Expected an integer between 1 and {message_id - 1} inclusive. Found {target}."
        )
