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

import os
import shutil
import tempfile
from pathlib import Path

from aea import AEA_DIR
from aea.configurations.constants import DEFAULT_PROTOCOL
from aea.mail.base import Envelope
from aea.protocols.base import JSONSerializer, Message, ProtobufSerializer, Protocol

from tests.conftest import UNKNOWN_PROTOCOL_PUBLIC_ID


class TestBaseSerializations:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        """Set up the use case."""
        cls.message = Message(content="hello")
        cls.message2 = Message(body={"content": "hello"})

    def test_default_protobuf_serialization(self):
        """Test that the default Protobuf serialization works."""
        message_bytes = ProtobufSerializer().encode(self.message)
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
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
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = JSONSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg

    def test_set(self):
        """Test that the set method works."""
        key, value = "temporary_key", "temporary_value"
        assert self.message.get(key) is None
        self.message.set(key, value)
        assert self.message.get(key) == value

    def test_unset(self):
        """Test the unset function of the message."""
        self.message2.unset("content")
        assert "content" not in self.message2.body.keys()

    def test_body_setter(self):
        """Test the body setter."""
        m_dict = {"Hello": "World"}
        self.message2.body = m_dict
        assert "Hello" in self.message2.body.keys()


class TestProtocolFromDir:
    """Test the 'Protocol.from_dir' method."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_protocol_load_positive(self):
        """Test protocol loaded correctly."""
        default_protocol = Protocol.from_dir(Path(AEA_DIR, "protocols", "default"))
        assert str(default_protocol.public_id) == str(
            DEFAULT_PROTOCOL
        ), "Protocol not loaded correctly."

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
