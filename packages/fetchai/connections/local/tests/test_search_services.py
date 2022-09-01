# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
# pylint: skip-file

import unittest.mock
from typing import cast

import pytest

from aea.common import Address
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)
from aea.mail.base import Envelope, EnvelopeContext, Message
from aea.multiplexer import InBox, Multiplexer
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.test_tools.mocks import AnyStringWith
from aea.test_tools.utils import wait_for_condition

from packages.fetchai.connections.local.connection import (
    LocalNode,
    OEFLocalConnection,
    OEF_LOCAL_NODE_ADDRESS,
    OEF_LOCAL_NODE_SEARCH_ADDRESS,
)
from packages.fetchai.connections.local.tests.test_misc import make_local_connection
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.dialogues import OefSearchDialogue
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


MAX_FLAKY_RERUNS = 3


class OefSearchDialogues(BaseOefSearchDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :param self_address: self address
        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return OefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


class TestNoValidDialogue:
    """Test that the search request returns an empty search result."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.public_key_1 = "public_key_1"
        cls.connection = make_local_connection(
            cls.address_1,
            cls.public_key_1,
            cls.node,
        )
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
        search_services_request.to = OEF_LOCAL_NODE_SEARCH_ADDRESS

        # the incorrect message cannot be sent into a dialogue, so this is omitted.

        search_services_request.sender = self.address_1
        envelope = Envelope(
            to=search_services_request.to,
            sender=search_services_request.sender,
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
        cls.public_key_1 = "public_key_1"
        cls.multiplexer = Multiplexer(
            [
                make_local_connection(
                    cls.address_1,
                    cls.public_key_1,
                    cls.node,
                )
            ]
        )

        cls.multiplexer.connect()
        cls.dialogues = OefSearchDialogues(cls.address_1)

    def test_empty_search_result(self):
        """Test that at the beginning, the search request returns an empty search result."""
        search_services_request, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=Query(constraints=[], model=None),
        )
        envelope = Envelope(
            to=search_services_request.to,
            sender=search_services_request.sender,
            message=search_services_request,
        )
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert (
            response_envelope.protocol_specification_id
            == OefSearchMessage.protocol_specification_id
        )
        search_result = cast(OefSearchMessage, response_envelope.message)
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

    def setup(self):
        """Set up the test."""
        self.node = LocalNode()
        self.node.start()

        self.address_1 = "address"
        self.public_key_1 = "public_key_1"
        self.multiplexer = Multiplexer(
            [
                make_local_connection(
                    self.address_1,
                    self.public_key_1,
                    self.node,
                )
            ]
        )

        self.multiplexer.connect()

        # register a service.
        self.dialogues = OefSearchDialogues(self.address_1)
        self.data_model = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=self.data_model
        )
        register_service_request, self.sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=register_service_request.to,
            sender=register_service_request.sender,
            message=register_service_request,
        )
        self.multiplexer.put(envelope)

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS
    )  # TODO: check reasons!. quite unstable test
    def test_not_empty_search_result(self):
        """Test that the search result contains one entry after a successful registration."""
        # build and send the request
        search_services_request, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=Query(constraints=[], model=self.data_model),
        )
        envelope = Envelope(
            to=search_services_request.to,
            sender=search_services_request.sender,
            message=search_services_request,
        )
        self.multiplexer.put(envelope)

        # check the result
        response_envelope = self.multiplexer.get(block=True, timeout=2.0)
        assert (
            response_envelope.protocol_specification_id
            == OefSearchMessage.protocol_specification_id
        )
        search_result = cast(OefSearchMessage, response_envelope.message)
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == (self.address_1,)

    def teardown(self):
        """Teardown the test."""
        self.multiplexer.disconnect()
        self.node.stop()


class TestUnregister:
    """Test that the unregister service results to Error Message."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.node = LocalNode()
        cls.node.start()

        cls.address_1 = "address_1"
        cls.public_key_1 = "public_key_1"
        cls.multiplexer1 = Multiplexer(
            [
                make_local_connection(
                    cls.address_1,
                    cls.public_key_1,
                    cls.node,
                )
            ]
        )
        cls.address_2 = "address_2"
        cls.public_key_2 = "public_key_2"
        cls.multiplexer2 = Multiplexer(
            [
                make_local_connection(
                    cls.address_2,
                    cls.public_key_2,
                    cls.node,
                )
            ]
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
        msg, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert (
            response_envelope.protocol_specification_id
            == OefSearchMessage.protocol_specification_id
        )
        response = cast(OefSearchMessage, response_envelope.message)
        response_dialogue = self.dialogues.update(response)
        assert response_dialogue == sending_dialogue
        assert response.performative == OefSearchMessage.Performative.OEF_ERROR

        msg, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)

        # Search for the registered service
        msg, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=Query([Constraint("foo", ConstraintType("==", 1))]),
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        search_result = cast(OefSearchMessage, response_envelope.message)
        response_dialogue = self.dialogues.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert len(search_result.agents) == 1

        # unregister the service
        msg, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)

        # the same query returns empty
        # Search for the register agent
        msg, sending_dialogue = self.dialogues.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=Query([Constraint("foo", ConstraintType("==", 1))]),
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)
        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        search_result = cast(OefSearchMessage, response_envelope.message)
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
        cls.public_key_1 = "public_key_1"
        cls.multiplexer1 = Multiplexer(
            [
                make_local_connection(
                    cls.address_1,
                    cls.public_key_1,
                    cls.node,
                )
            ]
        )

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.SELLER

        cls.dialogues = FipaDialogues(cls.address_1, role_from_first_message)

    @pytest.mark.asyncio
    async def test_messages(self):
        """Test that at the beginning, the search request returns an empty search result."""
        msg, sending_dialogue = self.dialogues.create(
            counterparty="some_agent",
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        with pytest.raises(ConnectionError):
            await make_local_connection(
                self.address_1,
                self.public_key_1,
                self.node,
            ).send(envelope)

        self.multiplexer1.connect()
        msg, sending_dialogue = self.dialogues.create(
            counterparty="this_address_does_not_exist",
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert (
            response_envelope.protocol_specification_id
            == DefaultMessage.protocol_specification_id
        )
        assert response_envelope.sender == OEF_LOCAL_NODE_ADDRESS
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
        cls.public_key_1 = "public_key_1"
        cls.address_2 = "multiplexer2"
        cls.public_key_2 = "public_key_2"
        cls.multiplexer1 = Multiplexer(
            [
                make_local_connection(
                    cls.address_1,
                    cls.public_key_1,
                    cls.node,
                )
            ]
        )
        cls.multiplexer2 = Multiplexer(
            [
                make_local_connection(
                    cls.address_2,
                    cls.public_key_2,
                    cls.node,
                )
            ]
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
        register_service_request, sending_dialogue = cls.dialogues1.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=register_service_request.to,
            sender=register_service_request.sender,
            message=register_service_request,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        cls.multiplexer1.put(envelope)
        wait_for_condition(lambda: len(cls.node.services) == 1, timeout=10)

        # register 'multiplexer2' as a service 'barfoo'.
        cls.data_model_barfoo = DataModel(
            "barfoo",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=cls.data_model_barfoo
        )
        register_service_request, sending_dialogue = cls.dialogues2.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=register_service_request.to,
            sender=register_service_request.sender,
            message=register_service_request,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )

        cls.multiplexer2.put(envelope)
        wait_for_condition(lambda: len(cls.node.services) == 2, timeout=10)

        # unregister multiplexer1
        data_model = DataModel(
            "foobar",
            attributes=[Attribute("foo", int, True), Attribute("bar", str, True)],
        )
        service_description = Description(
            {"foo": 1, "bar": "baz"}, data_model=data_model
        )
        msg, sending_dialogue = cls.dialogues1.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        cls.multiplexer1.put(envelope)
        # ensure one service stays registered
        wait_for_condition(lambda: len(cls.node.services) == 1, timeout=10)

    def test_filtered_search_result(self):
        """Test that the search result contains only the entries matching the query."""
        # build and send the request
        search_services_request, sending_dialogue = self.dialogues1.create(
            counterparty=OEF_LOCAL_NODE_SEARCH_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=Query(constraints=[], model=self.data_model_barfoo),
        )
        envelope = Envelope(
            to=search_services_request.to,
            sender=search_services_request.sender,
            message=search_services_request,
            context=EnvelopeContext(connection_id=OEFLocalConnection.connection_id),
        )
        self.multiplexer1.put(envelope)

        # check the result
        response_envelope = InBox(self.multiplexer1).get(block=True, timeout=5.0)
        search_result = cast(OefSearchMessage, response_envelope.message)
        response_dialogue = self.dialogues1.update(search_result)
        assert response_dialogue == sending_dialogue
        assert search_result.performative == OefSearchMessage.Performative.SEARCH_RESULT
        assert search_result.agents == (self.address_2,), self.node.services

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        cls.node.stop()
