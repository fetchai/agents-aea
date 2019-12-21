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

"""This module contains the tests for the search feature of the local OEF node."""
import time

import pytest

from aea.configurations.base import ConnectionConfig
from aea.helpers.search.models import Query, DataModel, Description, Constraint, ConstraintType
from aea.mail.base import Envelope, AEAConnectionError, Multiplexer, InBox
from packages.connections.local.connection import LocalNode, OEFLocalConnection
from packages.protocols.fipa.message import FIPAMessage
from packages.protocols.fipa.serialization import FIPASerializer
from packages.protocols.oef.message import OEFMessage
from packages.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer


class TestEmptySearch:
    """Test that the search request returns an empty search result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.multiplexer = Multiplexer([OEFLocalConnection(cls.address_1, cls.node)])

        cls.multiplexer.connect()

    def test_empty_search_result(self):
        """Test that at the beginning, the search request returns an empty search result."""
        request_id = 1
        query = Query(constraints=[], model=None)

        # build and send the request
        search_services_request = OEFMessage(type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=query)
        msg_bytes = OEFSerializer().encode(search_services_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.to == self.address_1
        assert response_envelope.sender == DEFAULT_OEF
        search_result = OEFSerializer().decode(response_envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert search_result.get("agents") == []

        # build and send the request
        search_agents_request = OEFMessage(type=OEFMessage.Type.SEARCH_AGENTS, id=request_id, query=query)
        msg_bytes = OEFSerializer().encode(search_agents_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        search_result = OEFSerializer().decode(response_envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert search_result.get("agents") == []

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer.disconnect()
        cls.node.stop()


class TestSimpleSearchResult:
    """Test that a simple search result return the expected result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address"
        cls.multiplexer = Multiplexer([OEFLocalConnection(cls.address_1, cls.node)])

        cls.multiplexer.connect()

        # register a service.
        request_id = 1
        service_id = ''
        cls.data_model = DataModel("foobar", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=cls.data_model)
        register_service_request = OEFMessage(type=OEFMessage.Type.REGISTER_SERVICE, id=request_id,
                                              service_description=service_description, service_id=service_id)
        msg_bytes = OEFSerializer().encode(register_service_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=cls.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        cls.multiplexer.put(envelope)

    def test_not_empty_search_result(self):
        """Test that the search result contains one entry after a successful registration."""
        request_id = 1
        query = Query(constraints=[], model=self.data_model)

        # build and send the request
        search_services_request = OEFMessage(type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=query)
        msg_bytes = OEFSerializer().encode(search_services_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.to == self.address_1
        assert response_envelope.sender == DEFAULT_OEF
        search_result = OEFSerializer().decode(response_envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert search_result.get("agents") == [self.address_1]

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer.disconnect()
        cls.node.stop()


class TestUnregister:
    """Test that the unregister service results to Error Message."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.multiplexer1 = Multiplexer([OEFLocalConnection(cls.address_1, cls.node)])
        cls.address_2 = "address_2"
        cls.multiplexer2 = Multiplexer([OEFLocalConnection(cls.address_2, cls.node)])
        cls.multiplexer1.connect()
        cls.multiplexer2.connect()

    def test_unregister_service_result(self):
        """Test that at the beginning, the search request returns an empty search result."""
        data_model = DataModel("foobar", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=data_model)
        msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_SERVICE, id=0, service_description=service_description,
                         service_id="Test_service")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert result.get("type") == OEFMessage.Type.OEF_ERROR

        msg = OEFMessage(type=OEFMessage.Type.REGISTER_SERVICE, id=0, service_description=service_description,
                         service_id="Test_Service")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        # Search for the register agent
        msg = OEFMessage(type=OEFMessage.Type.SEARCH_AGENTS, id=0, query=Query([Constraint("foo", ConstraintType("==", 1))]))
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert len(result.get("agents")) == 1

        # unregister the service
        data_model = DataModel("foobar", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=data_model)
        msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_SERVICE, id=0, service_description=service_description,
                         service_id="Test_service")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        # the same query returns empty
        # Search for the register agent
        msg = OEFMessage(type=OEFMessage.Type.SEARCH_AGENTS, id=0, query=Query([Constraint("foo", ConstraintType("==", 1))]))
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert len(result.get("agents")) == 0

    def test_search_agent(self):
        """Test the registered agents, we will not find any."""
        data_model = DataModel("foobar", attributes=[])
        agent_description = Description({"foo": 1, "bar": "baz"}, data_model=data_model)
        query = Query(constraints=[], model=data_model)

        # Register an agent
        msg = OEFMessage(type=OEFMessage.Type.REGISTER_AGENT, id=0, agent_description=agent_description,
                         agent_id="Test_agent")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        time.sleep(0.1)

        # Search for the register agent
        msg = OEFMessage(type=OEFMessage.Type.SEARCH_AGENTS, id=0, query=query)
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_2, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer2.put(envelope)

        # check the result
        response_envelope = self.multiplexer2.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert len(result.get("agents")) == 1, "There are registered agents!"

        # Send unregister message.
        msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_AGENT, id=0, agent_description=agent_description,
                         agent_id="Test_agent")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        time.sleep(0.1)

        # Trigger error message.
        msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_AGENT, id=0, agent_description=agent_description,
                         agent_id="Unknown_Agent")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert result.get("type") == OEFMessage.Type.OEF_ERROR

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        cls.node.stop()


class TestAgentMessage:
    """Test the the OEF will return Dialogue Error if it doesn't know the agent address."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.multiplexer1 = Multiplexer([OEFLocalConnection(cls.address_1, cls.node)])

    @pytest.mark.asyncio
    async def test_messages(self):
        """Test that at the beginning, the search request returns an empty search result."""
        msg = FIPAMessage((str(0), ''), 0, 0, FIPAMessage.Performative.CFP, query=None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        with pytest.raises(AEAConnectionError):
            await OEFLocalConnection(self.address_1, self.node).send(envelope)

        self.multiplexer1.connect()
        msg = FIPAMessage((str(0), str(1)), 0, 0, FIPAMessage.Performative.CFP, query=None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="this_address_does_not_exist",
                            sender=self.address_1, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.sender == DEFAULT_OEF
        result = OEFSerializer().decode(response_envelope.message)
        assert result.get("type") == OEFMessage.Type.DIALOGUE_ERROR

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.node.stop()


class TestOEFConnectionFromJson:
    """Test the the OEF will return a connection after reading the .json file."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()
        cls.address_1 = "address_1"

    def test_from_config(self):
        """Test the configuration loading."""
        con = OEFLocalConnection.from_config(address="pk", connection_configuration=ConnectionConfig())
        assert not con.connection_status.is_connected, "We are connected..."

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.node.stop()


class TestFilteredSearchResult:
    """Test that the query system of the search gives the expected result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "multiplexer1"
        cls.address_2 = "multiplexer2"
        cls.multiplexer1 = Multiplexer([OEFLocalConnection(cls.address_1, cls.node)])
        cls.multiplexer2 = Multiplexer([OEFLocalConnection(cls.address_2, cls.node)])
        cls.multiplexer1.connect()
        cls.multiplexer2.connect()

        # register 'multiplexer1' as a service 'foobar'.
        request_id = 1
        service_id = ''
        cls.data_model_foobar = DataModel("foobar", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=cls.data_model_foobar)
        register_service_request = OEFMessage(type=OEFMessage.Type.REGISTER_SERVICE, id=request_id,
                                              service_description=service_description, service_id=service_id)
        msg_bytes = OEFSerializer().encode(register_service_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=cls.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        cls.multiplexer1.put(envelope)

        time.sleep(1.0)

        # register 'multiplexer2' as a service 'barfoo'.
        cls.data_model_barfoo = DataModel("barfoo", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=cls.data_model_barfoo)
        register_service_request = OEFMessage(type=OEFMessage.Type.REGISTER_SERVICE, id=request_id,
                                              service_description=service_description, service_id=service_id)
        msg_bytes = OEFSerializer().encode(register_service_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=cls.address_2, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        cls.multiplexer2.put(envelope)

        # unregister multiplexer1
        data_model = DataModel("foobar", attributes=[])
        service_description = Description({"foo": 1, "bar": "baz"}, data_model=data_model)
        msg = OEFMessage(type=OEFMessage.Type.UNREGISTER_SERVICE, id=0, service_description=service_description,
                         service_id="Test_service")
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=DEFAULT_OEF, sender=cls.address_1, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        cls.multiplexer1.put(envelope)

    def test_filtered_search_result(self):
        """Test that the search result contains only the entries matching the query."""
        request_id = 1
        query = Query(constraints=[], model=self.data_model_barfoo)

        # build and send the request
        search_services_request = OEFMessage(type=OEFMessage.Type.SEARCH_SERVICES, id=request_id, query=query)
        msg_bytes = OEFSerializer().encode(search_services_request)
        envelope = Envelope(to=DEFAULT_OEF, sender=self.address_1, protocol_id=OEFMessage.protocol_id,
                            message=msg_bytes)
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = InBox(self.multiplexer1).get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OEFMessage.protocol_id
        assert response_envelope.to == self.address_1
        assert response_envelope.sender == DEFAULT_OEF
        search_result = OEFSerializer().decode(response_envelope.message)
        assert search_result.get("type") == OEFMessage.Type.SEARCH_RESULT
        assert search_result.get("agents") == [self.address_2]

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        cls.node.stop()
