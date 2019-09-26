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
import base64
import json
from unittest import mock

from aea.mail.base import Envelope
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.models import Description


def test_fipa_cfp_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    query = base64.b64encode(json.dumps({"foo": "bar"}).encode("utf-8"))
    msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.CFP, query=query)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver", sender="sender", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_fipa_propose_serialization():
    """Test that the serialization for the 'fipa' protocol works."""
    proposal = [
        Description({"foo1": 1, "bar1": 2}),  # DataModel("dm_bar", [AttributeSchema("foo1", int, True), AttributeSchema("bar1", int, True)]))
        Description({"foo2": 1, "bar2": 2}),
    ]
    msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.PROPOSE, proposal=proposal)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver", sender="sender", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
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
    msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
    msg_bytes = FIPASerializer().encode(msg)
    envelope = Envelope(to="receiver", sender="sender", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope == actual_envelope

    actual_msg = FIPASerializer().decode(actual_envelope.message)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_not_recognized():
    """Test that if a performative is not recognized, the consistency check fails (returns False)."""
    msg = FIPAMessage(
        performative=FIPAMessage.Performative.ACCEPT,
        message_id=0,
        dialogue_id=0,
        destination="publicKey",
        target=1)

    with mock.patch("aea.protocols.fipa.message.FIPAMessage.Performative") as mock_performative_enum:
        mock_performative_enum.ACCEPT.value = "unknown"
        assert not msg.check_consistency()


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert str(FIPAMessage.Performative.CFP) == "cfp"
    assert str(FIPAMessage.Performative.PROPOSE) == "propose"
    assert str(FIPAMessage.Performative.DECLINE) == "decline"
    assert str(FIPAMessage.Performative.ACCEPT) == "accept"
    assert str(FIPAMessage.Performative.MATCH_ACCEPT) == "match_accept"


# def test_fipa_message_consistency():
#     """Tests the consistency of a messge."""
#     public_key = "publicKey"
#     myPerformative = FIPAMessage.Performative.ACCEPT
#     assert myPerformative.__str__() == "accept",\
#         "The string representation of Performative must be accept"
#     msg = FIPAMessage(
#         performative=FIPAMessage.Performative.UNKNOWN,
#         message_id=0,
#         dialogue_id=0,
#         destination=public_key,
#         target=1)
#     assert msg.consistent is False
# #    msg_bytes = FIPASerializer().encode(msg)
