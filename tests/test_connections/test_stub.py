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
import time

import pytest
from unittest import mock

from aea.connections.oef.connection import OEFMailBox
from aea.connections.stub.connection import StubConnection
from aea.crypto.base import Crypto
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.fipa import fipa_pb2
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, DataModel, Attribute, Query, Constraint, ConstraintType
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer


class TestStubConnection:
    """Test that the stub connection is implemented correctly."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.connection = StubConnection()
        cls.mailbox1 = MailBox(cls.connection)
        cls.mailbox1.connect()

    def test_send_message(self):
        """Test that a default byte message can be sent correctly."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        expected_envelope = Envelope(to="any", sender="any", protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(msg))

        # from mailbox to connection
        self.mailbox1.outbox.put(expected_envelope)
        actual_envelope = self.connection.out_queue.get(timeout=2.0)
        assert expected_envelope == actual_envelope

        # from connection to mailbox
        self.connection.in_queue.put(expected_envelope)
        actual_envelope = self.mailbox1.inbox.get(timeout=2.0)
        assert expected_envelope == actual_envelope

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.mailbox1.disconnect()

