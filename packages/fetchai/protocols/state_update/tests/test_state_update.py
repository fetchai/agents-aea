# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
# pylint: skip-file

from typing import Type
from unittest.mock import patch

import pytest

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.state_update.dialogues import (
    StateUpdateDialogue as BaseStateUpdateDialogue,
)
from packages.fetchai.protocols.state_update.dialogues import (
    StateUpdateDialogues as BaseStateUpdateDialogues,
)
from packages.fetchai.protocols.state_update.message import StateUpdateMessage


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
        assert len(stum.valid_performatives) == 3
        stum = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.END,
        )
        assert stum._is_consistent()

    def test_message_inconsistency(self):
        """Test for an error in consistency of a message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"UNKNOWN": 10.0}
        utility_params = {"a_good": 20.0}
        with pytest.raises(ValueError, match="Field .* is not supported"):
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.INITIALIZE,
                amount_by_currency_id=currency_endowment,
                quantities_by_good_id=good_endowment,
                exchange_params_by_currency_id=exchange_params,
                utility_params_by_good_id=utility_params,
                non_exists_field="some value",
            )


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
        assert len(msg.valid_performatives) == 3
        encoded_msg = msg.serializer.encode(msg)
        decoded_msg = msg.serializer.decode(encoded_msg)
        assert msg == decoded_msg

    def test_serialization_end(self):
        """Test serialization of end message."""
        msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.END,
        )
        assert msg._is_consistent()
        assert len(msg.valid_performatives) == 3
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


def test_dialogues():
    """Test intiaontiation of dialogues."""
    state_update_dialogues = StateUpdateDialogues("agent_addr")
    msg, dialogue = state_update_dialogues.create(
        counterparty="abc",
        performative=StateUpdateMessage.Performative.INITIALIZE,
        amount_by_currency_id={},
        quantities_by_good_id={},
        exchange_params_by_currency_id={},
        utility_params_by_good_id={},
    )
    assert dialogue is not None


class StateUpdateDialogue(BaseStateUpdateDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[StateUpdateMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseStateUpdateDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class StateUpdateDialogues(BaseStateUpdateDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: self address
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return StateUpdateDialogue.Role.SKILL

        BaseStateUpdateDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=StateUpdateDialogue,
        )
