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

"""This module contains the tests for the FIPA protocol."""

import logging
from typing import Tuple, cast
from unittest import mock

import pytest

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer

logger = logging.getLogger(__name__)


def test_fipa_cfp_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    query = Query([Constraint("something", ConstraintType(">", 1))])

    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.CFP,
        query=query,
    )
    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FipaSerializer().decode(actual_envelope.message)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_fipa_cfp_serialization_bytes():
    """Test that the serialization - deserialization for the 'fipa' protocol works."""
    query = Query([Constraint("something", ConstraintType(">", 1))])
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.CFP,
        query=query,
    )
    msg.counterparty = "sender"
    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FipaSerializer().decode(actual_envelope.message)
    actual_msg.counterparty = "sender"
    expected_msg = msg
    assert expected_msg == actual_msg

    deserialised_msg = FipaSerializer().decode(envelope.message)
    deserialised_msg.counterparty = "sender"
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_fipa_propose_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    proposal = Description({"foo1": 1, "bar1": 2})
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.PROPOSE,
        proposal=proposal,
    )
    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FipaSerializer().decode(actual_envelope.message)
    expected_msg = msg

    p1 = actual_msg.get("proposal")
    p2 = expected_msg.get("proposal")
    assert p1.values == p2.values


def test_fipa_accept_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )
    msg.counterparty = "sender"
    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FipaSerializer().decode(actual_envelope.message)
    actual_msg.counterparty = "sender"
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_match_accept():
    """Test the serialization - deserialization of the match_accept performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.MATCH_ACCEPT,
    )
    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    msg.counterparty = "sender"
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FipaSerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_accept_with_inform():
    """Test the serialization - deserialization of the accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT_W_INFORM,
        info={"address": "dummy_address"},
    )

    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FipaSerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_match_accept_with_inform():
    """Test the serialization - deserialization of the match_accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
        info={"address": "dummy_address", "signature": "my_signature"},
    )

    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FipaSerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_inform():
    """Test the serialization-deserialization of the inform performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.INFORM,
        info={"foo": "bar"},
    )

    msg_bytes = FipaSerializer().encode(msg)
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg_bytes,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FipaSerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


# def test_unknown_performative():
#     """Test that we raise an exception when the performative is unknown during check_consistency."""
#     msg = FipaMessage(
#         message_id=1,
#         dialogue_reference=(str(0), ""),
#         target=0,
#         performative=FipaMessage.Performative.ACCEPT,
#     )
#     with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
#         assert not msg._is_consistent()


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert str(FipaMessage.Performative.CFP) == "cfp", "The str value must be cfp"
    assert (
        str(FipaMessage.Performative.PROPOSE) == "propose"
    ), "The str value must be propose"
    assert (
        str(FipaMessage.Performative.DECLINE) == "decline"
    ), "The str value must be decline"
    assert (
        str(FipaMessage.Performative.ACCEPT) == "accept"
    ), "The str value must be accept"
    assert (
        str(FipaMessage.Performative.MATCH_ACCEPT) == "match_accept"
    ), "The str value must be match_accept"
    assert (
        str(FipaMessage.Performative.ACCEPT_W_INFORM) == "accept_w_inform"
    ), "The str value must be accept_w_inform"
    assert (
        str(FipaMessage.Performative.MATCH_ACCEPT_W_INFORM) == "match_accept_w_inform"
    ), "The str value must be match_accept_w_inform"
    assert (
        str(FipaMessage.Performative.INFORM) == "inform"
    ), "The str value must be inform"


def test_fipa_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
            FipaSerializer().encode(msg)


def test_fipa_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )

    encoded_msg = FipaSerializer().encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
            FipaSerializer().decode(encoded_msg)


