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

import itertools
import logging
from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.valory.protocols.tendermint.dialogues import (
    TendermintDialogue,
    TendermintDialogues as BaseTendermintDialogues,
)
from packages.valory.protocols.tendermint.message import TendermintMessage

PERFORMATIVE = TendermintMessage.Performative

ALICE_TENDERMINT_INFO = dict(ip="192.168.0.0", hostname="alice")
BOB_TENDERMINT_INFO = dict(ip="192.168.255.255", hostname="bob")


def test_performative_name_value_matching():
    """Test performative name, value, and match."""
    for performative in TendermintMessage.Performative:
        assert performative.name.isupper()
        assert performative.value.islower()
        assert performative.name == performative.value.upper()


@pytest.mark.parametrize(
    "performative, kwargs",
    [
        (PERFORMATIVE.TENDERMINT_CONFIG_REQUEST, dict(query="")),
        (PERFORMATIVE.TENDERMINT_CONFIG_RESPONSE, dict(info=ALICE_TENDERMINT_INFO)),
        # (TendermintMessage.Performative.ERROR, dict(
        #     error_code=TendermintMessage.ErrorCode.INVALID_REQUEST,
        #     error_msg="Invalid request",
        #     info={"error": "Agent address not registered for this service."}
        # )),
    ],
)
def test_serialization(performative, kwargs):
    """Test that the serialization for the 'tendermint' protocol works."""

    msg = TendermintMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=performative,
        **kwargs
    )

    msg.to = "receiver"
    original_envelope = Envelope(to=msg.to, sender="sender", message=msg)
    retrieved_envelope = Envelope.decode(original_envelope.encode())
    # assert original_envelope = retrieved_envelope
    assert retrieved_envelope.to == original_envelope.to
    assert retrieved_envelope.sender == original_envelope.sender
    assert (
        retrieved_envelope.protocol_specification_id
        == original_envelope.protocol_specification_id
    )
    assert retrieved_envelope.sender == original_envelope.sender
    assert retrieved_envelope.context == original_envelope.context

    # what? why don't we decode the message contained in the envelope?
    logging.error(original_envelope.context)
    logging.error(retrieved_envelope.context)


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = TendermintMessage(performative=PERFORMATIVE.TENDERMINT_CONFIG_REQUEST)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(PERFORMATIVE, "__eq__", return_value=False):
            TendermintMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = TendermintMessage(
        performative=PERFORMATIVE.TENDERMINT_CONFIG_REQUEST, query=""
    )
    encoded_msg = TendermintMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(PERFORMATIVE, "__eq__", return_value=False):
            TendermintMessage.serializer.decode(encoded_msg)


class TendermintDialogues(BaseTendermintDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """Initialize dialogues"""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message"""
            return TendermintDialogue.Role.AGENT

        super().__init__(
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=TendermintDialogue,
        )


class TestDialogues:
    """Tests tendermint dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.dialogues_alice = TendermintDialogues("address_alice")
        cls.dialogues_bob = TendermintDialogues("address_bob")

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.dialogues_alice._create_self_initiated(
            dialogue_opponent_addr=self.dialogues_bob.self_address,
            dialogue_reference=("0", ""),
            role=TendermintDialogue.Role.AGENT,
        )
        assert isinstance(result, TendermintDialogue)
        assert result.role == TendermintDialogue.Role.AGENT

    def test_end_state_dialogue_stats(self):
        """Test end state dialogue stats"""
        dialogue_stats = self.dialogues_alice.dialogue_stats
        for end_state in TendermintDialogue.EndState:
            assert not dialogue_stats.self_initiated[end_state]
            for i, self_initiated in itertools.product(range(1, 3), [True, False]):
                dialogue_stats.add_dialogue_endstate(end_state, self_initiated)
                assert getattr(dialogue_stats, "self_initiated")[end_state] == i

    def test_message_exchange(self):
        """Test message exchange between agents"""
        # create message and initialize dialogue
        request_msg, dialogue = self.dialogues_alice.create(
            counterparty=self.dialogues_bob.self_address,
            performative=TendermintMessage.Performative.TENDERMINT_CONFIG_REQUEST,
            query="",
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
            performative=TendermintMessage.Performative.TENDERMINT_CONFIG_RESPONSE,
            info=ALICE_TENDERMINT_INFO,
        )
        alice_dialogue = self.dialogues_alice.update(response_msg)
        assert alice_dialogue.last_incoming_message == response_msg
