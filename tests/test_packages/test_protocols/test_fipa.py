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
from typing import Any, Optional
from unittest import mock

import pytest

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Address, Envelope
from aea.protocols.base import Message

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage

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
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
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
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


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
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


def test_fipa_accept_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
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
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    msg.counterparty = "receiver"
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_accept_with_inform():
    """Test the serialization - deserialization of the accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT_W_INFORM,
        info={"address": "dummy_address"},
    )
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_match_accept_with_inform():
    """Test the serialization - deserialization of the match_accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
        info={"address": "dummy_address", "signature": "my_signature"},
    )
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_inform():
    """Test the serialization-deserialization of the inform performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.INFORM,
        info={"foo": "bar"},
    )
    msg.counterparty = "receiver"
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=FipaMessage.protocol_id,
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert expected_envelope.protocol_id == actual_envelope.protocol_id
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.counterparty = actual_envelope.to
    expected_msg = msg
    assert expected_msg == actual_msg


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
            FipaMessage.serializer.encode(msg)


def test_fipa_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )

    encoded_msg = FipaMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
            FipaMessage.serializer.decode(encoded_msg)


class TestDialogues:
    """Tests dialogues model from the packages protocols fipa."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.buyer_addr = "buyer address"
        cls.seller_addr = "seller address"
        cls.buyer_dialogues = BuyerDialogues(cls.buyer_addr)
        cls.seller_dialogues = SellerDialogues(cls.seller_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.buyer_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.seller_addr, role=FipaDialogue.Role.SELLER,
        )
        assert isinstance(result, FipaDialogue)
        assert result.role == FipaDialogue.Role.SELLER, "The role must be seller."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.buyer_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.seller_addr,
            dialogue_reference=(str(0), ""),
            role=FipaDialogue.Role.BUYER,
        )
        assert isinstance(result, FipaDialogue)
        assert result.role == FipaDialogue.Role.BUYER, "The role must be buyer."

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

    def test_dialogues_self_initiated(self):
        """Test an end to end scenario of client-seller dialogue."""

        # Create a message destined for the seller.
        cfp_msg = FipaMessage(
            message_id=1,
            dialogue_reference=self.buyer_dialogues.new_self_initiated_dialogue_reference(),
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_msg.counterparty = self.seller_addr

        # Extends the outgoing list of messages.
        buyer_dialogue = self.buyer_dialogues.update(cfp_msg)

        # Checking that I can retrieve the dialogue.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(cfp_msg)
        assert (
            retrieved_dialogue == buyer_dialogue
        ), "Should have found correct dialogue"

        assert (
            cfp_msg.dialogue_reference[0] != "" and cfp_msg.dialogue_reference[1] == ""
        ), "The dialogue_reference is not set correctly."

        # MESSAGE BEING SENT BETWEEN AGENTS

        # change the incoming message field & counterparty
        cfp_msg.is_incoming = True
        cfp_msg.counterparty = self.buyer_addr

        # Creates a new dialogue for the seller side based on the income message.
        seller_dialogue = self.seller_dialogues.update(cfp_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = seller_dialogue.last_incoming_message
        assert last_msg == cfp_msg, "The messages must be equal"

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

        assert (
            proposal_msg.dialogue_reference[0] != ""
            and proposal_msg.dialogue_reference[1] != ""
        ), "The dialogue_reference is not setup properly."

        # Extends the outgoing list of messages.
        seller_dialogue.update(proposal_msg)

        # MESSAGE BEING SENT BETWEEN AGENTS

        # change the incoming message field
        proposal_msg.is_incoming = True

        # change message counterparty field
        proposal_msg.counterparty = self.seller_addr

        # Client received the message and we extend the incoming messages list.
        buyer_dialogue = self.buyer_dialogues.update(proposal_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = buyer_dialogue.last_incoming_message
        assert last_msg == proposal_msg, "The two messages must be equal."

        # Retrieve the dialogue based on the received message.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(proposal_msg)
        assert retrieved_dialogue == buyer_dialogue, "Should have found dialogue"

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
        buyer_dialogue.update(accept_msg)

        # MESSAGE BEING SENT BETWEEN AGENTS

        # change the incoming message field
        accept_msg.is_incoming = True

        # change message counterparty field
        accept_msg.counterparty = self.buyer_addr

        # Adds the message to the seller incoming message list.
        seller_dialogue = self.seller_dialogues.update(accept_msg)

        retrieved_dialogue = self.seller_dialogues.get_dialogue(accept_msg)
        assert seller_dialogue == retrieved_dialogue, "Should have found dialogue"

    def test_update(self):
        """Test the `update` functionality."""
        cfp_msg = FipaMessage(
            message_id=1,
            dialogue_reference=self.buyer_dialogues.new_self_initiated_dialogue_reference(),
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_msg.counterparty = self.seller_addr
        buyer_dialogue = self.buyer_dialogues.update(cfp_msg)

        assert len(buyer_dialogue._outgoing_messages) == 1, "No outgoing message."
        assert len(buyer_dialogue._incoming_messages) == 0, "Some incoming messages."
        assert (
            buyer_dialogue.last_outgoing_message == cfp_msg
        ), "Wrong outgoing message."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[0] != ""
        ), "Dialogue reference incorrect."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[1] == ""
        ), "Dialogue reference incorrect."
        dialogue_reference_left_part = buyer_dialogue.dialogue_label.dialogue_reference[
            0
        ]

        # message arrives at counterparty
        cfp_msg.is_incoming = True
        cfp_msg.counterparty = self.buyer_addr
        seller_dialogue = self.seller_dialogues.update(cfp_msg)

        assert len(seller_dialogue._outgoing_messages) == 0, "Some outgoing message."
        assert len(seller_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            seller_dialogue.last_incoming_message == cfp_msg
        ), "Wrong incoming message."
        assert (
            seller_dialogue.dialogue_label.dialogue_reference[0] != ""
        ), "Dialogue reference incorrect."
        assert (
            seller_dialogue.dialogue_label.dialogue_reference[1] != ""
        ), "Dialogue reference incorrect."

        # seller creates response message
        proposal_msg = FipaMessage(
            message_id=cfp_msg.message_id + 1,
            dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
            target=cfp_msg.message_id,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 1, "bar1": 2}),
        )
        proposal_msg.counterparty = self.buyer_addr

        self.seller_dialogues.update(proposal_msg)

        assert len(seller_dialogue._outgoing_messages) == 1, "No outgoing messages."
        assert len(seller_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            seller_dialogue.last_outgoing_message == proposal_msg
        ), "Wrong outgoing message."

        # message arrives at counterparty
        proposal_msg.counterparty = self.seller_addr
        proposal_msg.is_incoming = True
        self.buyer_dialogues.update(proposal_msg)

        assert len(buyer_dialogue._outgoing_messages) == 1, "No outgoing messages."
        assert len(buyer_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            buyer_dialogue.last_outgoing_message == cfp_msg
        ), "Wrong outgoing message."
        assert (
            buyer_dialogue.last_incoming_message == proposal_msg
        ), "Wrong incoming message."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[0] != ""
        ), "Dialogue reference incorrect."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[1] != ""
        ), "Dialogue reference incorrect."
        assert (
            dialogue_reference_left_part
            == buyer_dialogue.dialogue_label.dialogue_reference[0]
        ), "Dialogue refernce changed unexpectedly."


class BuyerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )


class BuyerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, agent_address) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        FipaDialogues.__init__(self, agent_address)

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: BaseDialogue.Role,
    ) -> BuyerDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = BuyerDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return FipaDialogue.Role.BUYER


class SellerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self.some_object = None  # type: Optional[Any]


class SellerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, agent_address) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        FipaDialogues.__init__(self, agent_address)

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: BaseDialogue.Role,
    ) -> SellerDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = SellerDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return FipaDialogue.Role.SELLER
