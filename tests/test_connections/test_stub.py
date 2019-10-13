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

"""This test module contains the tests for the stub connection."""
import shutil
import tempfile
from pathlib import Path

from aea.connections.stub.connection import StubConnection
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer


class TestStubConnection:
    """Test that the stub connection is implemented correctly."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.tmpdir = Path(tempfile.mktemp())
        d = cls.tmpdir / "test_stub"
        d.mkdir(parents=True)
        cls.input_file_path = d / "input_file.csv"
        cls.output_file_path = d / "input_file.csv"

        cls.connection = StubConnection(cls.input_file_path, cls.output_file_path)
        cls.mailbox = MailBox(cls.connection)
        cls.mailbox.connect()

    def test_reception(self):
        """Test that the mailbox receives what has been enqueued in the input file."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        expected_envelope = Envelope(to="any", sender="any", protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(msg))

        encoded_envelope = "{},{},{},{}".format(expected_envelope.to, expected_envelope.sender, expected_envelope.protocol_id, expected_envelope.message.decode("utf-8"))
        encoded_envelope = encoded_envelope.encode("utf-8")
        with open(self.input_file_path, "ab+") as f:
            f.write(encoded_envelope + b"\n")
            f.flush()

        actual_envelope = self.mailbox.inbox.get(timeout=2.0)
        assert expected_envelope == actual_envelope

    def test_send_message(self):
        """Test that the messages in the outbox are posted on the output file."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        expected_envelope = Envelope(to="any", sender="any", protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(msg))

        self.mailbox.outbox.put(expected_envelope)

        with open(self.output_file_path, "rb+") as f:
            lines = f.readlines()

        assert len(lines) == 1
        line = lines[0]
        to, sender, protocol_id, message = line.strip().split(b",", maxsplit=3)
        to = to.decode("utf-8")
        sender = sender.decode("utf-8")
        protocol_id = protocol_id.decode("utf-8")

        actual_envelope = Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)
        assert expected_envelope == actual_envelope

    @classmethod
    def teardown_class(cls):
        """Tear down the test."""
        shutil.rmtree(cls.tmpdir, ignore_errors=True)
        cls.mailbox.disconnect()