class TestDialogues:
    """Tests dialogues model from the packages protocols fipa."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.buyer_addr = "buyer address"
        cls.seller_addr = "seller address"
        cls.buyer_dialogues = FipaDialogues(cls.buyer_addr)
        cls.seller_dialogues = FipaDialogues(cls.seller_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.buyer_dialogues.create_self_initiated(
            dialogue_opponent_addr=self.seller_addr, role=FipaDialogue.AgentRole.SELLER,
        )
        assert isinstance(result, FipaDialogue)
        assert result.role == FipaDialogue.AgentRole.SELLER, "The role must be seller."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.buyer_dialogues.create_opponent_initiated(
            dialogue_opponent_addr=self.seller_addr,
            dialogue_reference=(str(0), ""),
            role=FipaDialogue.AgentRole.BUYER,
        )
        assert isinstance(result, FipaDialogue)
        assert result.role == FipaDialogue.AgentRole.BUYER

    def test_dialogue_endstates(self):
        """Test the end states of a dialogue."""
        assert self.buyer_dialogues.dialogue_stats is not None
        self.buyer_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.SUCCESSFUL, is_self_initiated=True
        )
        self.buyer_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_CFP, is_self_initiated=False
        )
        assert self.buyer_dialogues.dialogue_stats.self_initiated == {
            FipaDialogue.EndState.SUCCESSFUL: 1,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
            FipaDialogue.EndState.DECLINED_CFP: 0,
        }
        assert self.buyer_dialogues.dialogue_stats.other_initiated == {
            FipaDialogue.EndState.SUCCESSFUL: 0,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
            FipaDialogue.EndState.DECLINED_CFP: 1,
        }

    def test_dialogues_self_initiated_no_seller(self):
        """Test an end to end scenario of client-seller dialogue."""
        pytest.skip("This test is being skipped since it tests the old dialogue api")
        # Initialise a dialogue
        buyer_dialogue = self.buyer_dialogues.create_self_initiated(
            dialogue_opponent_addr=self.seller_addr, role=FipaDialogue.AgentRole.BUYER,
        )

        # Register the dialogue to the dictionary of dialogues.
        self.buyer_dialogues.dialogues[buyer_dialogue.dialogue_label] = cast(
            FipaDialogue, buyer_dialogue
        )

        # Send a message to the seller.
        cfp_msg = FipaMessage(
            message_id=1,
            dialogue_reference=buyer_dialogue.dialogue_label.dialogue_reference,
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_msg.counterparty = self.seller_addr

        # Checking that I cannot retrieve the dialogue.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(cfp_msg,)
        assert not retrieved_dialogue, "Should not have found any dialogues"

        # Checking the value error when we are trying to retrieve an un-existing dialogue.
        with pytest.raises(ValueError, match="Should have found dialogue."):
            self.buyer_dialogues.get_dialogue(cfp_msg)

        # Extends the outgoing list of messages.
        buyer_dialogue.outgoing_extend(cfp_msg)

        # Creates a new dialogue for the seller side based on the income message.
        seller_dialogue = self.seller_dialogues.create_opponent_initiated(
            dialogue_opponent_addr=cfp_msg.counterparty,
            dialogue_reference=cfp_msg.dialogue_reference,
            role=FipaDialogue.AgentRole.SELLER,
        )

        # Register the dialogue to the dictionary of dialogues.
        self.seller_dialogues.dialogues[seller_dialogue.dialogue_label] = cast(
            FipaDialogue, seller_dialogue
        )

        # change the incoming message field
        cfp_msg.is_incoming = True

        # change message counterparty field
        cfp_msg.counterparty = self.seller_addr

        # Extend the incoming list of messages.
        seller_dialogue.incoming_extend(cfp_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = seller_dialogue.last_incoming_message
        assert last_msg == cfp_msg, "The messages must be equal"
        dialogue_reference = cast(
            Tuple[str, str], last_msg.body.get("dialogue_reference")
        )
        assert (
            dialogue_reference[0] != "" and dialogue_reference[1] == ""
        ), "The dialogue_reference is not set correctly."

        # Generate a proposal message to send to the buyer.
        proposal = Description({"foo1": 1, "bar1": 2})
        message_id = cfp_msg.message_id + 1
        target = cfp_msg.message_id
        proposal_msg = FipaMessage(
            message_id=message_id,
            dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
            target=target,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )
        proposal_msg.counterparty = self.buyer_addr

        # Extends the outgoing list of messages.
        seller_dialogue.outgoing_extend(proposal_msg)

        # change the incoming message field
        cfp_msg.is_incoming = True

        # change message counterparty field
        cfp_msg.counterparty = self.seller_addr

        # Client received the message and we extend the incoming messages list.
        buyer_dialogue.incoming_extend(proposal_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = buyer_dialogue.last_incoming_message
        assert last_msg == proposal_msg, "The two messages must be equal."
        dialogue_reference = cast(
            Tuple[str, str], last_msg.body.get("dialogue_reference")
        )
        assert (
            dialogue_reference[0] != "" and dialogue_reference[1] != ""
        ), "The dialogue_reference is not setup properly."

        # Retrieve the dialogue based on the received message.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(proposal_msg,)
        assert retrieved_dialogue.dialogue_label is not None

        # Create an accept_w_inform message to send seller.
        message_id = proposal_msg.message_id + 1
        target = proposal_msg.message_id
        accept_msg = FipaMessage(
            message_id=message_id,
            dialogue_reference=buyer_dialogue.dialogue_label.dialogue_reference,
            target=target,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={"address": "dummy_address"},
        )
        accept_msg.counterparty = self.seller_addr

        # Adds the message to the buyer outgoing list.
        buyer_dialogue.outgoing_extend(accept_msg)

        # change the incoming message field
        cfp_msg.is_incoming = True

        # change message counterparty field
        cfp_msg.counterparty = self.buyer_addr

        # Adds the message to the seller incoming message list.
        seller_dialogue.incoming_extend(accept_msg)

        retrieved_dialogue = self.seller_dialogues.get_dialogue(accept_msg,)
        assert retrieved_dialogue.dialogue_label in self.seller_dialogues.dialogues

    def test_dialogues_self_initiated_is_seller(self):
        """Test an end to end scenario of seller-client dialogue."""
        pytest.skip("This test is being skipped since it tests the old dialogue api")

        # Initialise a dialogue
        seller_dialogue = self.seller_dialogues.create_self_initiated(
            dialogue_opponent_addr=self.buyer_addr, role=FipaDialogue.AgentRole.SELLER,
        )

        # Register the dialogue to the dictionary of dialogues.
        self.seller_dialogues.dialogues[seller_dialogue.dialogue_label] = cast(
            FipaDialogue, seller_dialogue
        )

        # Send a message to the client.
        cfp_msg = FipaMessage(
            message_id=1,
            dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_msg.counterparty = self.seller_addr

        seller_dialogue.outgoing_extend(cfp_msg)

        # Creates a new dialogue for the client side based on the income message.
        client_dialogue = self.buyer_dialogues.create_opponent_initiated(
            dialogue_opponent_addr=cfp_msg.counterparty,
            dialogue_reference=cfp_msg.dialogue_reference,
            role=FipaDialogue.AgentRole.BUYER,
        )

        # Register the dialogue to the dictionary of dialogues.
        self.buyer_dialogues.dialogues[client_dialogue.dialogue_label] = cast(
            FipaDialogue, client_dialogue
        )

        # Extend the incoming list of messages.
        client_dialogue.incoming_extend(cfp_msg)

        # Generate a proposal message to send to the seller.
        proposal = Description({"foo1": 1, "bar1": 2})
        message_id = cfp_msg.message_id + 1
        target = cfp_msg.message_id
        proposal_msg = FipaMessage(
            message_id=message_id,
            dialogue_reference=client_dialogue.dialogue_label.dialogue_reference,
            target=target,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )
        proposal_msg.counterparty = self.buyer_addr

        # Extends the outgoing list of messages.
        client_dialogue.outgoing_extend(proposal_msg)

        # Seller received the message and we extend the incoming messages list.
        seller_dialogue.incoming_extend(proposal_msg)

        # Test the self_initiated_dialogue explicitly
        message_id = proposal_msg.message_id + 1
        target = proposal_msg.message_id
        accept_msg = FipaMessage(
            message_id=message_id,
            dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
            target=target,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={"address": "dummy_address"},
        )
        accept_msg.counterparty = self.buyer_addr

        # Adds the message to the client outgoing list.
        seller_dialogue.outgoing_extend(accept_msg)
        # Adds the message to the seller incoming message list.
        client_dialogue.incoming_extend(accept_msg)
