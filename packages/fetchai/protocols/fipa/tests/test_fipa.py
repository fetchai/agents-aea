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

"""This module contains the tests of the fipa protocol package."""
# pylint: skip-file

import logging
from typing import Any, Optional, Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.fipa import message
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.message import (
    _default_logger as fipa_message_logger,
)


logger = logging.getLogger(__name__)


def test_cfp_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.CFP,
        query=Query([Constraint("something", ConstraintType(">", 1))]),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_propose_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.PROPOSE,
        proposal=Description({"foo1": 1, "bar1": 2}),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_accept_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_decline_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.DECLINE,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_match_accept_serialization():
    """Test the serialization - deserialization of the match_accept performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.MATCH_ACCEPT,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_accept_with_inform_serialization():
    """Test the serialization - deserialization of the accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.ACCEPT_W_INFORM,
        info={"address": "dummy_address"},
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_match_accept_with_inform_serialization():
    """Test the serialization - deserialization of the match_accept_with_address performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
        info={"address": "dummy_address", "signature": "my_signature"},
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_inform_serialization():
    """Test the serialization-deserialization of the inform performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.INFORM,
        info={"foo": "bar"},
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_end_serialization():
    """Test the serialization-deserialization of the end performative."""
    msg = FipaMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=FipaMessage.Performative.END,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = FipaMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


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


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = FipaMessage(
        performative=FipaMessage.Performative.ACCEPT,
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
            FipaMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = FipaMessage(
        performative=FipaMessage.Performative.ACCEPT,
    )

    encoded_msg = FipaMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FipaMessage.Performative, "__eq__", return_value=False):
            FipaMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the fipa message is incorrect."""
    with mock.patch.object(fipa_message_logger, "error") as mock_logger:
        FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests fipa dialogues."""

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
            dialogue_opponent_addr=self.seller_addr,
            dialogue_reference=(str(0), ""),
            role=FipaDialogue.Role.SELLER,
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
        cfp_msg, buyer_dialogue = self.buyer_dialogues.create(
            counterparty=self.seller_addr,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )

        # Checking that I can retrieve the dialogue.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(cfp_msg)
        assert (
            retrieved_dialogue == buyer_dialogue
        ), "Should have found correct dialogue"

        assert (
            cfp_msg.dialogue_reference[0] != "" and cfp_msg.dialogue_reference[1] == ""
        ), "The dialogue_reference is not set correctly."

        # MESSAGE BEING SENT BETWEEN AGENTS

        # Creates a new dialogue for the seller side based on the income message.
        seller_dialogue = self.seller_dialogues.update(cfp_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = seller_dialogue.last_incoming_message
        assert last_msg == cfp_msg, "The messages must be equal"

        # Generate a proposal message to send to the buyer.
        proposal = Description({"foo1": 1, "bar1": 2})
        proposal_msg = seller_dialogue.reply(
            target_message=cfp_msg,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )

        # MESSAGE BEING SENT BETWEEN AGENTS

        # Client received the message and we extend the incoming messages list.
        buyer_dialogue = self.buyer_dialogues.update(proposal_msg)

        # Check that both fields in the dialogue_reference are set.
        last_msg = buyer_dialogue.last_incoming_message
        assert last_msg == proposal_msg, "The two messages must be equal."

        # Retrieve the dialogue based on the received message.
        retrieved_dialogue = self.buyer_dialogues.get_dialogue(proposal_msg)
        assert retrieved_dialogue == buyer_dialogue, "Should have found dialogue"

        # Create an accept_w_inform message to send seller.
        accept_msg = buyer_dialogue.reply(
            target_message=proposal_msg,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={"address": "dummy_address"},
        )
        # MESSAGE BEING SENT BETWEEN AGENTS

        # Adds the message to the seller incoming message list.
        seller_dialogue = self.seller_dialogues.update(accept_msg)

        retrieved_dialogue = self.seller_dialogues.get_dialogue(accept_msg)
        assert seller_dialogue == retrieved_dialogue, "Should have found dialogue"

    def test_update(self):
        """Test the `update` functionality."""
        cfp_msg, buyer_dialogue = self.buyer_dialogues.create(
            counterparty=self.seller_addr,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )

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
        proposal_msg = seller_dialogue.reply(
            target_message=cfp_msg,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 1, "bar1": 2}),
        )

        assert len(seller_dialogue._outgoing_messages) == 1, "No outgoing messages."
        assert len(seller_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            seller_dialogue.last_outgoing_message == proposal_msg
        ), "Wrong outgoing message."

        # message arrives at counterparty
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

    def test_counter_proposing(self):
        """Test that fipa supports counter proposing."""
        cfp_msg, buyer_dialogue = self.buyer_dialogues.create(
            counterparty=self.seller_addr,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )

        assert len(buyer_dialogue._outgoing_messages) == 1, "No outgoing message."
        assert len(buyer_dialogue._incoming_messages) == 0, "Some incoming messages."
        assert (
            buyer_dialogue.last_outgoing_message == cfp_msg
        ), "wrong outgoing message in buyer dialogue after sending cfp."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[0] != ""
        ), "Dialogue reference incorrect."
        assert (
            buyer_dialogue.dialogue_label.dialogue_reference[1] == ""
        ), "Dialogue reference incorrect."
        dialogue_reference_left_part = buyer_dialogue.dialogue_label.dialogue_reference[
            0
        ]

        # cfp arrives at seller

        seller_dialogue = self.seller_dialogues.update(cfp_msg)

        assert len(seller_dialogue._outgoing_messages) == 0, "Some outgoing message."
        assert len(seller_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            seller_dialogue.last_incoming_message == cfp_msg
        ), "wrong incoming message in seller dialogue after receiving cfp."
        assert (
            seller_dialogue.dialogue_label.dialogue_reference[0] != ""
        ), "Dialogue reference incorrect."
        assert (
            seller_dialogue.dialogue_label.dialogue_reference[1] != ""
        ), "Dialogue reference incorrect."

        # seller creates proposal
        proposal_msg = seller_dialogue.reply(
            target_message=cfp_msg,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 1, "bar1": 2}),
        )

        assert len(seller_dialogue._outgoing_messages) == 1, "No outgoing messages."
        assert len(seller_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            seller_dialogue.last_outgoing_message == proposal_msg
        ), "wrong outgoing message in seller dialogue after sending proposal."

        # proposal arrives at buyer

        buyer_dialogue = self.buyer_dialogues.update(proposal_msg)

        assert len(buyer_dialogue._outgoing_messages) == 1, "No outgoing messages."
        assert len(buyer_dialogue._incoming_messages) == 1, "No incoming messages."
        assert (
            buyer_dialogue.last_incoming_message == proposal_msg
        ), "wrong incoming message in buyer dialogue after receiving proposal."
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

        # buyer creates counter proposal 1
        counter_proposal_msg_1 = buyer_dialogue.reply(
            target_message=proposal_msg,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 3, "bar1": 3}),
        )

        assert (
            len(buyer_dialogue._outgoing_messages) == 2
        ), "incorrect number of outgoing_messages in buyer dialogue after sending counter-proposal 1."
        assert (
            len(buyer_dialogue._incoming_messages) == 1
        ), "incorrect number of incoming_messages in buyer dialogue after sending counter-proposal 1."
        assert (
            buyer_dialogue.last_outgoing_message == counter_proposal_msg_1
        ), "wrong outgoing message in buyer dialogue after sending counter-proposal 1."

        # counter-proposal 1 arrives at seller

        seller_dialogue = self.seller_dialogues.update(counter_proposal_msg_1)

        assert (
            len(seller_dialogue._outgoing_messages) == 1
        ), "incorrect number of outgoing_messages in seller dialogue after receiving counter-proposal 1."
        assert (
            len(seller_dialogue._incoming_messages) == 2
        ), "incorrect number of incoming_messages in seller dialogue after receiving counter-proposal 1."
        assert (
            seller_dialogue.last_incoming_message == counter_proposal_msg_1
        ), "wrong incoming message in seller dialogue after receiving counter-proposal 1."

        # seller creates counter-proposal 2
        counter_proposal_msg_2 = seller_dialogue.reply(
            target_message=counter_proposal_msg_1,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 2, "bar1": 2}),
        )

        assert (
            len(seller_dialogue._outgoing_messages) == 2
        ), "incorrect number of outgoing_messages in seller dialogue after sending counter-proposal 2."
        assert (
            len(seller_dialogue._incoming_messages) == 2
        ), "incorrect number of incoming_messages in seller dialogue after sending counter-proposal 2."
        assert (
            seller_dialogue.last_outgoing_message == counter_proposal_msg_2
        ), "wrong outgoing message in seller dialogue after sending counter-proposal 2."

        # counter-proposal 2 arrives at buyer

        buyer_dialogue = self.buyer_dialogues.update(counter_proposal_msg_2)

        assert (
            len(buyer_dialogue._outgoing_messages) == 2
        ), "incorrect number of outgoing_messages in buyer dialogue after receiving counter-proposal 2."
        assert (
            len(buyer_dialogue._incoming_messages) == 2
        ), "incorrect number of incoming_messages in buyer dialogue after receiving counter-proposal 2."
        assert (
            buyer_dialogue.last_incoming_message == counter_proposal_msg_2
        ), "wrong incoming message in buyer dialogue after receiving counter-proposal 2."


class BuyerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[FipaMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        FipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class BuyerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogues is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.BUYER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=BuyerDialogue,
        )


class SellerDialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("some_object",)

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[FipaMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        FipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self.some_object = None  # type: Optional[Any]


class SellerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogues is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.SELLER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=SellerDialogue,
        )
