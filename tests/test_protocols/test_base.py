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

"""This module contains the tests of the messages module."""
from aea.mail.base import Envelope
from aea.protocols.base.message import Message
from aea.protocols.base.serialization import ProtobufSerializer, JSONSerializer


class TestBaseSerializations:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        """Set up the use case."""
        cls.message = Message(content="hello")

    def test_default_protobuf_serialization(self):
        """Test that the default Protobuf serialization works."""
        message_bytes = ProtobufSerializer().encode(self.message)
        envelope = Envelope(to="receiver", sender="sender", protocol_id="my_own_protocol", message=message_bytes)
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = ProtobufSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg

    def test_default_json_serialization(self):
        """Test that the default JSON serialization works."""
        message_bytes = JSONSerializer().encode(self.message)
        envelope = Envelope(to="receiver", sender="sender", protocol_id="my_own_protocol", message=message_bytes)
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = JSONSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg
