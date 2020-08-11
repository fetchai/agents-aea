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
import copy
import time
import unittest.mock
from typing import Optional, cast

import pytest

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)
from aea.mail.base import AEAConnectionError, Envelope
from aea.multiplexer import InBox, Multiplexer
from aea.protocols.default.message import DefaultMessage

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.common.mocks import AnyStringWith
from tests.common.utils import wait_for_condition
from tests.conftest import MAX_FLAKY_RERUNS, _make_local_connection


class TestNoValidDialogue:
    """Test that the search request returns an empty search result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.connection = _make_local_connection(cls.address_1, cls.node,)
        cls.multiplexer = Multiplexer([cls.connection])

        cls.multiplexer.connect()
        cls.dialogues = OefSearchDialogues(cls.address_1)

    @pytest.mark.asyncio
    async def test_wrong_dialogue(self):
        """Test that at the beginning, the search request returns an empty search result."""
        query = Query(
            constraints=[Constraint("foo", ConstraintType("==", 1))], model=None
        )

        # build and send the request
        search_services_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            message_id=2,
            target=1,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=query,
        )
        search_services_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], self.dialogues.update(search_services_request)
        )
        assert sending_dialogue is None
        search_services_request.sender = self.address_1
        envelope = Envelope(
            to=search_services_request.counterparty,
            sender=search_services_request.sender,
            protocol_id=search_services_request.protocol_id,
            message=search_services_request,
        )
        with unittest.mock.patch.object(
            self.node, "_handle_oef_message", side_effect=self.node._handle_oef_message
        ) as mock_handle:
            with unittest.mock.patch.object(self.node.logger, "warning") as mock_logger:
                self.multiplexer.put(envelope)
                wait_for_condition(lambda: mock_handle.called, timeout=1.0)
                mock_logger.assert_any_call(
                    AnyStringWith("Could not create dialogue for message=")
                )

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer.disconnect()
        cls.node.stop()


class TestEmptySearch:
    """Test that the search request returns an empty search result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.multiplexer = Multiplexer(
            [_make_local_connection(cls.address_1, cls.node,)]
        )

        cls.multiplexer.connect()
        cls.dialogues = OefSearchDialogues(cls.address_1)

    def test_empty_search_result(self):
        """Test that at the beginning, the search request returns an empty search result."""
        query = Query(constraints=[], model=None)

        # build and send the request
        search_services_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=query,
        )
        search_services_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], self.dialogues.update(search_services_request)
        )
        assert sending_dialogue is not None
        envelope = Envelope(
            to=search_services_request.counterparty,
            sender=search_services_request.sender,
            protocol_id=search_services_request.protocol_id,
            message=search_services_request,
        )
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert response_envelope.protocol_id == OefSearchMessage.protocol_id
        search_result_orig = cast(OefSearchMessage, response_envelope.message)
        search_result = copy.copy(search_result_orig)
        search_result.is_incoming = True
        search_result.counterparty = search_result_orig.sender
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == ()

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
        cls.multiplexer = Multiplexer(
            [_make_local_connection(cls.address_1, cls.node,)]
        )

        cls.multiplexer.connect()

        # register a service.
        cls.dialogues = OefSearchDialogues(cls.address_1)
        cls.data_model = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=cls.data_model
        )
        register_service_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=cls.dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        register_service_request.counterparty = str(OEFLocalConnection.connection_id)
        cls.sending_dialogue = cast(
            Optional[OefSearchDialogue], cls.dialogues.update(register_service_request)
        )
        assert cls.sending_dialogue is not None
        envelope = Envelope(
            to=register_service_request.counterparty,
            sender=register_service_request.sender,
            protocol_id=register_service_request.protocol_id,
            message=register_service_request,
        )
        cls.multiplexer.put(envelope)

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS
    )  # TODO: check reasons!. quite unstable test
    def test_not_empty_search_result(self):
        """Test that the search result contains one entry after a successful registration."""
        query = Query(constraints=[], model=self.data_model)

        # build and send the request
        search_services_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=query,
        )
        search_services_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], self.dialogues.update(search_services_request)
        )
        assert sending_dialogue is not None
        envelope = Envelope(
            to=search_services_request.counterparty,
            sender=search_services_request.sender,
            protocol_id=search_services_request.protocol_id,
            message=search_services_request,
        )
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert response_envelope.protocol_id == OefSearchMessage.protocol_id
        search_result_orig = cast(OefSearchMessage, response_envelope.message)
        search_result = copy.copy(search_result_orig)
        search_result.is_incoming = True
        search_result.counterparty = search_result_orig.sender
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == (self.address_1,)

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
        cls.multiplexer1 = Multiplexer(
            [_make_local_connection(cls.address_1, cls.node,)]
        )
        cls.address_2 = "address_2"
        cls.multiplexer2 = Multiplexer(
            [_make_local_connection(cls.address_2, cls.node,)]
        )
        cls.multiplexer1.connect()
        cls.multiplexer2.connect()
        cls.dialogues = OefSearchDialogues(cls.address_1)

    def test_unregister_service_result(self):
        """Test that at the beginning, the search request returns an empty search result."""
        data_model = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model
        )
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == OefSearchMessage.protocol_id
        response_orig = cast(OefSearchMessage, response_envelope.message)
        response = copy.copy(response_orig)
        response.is_incoming = True
        response.counterparty = response_orig.sender
        response_dialogue = self.dialogues.update(response)
        assert response_dialogue == sending_dialogue
        assert response.performative == OefSearchMessage.Performative.OEF_ERROR

        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)

        # Search for the registered service
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=Query([Constraint("foo", ConstraintType("==", 1))]),
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        search_result_orig = cast(OefSearchMessage, response_envelope.message)
        search_result = copy.copy(search_result_orig)
        search_result.is_incoming = True
        search_result.counterparty = search_result_orig.sender
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert len(search_result.agents) == 1

        # unregister the service
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)

        # the same query returns empty
        # Search for the register agent
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=Query([Constraint("foo", ConstraintType("==", 1))]),
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        search_result_orig = cast(OefSearchMessage, response_envelope.message)
        search_result = copy.copy(search_result_orig)
        search_result.is_incoming = True
        search_result.counterparty = search_result_orig.sender
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == ()

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
        cls.multiplexer1 = Multiplexer(
            [_make_local_connection(cls.address_1, cls.node,)]
        )
        cls.dialogues = FipaDialogues(cls.address_1)

    @pytest.mark.asyncio
    async def test_messages(self):
        """Test that at the beginning, the search request returns an empty search result."""
        msg = FipaMessage(
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[FipaDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        with pytest.raises(AEAConnectionError):
            await _make_local_connection(self.address_1, self.node,).send(envelope)

        self.multiplexer1.connect()
        msg = FipaMessage(
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        msg.counterparty = "this_address_does_not_exist"
        sending_dialogue = cast(Optional[FipaDialogue], self.dialogues.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert response_envelope.protocol_id == DefaultMessage.protocol_id
        assert response_envelope.sender == str(OEFLocalConnection.connection_id)
        result = response_envelope.message
        assert result.performative == DefaultMessage.Performative.ERROR

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
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
        cls.multiplexer1 = Multiplexer(
            [_make_local_connection(cls.address_1, cls.node,)]
        )
        cls.multiplexer2 = Multiplexer(
            [_make_local_connection(cls.address_2, cls.node,)]
        )
        cls.multiplexer1.connect()
        cls.multiplexer2.connect()
        cls.dialogues1 = OefSearchDialogues(cls.address_1)
        cls.dialogues2 = OefSearchDialogues(cls.address_2)

        # register 'multiplexer1' as a service 'foobar'.
        cls.data_model_foobar = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=cls.data_model_foobar
        )
        register_service_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=cls.dialogues1.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        register_service_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], cls.dialogues1.update(register_service_request)
        )
        assert sending_dialogue is not None
        envelope = Envelope(
            to=register_service_request.counterparty,
            sender=register_service_request.sender,
            protocol_id=register_service_request.protocol_id,
            message=register_service_request,
        )
        cls.multiplexer1.put(envelope)

        time.sleep(1.0)

        # register 'multiplexer2' as a service 'barfoo'.
        cls.data_model_barfoo = DataModel(
            "barfoo",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=cls.data_model_barfoo
        )
        register_service_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=cls.dialogues1.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        register_service_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], cls.dialogues2.update(register_service_request)
        )
        assert sending_dialogue is not None
        envelope = Envelope(
            to=register_service_request.counterparty,
            sender=register_service_request.sender,
            protocol_id=register_service_request.protocol_id,
            message=register_service_request,
        )
        cls.multiplexer2.put(envelope)

        # unregister multiplexer1
        data_model = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model
        )
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=cls.dialogues1.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        msg.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(Optional[OefSearchDialogue], cls.dialogues1.update(msg))
        assert sending_dialogue is not None
        envelope = Envelope(
            to=msg.counterparty,
            sender=msg.sender,
            protocol_id=msg.protocol_id,
            message=msg,
        )
        cls.multiplexer1.put(envelope)

    def test_filtered_search_result(self):
        """Test that the search result contains only the entries matching the query."""
        query = Query(constraints=[], model=self.data_model_barfoo)

        # build and send the request
        search_services_request = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.dialogues1.new_self_initiated_dialogue_reference(),
            query=query,
        )
        search_services_request.counterparty = str(OEFLocalConnection.connection_id)
        sending_dialogue = cast(
            Optional[OefSearchDialogue], self.dialogues1.update(search_services_request)
        )
        assert sending_dialogue is not None
        envelope = Envelope(
            to=search_services_request.counterparty,
            sender=search_services_request.sender,
            protocol_id=search_services_request.protocol_id,
            message=search_services_request,
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = InBox(self.multiplexer1).get(block=True, timeout=5.0)
        search_result_orig = cast(OefSearchMessage, response_envelope.message)
        search_result = copy.copy(search_result_orig)
        search_result.is_incoming = True
        search_result.counterparty = search_result_orig.sender
        response_dialogue = self.dialogues1.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == (self.address_2,)

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        cls.node.stop()
