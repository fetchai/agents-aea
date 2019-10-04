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
import time

import pytest
from unittest import mock

from aea.connections.oef.connection import OEFMailBox
from aea.crypto.base import Crypto
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.fipa import fipa_pb2
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, DataModel, Attribute, Query, Constraint, ConstraintType
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

    class TestSearchServices:
        """Tests related to service search functionality."""

        @classmethod
        def setup_class(cls):
            """Set the test up."""
            cls.crypto1 = Crypto()
            cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
            cls.mailbox1.connect()

        def test_search_services_with_query_without_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has no data model.
            """
            request_id = 1
            search_query_empty_model = Query([Constraint("foo", ConstraintType("==", "bar"))], model=None)
            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=search_query_empty_model)
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))

            envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
            search_result = OEFSerializer().decode(envelope.message)
            assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
            assert search_result.get("id")
            assert request_id and search_result.get("agents") == []

        def test_search_services_with_query_with_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has a simple data model.
            """
            request_id = 2
            data_model = DataModel("foobar", [Attribute("foo", str, True)])
            search_query = Query([Constraint("foo", ConstraintType("==", "bar"))], model=data_model)
            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=search_query)
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))

            envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
            search_result = OEFSerializer().decode(envelope.message)
            assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
            assert search_result.get("id") == request_id
            assert search_result.get("agents") == []

        @classmethod
        def teardown_class(cls):
            """Teardowm the test."""
            cls.mailbox1.disconnect()

    class TestRegisterService:
        """Tests related to service registration functionality."""

        @classmethod
        def setup_class(cls):
            """Set the test up."""
            cls.crypto1 = Crypto()
            cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
            cls.mailbox1.connect()

        def test_register_service(self):
            """Test that a register service request works correctly."""
            foo_datamodel = DataModel("foo", [Attribute("bar", int, True, "A bar attribute.")])
            desc = Description({"bar": 1}, data_model=foo_datamodel)
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=1, service_description=desc, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=2, query=Query([Constraint("bar", ConstraintType("==", 1))], model=foo_datamodel))
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))
            envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
            search_result = OEFSerializer().decode(envelope.message)
            assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
            assert search_result.get("id") == 2
            assert search_result.get("agents") == [self.crypto1.public_key]

        @classmethod
        def teardown_class(cls):
            """Teardowm the test."""
            cls.mailbox1.disconnect()

    class TestUnregisterService:
        """Tests related to service unregistration functionality."""

        @classmethod
        def setup_class(cls):
            """
            Set the test up.

            Steps:
            - Register a service
            - Check that the registration worked.
            """
            cls.crypto1 = Crypto()
            cls.mailbox1 = OEFMailBox(cls.crypto1.public_key, oef_addr="127.0.0.1", oef_port=10000)
            cls.mailbox1.connect()

            cls.request_id = 1
            cls.foo_datamodel = DataModel("foo", [Attribute("bar", int, True, "A bar attribute.")])
            cls.desc = Description({"bar": 1}, data_model=cls.foo_datamodel)
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=cls.request_id, service_description=cls.desc, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            cls.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=cls.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

            time.sleep(1.0)

            cls.request_id += 1
            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=cls.request_id, query=Query([Constraint("bar", ConstraintType("==", 1))], model=cls.foo_datamodel))
            cls.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=cls.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))
            envelope = cls.mailbox1.inbox.get(block=True, timeout=5.0)
            search_result = OEFSerializer().decode(envelope.message)
            assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
            assert search_result.get("id") == cls.request_id
            assert search_result.get("agents") == [cls.crypto1.public_key]

        def test_unregister_service(self):
            """Test that an unregister service request works correctly.

            Steps:
            2. unregister the service
            3. search for that service
            4. assert that no result is found.
            """
            self.request_id += 1
            msg = OEFMessage(oef_type=OEFMessage.Type.UNREGISTER_SERVICE, id=self.request_id, service_description=self.desc, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

            time.sleep(1.0)

            self.request_id += 1
            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=self.request_id, query=Query([Constraint("bar", ConstraintType("==", 1))], model=self.foo_datamodel))
            self.mailbox1.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto1.public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(search_request))

            envelope = self.mailbox1.inbox.get(block=True, timeout=5.0)
            search_result = OEFSerializer().decode(envelope.message)
            assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
            assert search_result.get("id") == self.request_id
            assert search_result.get("agents") == []

        @classmethod
        def teardown_class(cls):
            """Teardown the test."""
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
        cfp_bytes = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.CFP, query=Query([Constraint('something', ConstraintType('>', 1))]))
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
        # NOTE since the OEF SDK doesn't support the match accept, we have to use a fixed message id!
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

    def test_serialisation_fipa(self):
        """Tests a Value Error flag for wrong CFP query."""
        with pytest.raises(ValueError):
            msg = FIPAMessage(
                performative=FIPAMessage.Performative.CFP,
                message_id=0,
                dialogue_id=0,
                destination="publicKey",
                target=1)
            with mock.patch("aea.protocols.fipa.message.FIPAMessage.Performative")\
                    as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                assert FIPASerializer().encode(msg), "Raises Value Error"
        with pytest.raises(ValueError):
            msg.set("query", "Hello")
            assert FIPASerializer().encode(msg), "Query type is Supported!"
        with pytest.raises(ValueError):
            cfp_msg = FIPAMessage(message_id=0,
                                  dialogue_id=0,
                                  target=0,
                                  performative=FIPAMessage.Performative.CFP,
                                  query=b"hello")
            cfp_msg.set("query", "hello")
            fipa_msg = fipa_pb2.FIPAMessage()
            fipa_msg.message_id = cfp_msg.get("id")
            fipa_msg.dialogue_id = cfp_msg.get("dialogue_id")
            fipa_msg.target = cfp_msg.get("target")
            performative = fipa_pb2.FIPAMessage.CFP()
            fipa_msg.cfp.CopyFrom(performative)
            fipa_bytes = fipa_msg.SerializeToString()
            assert FIPASerializer().decode(fipa_bytes),\
                "The encoded message is a valid FIPA message."
        with pytest.raises(ValueError):
            cfp_msg = FIPAMessage(message_id=0,
                                  dialogue_id=0,
                                  target=0,
                                  performative=FIPAMessage.Performative.CFP,
                                  query=b"hello")
            with mock.patch("aea.protocols.fipa.message.FIPAMessage.Performative")\
                    as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                fipa_msg = fipa_pb2.FIPAMessage()
                fipa_msg.message_id = cfp_msg.get("id")
                fipa_msg.dialogue_id = cfp_msg.get("dialogue_id")
                fipa_msg.target = cfp_msg.get("target")
                performative = fipa_pb2.FIPAMessage.CFP()
                fipa_msg.cfp.CopyFrom(performative)
                fipa_bytes = fipa_msg.SerializeToString()
                assert FIPASerializer().decode(fipa_bytes),\
                    "The encoded message is a FIPA message"

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.mailbox1.disconnect()
        cls.mailbox2.disconnect()
