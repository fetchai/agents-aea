# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains tests for the register protocol."""
# pylint: skip-file

from itertools import product
from unittest import mock

import pytest

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.valory.protocols.tendermint.dialogues import (
    TendermintDialogue,
    TendermintDialogues,
)
from packages.valory.protocols.tendermint.message import TendermintMessage


PERFORMATIVE = TendermintMessage.Performative
INITIAL_DIALOGUE_REFERENCE = ("0", "")
ALICE_TENDERMINT_INFO = "http://node2:26657"
BOB_TENDERMINT_INFO = "tcp://0.0.0.0:26656"

PERFORMATIVE_TEST_KWARGS = [
    dict(
        error_code=TendermintMessage.ErrorCode.INVALID_REQUEST,
        error_msg="Invalid request",
        error_data={"error": "Agent address not registered for this service."},
    ),
    dict(query=""),
    dict(info=ALICE_TENDERMINT_INFO),
]


# utility function
def mock_role(  # pylint: disable=unused-argument
    message: Message, receiver_address: Address
) -> BaseDialogue.Role:
    """Infer the role of the agent from an incoming/outgoing first message"""
    return TendermintDialogue.Role.AGENT


# tests
def test_performative_name_value_matching():
    """Test performative name, value, and match."""
    for performative in TendermintMessage.Performative:
        assert performative.name.isupper()
        assert performative.value.islower()
        assert performative.name == performative.value.upper()


@pytest.mark.parametrize(
    "performative, kwargs",
    zip(PERFORMATIVE, PERFORMATIVE_TEST_KWARGS),
)
def test_serialization(performative, kwargs):
    """Test that the serialization for the 'tendermint' protocol works."""

    msg = TendermintMessage(
        message_id=1,
        dialogue_reference=INITIAL_DIALOGUE_REFERENCE,
        target=0,
        performative=performative,
        **kwargs
    )
    encoded_msg = TendermintMessage.serializer.encode(msg)
    assert isinstance(encoded_msg, bytes)
    decoded_msg = TendermintMessage.serializer.decode(encoded_msg)
    assert decoded_msg == msg


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = TendermintMessage(performative=PERFORMATIVE.REQUEST)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(PERFORMATIVE, "__eq__", return_value=False):
            TendermintMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = TendermintMessage(performative=PERFORMATIVE.REQUEST, query="")
    encoded_msg = TendermintMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(PERFORMATIVE, "__eq__", return_value=False):
            TendermintMessage.serializer.decode(encoded_msg)


def test_inconsistent_type():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = TendermintMessage(performative=PERFORMATIVE.REQUEST, query=123)
    with pytest.raises(TypeError):
        TendermintMessage.serializer.encode(msg)


class TestDialogues:
    """Tests tendermint dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        args = mock_role, TendermintDialogue
        cls.dialogues_alice = TendermintDialogues("address_alice", *args)
        cls.dialogues_bob = TendermintDialogues("address_bob", *args)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.dialogues_alice._create_self_initiated(
            dialogue_opponent_addr=self.dialogues_bob.self_address,
            dialogue_reference=INITIAL_DIALOGUE_REFERENCE,
            role=TendermintDialogue.Role.AGENT,
        )
        assert isinstance(result, TendermintDialogue)
        assert result.role == TendermintDialogue.Role.AGENT

    def test_end_state_dialogue_stats(self):
        """Test end state dialogue stats"""
        dialogue_stats = self.dialogues_alice.dialogue_stats
        iterator = product(TendermintDialogue.EndState, range(1, 3), [True, False])
        for end_state, i, is_self_initiated in iterator:
            dialogue_stats.add_dialogue_endstate(end_state, is_self_initiated)
            assert dialogue_stats.self_initiated[end_state] == i

    def test_message_exchange(self):
        """Test message exchange between agents"""
        # create message and initialize dialogue
        request_msg, dialogue = self.dialogues_alice.create(
            counterparty=self.dialogues_bob.self_address,
            performative=TendermintMessage.Performative.REQUEST,
        )
        assert self.dialogues_alice.get_dialogue(request_msg)
        assert request_msg.dialogue_reference[0]
        assert not request_msg.dialogue_reference[1]
        # send message
        bob_dialogue = self.dialogues_bob.update(request_msg)
        assert bob_dialogue.last_incoming_message == request_msg
        # share tendermint configuration details
        response_msg = bob_dialogue.reply(
            target_message=request_msg,
            performative=TendermintMessage.Performative.RESPONSE,
            info=ALICE_TENDERMINT_INFO,
        )
        alice_dialogue = self.dialogues_alice.update(response_msg)
        assert alice_dialogue.last_incoming_message == response_msg
