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

"""This module contains the tests of the ml_trade protocol package."""

import logging
import sys
from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

import packages
from packages.fetchai.protocols.ml_trade.dialogues import (
    MlTradeDialogue,
    MlTradeDialogues,
)
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.ml_trade.message import (
    _default_logger as ml_trade_message_logger,
)

from tests.conftest import ROOT_DIR


logger = logging.getLogger(__name__)
sys.path.append(ROOT_DIR)


def test_cfp_serialization():
    """Test the serialization for 'cfp' speech-act works."""
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.CFP,
        query=Query([Constraint("something", ConstraintType(">", 1))]),
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = MlTradeMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_terms_serialization():
    """Test the serialization for 'terms' speech-act works."""
    msg = MlTradeMessage(
        message_id=2,
        target=1,
        performative=MlTradeMessage.Performative.TERMS,
        terms=Description({"foo1": 1, "bar1": 2}),
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = MlTradeMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_accept_serialization():
    """Test the serialization for 'accept' speech-act works."""
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.ACCEPT,
        terms=Description({"foo1": 1, "bar1": 2}),
        tx_digest="some_tx_digest",
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = MlTradeMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_data_serialization():
    """Test the serialization for 'data' speech-act works."""
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.DATA,
        terms=Description({"foo1": 1, "bar1": 2}),
        payload=b"some_payload",
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = MlTradeMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert str(MlTradeMessage.Performative.CFP) == "cfp", "The str value must be cfp"
    assert (
        str(MlTradeMessage.Performative.TERMS) == "terms"
    ), "The str value must be terms"
    assert (
        str(MlTradeMessage.Performative.ACCEPT) == "accept"
    ), "The str value must be accept"
    assert str(MlTradeMessage.Performative.DATA) == "data", "The str value must be data"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.CFP,
        query=Query([Constraint("something", ConstraintType(">", 1))]),
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            MlTradeMessage.Performative, "__eq__", return_value=False
        ):
            MlTradeMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.CFP,
        query=Query([Constraint("something", ConstraintType(">", 1))]),
    )

    encoded_msg = MlTradeMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            MlTradeMessage.Performative, "__eq__", return_value=False
        ):
            MlTradeMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    packages.fetchai.protocols.ml_trade.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_fipa_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the fipa message is incorrect."""
    with mock.patch.object(ml_trade_message_logger, "error") as mock_logger:
        MlTradeMessage(
            performative=MlTradeMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests ml_trade dialogues."""

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
            role=MlTradeDialogue.Role.SELLER,
        )
        assert isinstance(result, MlTradeDialogue)
        assert result.role == MlTradeDialogue.Role.SELLER, "The role must be seller."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.buyer_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.seller_addr,
            dialogue_reference=(str(0), ""),
            role=MlTradeDialogue.Role.BUYER,
        )
        assert isinstance(result, MlTradeDialogue)
        assert result.role == MlTradeDialogue.Role.BUYER, "The role must be buyer."


class BuyerDialogue(MlTradeDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[MlTradeMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        MlTradeDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class BuyerDialogues(MlTradeDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return MlTradeDialogue.Role.BUYER

        MlTradeDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=BuyerDialogue,
        )


class SellerDialogue(MlTradeDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[MlTradeMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        MlTradeDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class SellerDialogues(MlTradeDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return MlTradeDialogue.Role.SELLER

        MlTradeDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=SellerDialogue,
        )
