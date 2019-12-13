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
from unittest import mock

import pytest

from aea.mail.base import Envelope
from aea.protocols.fipa.dialogues import FIPADialogues, FIPADialogue
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.models import Description, Query, Constraint, ConstraintType


def test_fipa_cfp_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    query = Query([Constraint('something', ConstraintType('>', 1))])

    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=0,
                      performative=FIPAMessage.Performative.CFP,
                      query=query)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg.set("query", "not_supported_query")
    with pytest.raises(ValueError, match="Query type not supported:"):
        FIPASerializer().encode(msg)


def test_fipa_cfp_serialization_bytes():
    """Test that the serialization - deserialization for the 'fipa' protocol works."""
    query = b'Hello'
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=0,
                      performative=FIPAMessage.Performative.CFP,
                      query=query)
    msg.counterparty = "sender"
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    actual_msg.counterparty = "sender"
    expected_msg = msg
    assert expected_msg == actual_msg

    deserialised_msg = FIPASerializer().decode(envelope.message)
    deserialised_msg.counterparty = "sender"
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_fipa_propose_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    proposal = [
        Description({"foo1": 1, "bar1": 2}),
        Description({"foo2": 1, "bar2": 2}),
    ]
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=0,
                      performative=FIPAMessage.Performative.PROPOSE,
                      proposal=proposal)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    expected_msg = msg

    p1 = actual_msg.get("proposal")
    p2 = expected_msg.get("proposal")
    assert p1[0].values == p2[0].values
    assert p1[1].values == p2[1].values


def test_fipa_accept_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=0,
                      performative=FIPAMessage.Performative.ACCEPT)
    msg.counterparty = "sender"
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    actual_msg.counterparty = "sender"
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_match_accept():
    """Test the serialization - deserialization of the match_accept performative."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.MATCH_ACCEPT)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    msg.counterparty = "sender"
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FIPASerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_not_recognized():
    """Tests an unknown Performative."""
    msg = FIPAMessage(
        performative=FIPAMessage.Performative.ACCEPT,
        message_id=0,
        dialogue_reference=(str(0), ''),
        target=1)

    with mock.patch("aea.protocols.fipa.message.FIPAMessage.Performative")\
            as mock_performative_enum:
        mock_performative_enum.ACCEPT.value = "unknown"
        assert not msg.check_consistency(),\
            "We expect that the check_consistency will return False"


def test_performative_accept_with_inform():
    """Test the serialization - deserialization of the accept_with_address performative."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
                      info={"address": "dummy_address"})

    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FIPASerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_match_accept_with_inform():
    """Test the serialization - deserialization of the match_accept_with_address performative."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
                      info={"address": "dummy_address", "signature": "my_signature"})

    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FIPASerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_inform():
    """Test the serialization-deserialization of the inform performative."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.INFORM,
                      info={"foo": "bar"})

    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver",
                        sender="sender",
                        protocol_id=FIPAMessage.protocol_id,
                        message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope
    deserialised_msg = FIPASerializer().decode(envelope.message)
    assert msg.get("performative") == deserialised_msg.get("performative")


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert str(FIPAMessage.Performative.CFP) == "cfp",\
        "The str value must be cfp"
    assert str(FIPAMessage.Performative.PROPOSE) == "propose",\
        "The str value must be propose"
    assert str(FIPAMessage.Performative.DECLINE) == "decline",\
        "The str value must be decline"
    assert str(FIPAMessage.Performative.ACCEPT) == "accept",\
        "The str value must be accept"
    assert str(FIPAMessage.Performative.MATCH_ACCEPT) == "match_accept",\
        "The str value must be match_accept"
    assert str(FIPAMessage.Performative.ACCEPT_W_INFORM) == "accept_w_inform", \
        "The str value must be accept_w_inform"
    assert str(FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM) == "match_accept_w_inform", \
        "The str value must be match_accept_w_inform"
    assert str(FIPAMessage.Performative.INFORM) == "inform", \
        "The str value must be inform"


def test_fipa_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.ACCEPT)

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FIPAMessage.Performative, "__eq__", return_value=False):
            FIPASerializer().encode(msg)


def test_fipa_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = FIPAMessage(message_id=0,
                      dialogue_reference=(str(0), ''),
                      target=1,
                      performative=FIPAMessage.Performative.ACCEPT)

    encoded_msg = FIPASerializer().encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(FIPAMessage.Performative, "__eq__", return_value=False):
            FIPASerializer().decode(encoded_msg)


def test_dialogues():
    """Test the dialogues model."""
    dialogues = FIPADialogues()
    result = dialogues.create_self_initiated(dialogue_starter_addr="starter", dialogue_opponent_addr="opponent", is_seller=True)
    assert isinstance(result, FIPADialogue)
    result = dialogues.create_opponent_initiated(dialogue_opponent_addr="opponent", dialogue_reference=(str(0), ''), is_seller=False)
    assert isinstance(result, FIPADialogue)
    assert result.role == FIPADialogue.AgentRole.BUYER
    assert dialogues.dialogue_stats is not None
    dialogues.dialogue_stats.add_dialogue_endstate(FIPADialogue.EndState.SUCCESSFUL, is_self_initiated=True)
    dialogues.dialogue_stats.add_dialogue_endstate(FIPADialogue.EndState.DECLINED_CFP, is_self_initiated=False)
    assert dialogues.dialogue_stats.self_initiated == {FIPADialogue.EndState.SUCCESSFUL: 1, FIPADialogue.EndState.DECLINED_PROPOSE: 0, FIPADialogue.EndState.DECLINED_ACCEPT: 0, FIPADialogue.EndState.DECLINED_CFP: 0}
    assert dialogues.dialogue_stats.other_initiated == {FIPADialogue.EndState.SUCCESSFUL: 0, FIPADialogue.EndState.DECLINED_PROPOSE: 0, FIPADialogue.EndState.DECLINED_ACCEPT: 0, FIPADialogue.EndState.DECLINED_CFP: 1}
