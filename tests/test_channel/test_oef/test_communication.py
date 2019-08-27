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

"""This test module contains the tests for the OEF communication using an OEF."""

import pytest
from oef.query import Eq

from aea.channel.oef import OEFMailBox
from aea.crypto.base import Crypto
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, DataModel, Attribute, Query, Constraint
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer


def test_connection(network_node):
    """Test that a mailbox can connect to the OEF."""
    crypto = Crypto()
    mailbox = OEFMailBox(crypto.public_key, oef_addr="127.0.0.1", oef_port=10000)
    mailbox.connect()

    mailbox.disconnect()


class TestDefault:
    """Test that the default protocol is correctly implemented by the OEF channel."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.crypto1 = Crypto()
        cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
        cls.mailbox1.connect()

    def test_send_message(self):
        """Test that a default byte message can be sent correctly."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        self.mailbox1.outbox.put_message(to=self.crypto1.public_key, sender=self.crypto1.public_key,
                                         protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(msg))

        recv_msg = self.mailbox1.inbox.get(block=True, timeout=3.0)
        assert recv_msg is not None

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.mailbox1.disconnect()


class TestOEF:
    """Test that the OEF protocol is correctly implemented by the OEF channel."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.crypto1 = Crypto()
        cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
        cls.mailbox1.connect()

    def test_search_services(self):
        """Test that a search services request can be sent correctly."""
        request_id = 1
        data_model = DataModel("foobar", [Attribute("foo", str, True)])
        search_query = Query([Constraint("foo", Eq("bar"))], model=data_model)
        search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=search_query)
        self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))

        envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
        search_result = OEFSerializer().decode(envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT and search_result.get("id") == 1

        request_id = 2
        search_query_empty_model = Query([Constraint("foo", Eq("bar"))], model=None)
        search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=search_query_empty_model)
        self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))

        envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
        search_result = OEFSerializer().decode(envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT and search_result.get("id") == 2

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.mailbox1.disconnect()


class TestFIPA:
    """Test that the FIPA protocol is correctly implemented by the OEF channel."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Activate the OEF Node fixture."""
        pass

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.crypto1 = Crypto()
        cls.crypto2 = Crypto()
        cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
        cls.mailbox2 = OEFMailBox(cls.crypto2.public_key, oef_addr="127.0.0.1", oef_port=10000)
        cls.mailbox1.connect()
        cls.mailbox2.connect()

    def test_cfp(self):
        """Test that a CFP can be sent correctly."""
        cfp_bytes = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.CFP, query=b"hello")
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(cfp_bytes))
        envelope = self.mailbox2.inbox.get(block=True, timeout=5.0)
        expected_cfp_bytes = FIPASerializer().decode(envelope.message)
        assert expected_cfp_bytes == cfp_bytes

        cfp_none = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.CFP, query=None)
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(cfp_none))
        envelope = self.mailbox2.inbox.get(block=True, timeout=5.0)
        expected_cfp_none = FIPASerializer().decode(envelope.message)
        assert expected_cfp_none == cfp_none

    def test_propose(self):
        """Test that a Propose can be sent correctly."""
        propose_empty = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.PROPOSE, proposal=[])
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(propose_empty))
        envelope = self.mailbox2.inbox.get(block=True, timeout=2.0)
        expected_propose_empty = FIPASerializer().decode(envelope.message)
        assert expected_propose_empty == propose_empty

        propose_descriptions = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.PROPOSE, proposal=[Description({"foo": "bar"}, DataModel("foobar", [Attribute("foo", str, True)]))])
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(propose_descriptions))
        envelope = self.mailbox2.inbox.get(block=True, timeout=2.0)
        expected_propose_descriptions = FIPASerializer().decode(envelope.message)
        assert expected_propose_descriptions == propose_descriptions

    def test_accept(self):
        """Test that an Accept can be sent correctly."""
        accept = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(accept))
        envelope = self.mailbox2.inbox.get(block=True, timeout=2.0)
        expected_accept = FIPASerializer().decode(envelope.message)
        assert expected_accept == accept

    def test_match_accept(self):
        """Test that a match accept can be sent correctly."""
        # TODO since the OEF SDK doesn't support the match accept, we have to use a fixed message id!
        match_accept = FIPAMessage(message_id=4, dialogue_id=0, target=3, performative=FIPAMessage.Performative.MATCH_ACCEPT)
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(match_accept))
        envelope = self.mailbox2.inbox.get(block=True, timeout=2.0)
        expected_match_accept = FIPASerializer().decode(envelope.message)
        assert expected_match_accept == match_accept

    def test_decline(self):
        """Test that a Decline can be sent correctly."""
        decline = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.DECLINE)
        self.mailbox1.outbox.put_message(to=self.crypto2.public_key, sender=self.crypto1.public_key, protocol_id=FIPAMessage.protocol_id, message=FIPASerializer().encode(decline))
        envelope = self.mailbox2.inbox.get(block=True, timeout=2.0)
        expected_decline = FIPASerializer().decode(envelope.message)
        assert expected_decline == decline

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.mailbox1.disconnect()
        cls.mailbox2.disconnect()
