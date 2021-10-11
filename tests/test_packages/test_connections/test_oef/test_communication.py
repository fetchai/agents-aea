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
import asyncio
import logging
import sys
import time
import unittest
import warnings
from contextlib import suppress
from typing import cast
from unittest import mock
from unittest.mock import patch

import pytest
from oef.messages import OEFErrorOperation
from oef.query import ConstraintExpr

from aea.common import Address
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    ConstraintTypes,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.mail.base import Envelope
from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.multiplexer import Multiplexer
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.oef.connection import OEFObjectTranslator
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa import fipa_pb2
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.dialogues import OefSearchDialogue
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.common.utils import UseOef
from tests.conftest import (
    FETCHAI_ADDRESS_ONE,
    FETCHAI_ADDRESS_TWO,
    _make_oef_connection,
)


logger = logging.getLogger(__name__)

SOME_SKILL_ID = "some/skill:0.1.0"

DUMMY_PUBLIC_KEY = "some_public_key"


class OefSearchDialogues(BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, self_address: str) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
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


class TestDefault(UseOef):
    """Test that the default protocol is correctly implemented by the OEF channel."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.connection = _make_oef_connection(
            FETCHAI_ADDRESS_ONE, DUMMY_PUBLIC_KEY, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.multiplexer = Multiplexer(
            [cls.connection], protocols=[FipaMessage, DefaultMessage]
        )
        cls.multiplexer.connect()

    def test_send_message(self):
        """Test that a default byte message can be sent correctly."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        self.multiplexer.put(
            Envelope(to=FETCHAI_ADDRESS_ONE, sender=FETCHAI_ADDRESS_ONE, message=msg,)
        )
        recv_msg = self.multiplexer.get(block=True, timeout=3.0)
        assert recv_msg is not None

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.multiplexer.disconnect()


class TestOEF(UseOef):
    """Test that the OEF protocol is correctly implemented by the OEF channel."""

    class TestSearchServices:
        """Tests related to service search functionality."""

        def setup(self):
            """Set the test up."""
            self.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE,
                DUMMY_PUBLIC_KEY,
                oef_addr="127.0.0.1",
                oef_port=10000,
            )
            self.multiplexer = Multiplexer(
                [self.connection], protocols=[FipaMessage, DefaultMessage]
            )
            self.multiplexer.connect()
            self.oef_search_dialogues = OefSearchDialogues(SOME_SKILL_ID)

        def test_search_services_with_query_without_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has no data model.
            """
            search_query_empty_model = Query(
                [Constraint("foo", ConstraintType("==", "bar"))], model=None
            )
            oef_search_request, sending_dialogue = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=search_query_empty_model,
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = self.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue is not None
            assert oef_search_dialogue == sending_dialogue
            assert oef_search_response.agents == ()

        def test_search_services_with_query_with_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has a simple data model.
            """
            data_model = DataModel("foobar", [Attribute("foo", str, True)])
            search_query = Query(
                [Constraint("foo", ConstraintType("==", "bar"))], model=data_model
            )
            oef_search_request, sending_dialogue = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=search_query,
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = self.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue is not None
            assert oef_search_dialogue == sending_dialogue
            assert oef_search_response.agents == ()

        def test_search_services_with_distance_query(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has a simple data model.
            """
            tour_eiffel = Location(48.8581064, 2.29447)
            attribute = Attribute("latlon", Location, True)
            data_model = DataModel("geolocation", [attribute])
            search_query = Query(
                [
                    Constraint(
                        attribute.name, ConstraintType("distance", (tour_eiffel, 1.0))
                    )
                ],
                model=data_model,
            )
            oef_search_request, sending_dialogue = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=search_query,
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )
            envelope = self.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = self.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue is not None
            assert oef_search_dialogue == sending_dialogue
            assert oef_search_response.agents == ()

        def teardown(self):
            """Teardowm the test."""
            self.multiplexer.disconnect()

    class TestRegisterService:
        """Tests related to service registration functionality."""

        @classmethod
        def setup_class(cls):
            """Set the test up."""
            cls.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE,
                DUMMY_PUBLIC_KEY,
                oef_addr="127.0.0.1",
                oef_port=10000,
            )
            cls.multiplexer = Multiplexer(
                [cls.connection], protocols=[FipaMessage, DefaultMessage]
            )
            cls.multiplexer.connect()
            cls.oef_search_dialogues = OefSearchDialogues(SOME_SKILL_ID)

        def test_register_service(self):
            """Test that a register service request works correctly."""
            foo_datamodel = DataModel(
                "foo", [Attribute("bar", int, True, "A bar attribute.")]
            )
            desc = Description({"bar": 1}, data_model=foo_datamodel)
            oef_search_registration, _ = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=desc,
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_registration.to,
                    sender=oef_search_registration.sender,
                    message=oef_search_registration,
                )
            )
            time.sleep(1)

            oef_search_request, sending_dialogue_2 = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))], model=foo_datamodel
                ),
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )
            envelope = self.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = self.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue == sending_dialogue_2
            assert oef_search_response.agents == (
                FETCHAI_ADDRESS_ONE,
            ), "search_result.agents != [FETCHAI_ADDRESS_ONE] FAILED in test_oef/test_communication.py"

        @classmethod
        def teardown_class(cls):
            """Teardowm the test."""
            cls.multiplexer.disconnect()

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
            cls.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE,
                DUMMY_PUBLIC_KEY,
                oef_addr="127.0.0.1",
                oef_port=10000,
            )
            cls.multiplexer = Multiplexer(
                [cls.connection], protocols=[FipaMessage, DefaultMessage]
            )
            cls.multiplexer.connect()
            cls.oef_search_dialogues = OefSearchDialogues(SOME_SKILL_ID)

            cls.foo_datamodel = DataModel(
                "foo", [Attribute("bar", int, True, "A bar attribute.")]
            )
            cls.desc = Description({"bar": 1}, data_model=cls.foo_datamodel)
            oef_search_registration, _ = cls.oef_search_dialogues.create(
                counterparty=str(cls.connection.connection_id),
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=cls.desc,
            )

            cls.multiplexer.put(
                Envelope(
                    to=oef_search_registration.to,
                    sender=oef_search_registration.sender,
                    message=oef_search_registration,
                )
            )

            time.sleep(1.0)

            (oef_search_request, sending_dialogue_2,) = cls.oef_search_dialogues.create(
                counterparty=str(cls.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))],
                    model=cls.foo_datamodel,
                ),
            )
            cls.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )
            envelope = cls.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = cls.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue == sending_dialogue_2
            assert oef_search_response.agents == (
                FETCHAI_ADDRESS_ONE,
            ), "search_result.agents != [FETCHAI_ADDRESS_ONE] FAILED in test_oef/test_communication.py"

        def test_unregister_service(self):
            """Test that an unregister service request works correctly.

            Steps:
            2. unregister the service
            3. search for that service
            4. assert that no result is found.
            """
            oef_search_deregistration, _ = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                service_description=self.desc,
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_deregistration.to,
                    sender=oef_search_deregistration.sender,
                    message=oef_search_deregistration,
                )
            )

            time.sleep(1.0)

            oef_search_request, sending_dialogue_2 = self.oef_search_dialogues.create(
                counterparty=str(self.connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))],
                    model=self.foo_datamodel,
                ),
            )
            self.multiplexer.put(
                Envelope(
                    to=oef_search_request.to,
                    sender=oef_search_request.sender,
                    message=oef_search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            oef_search_response = envelope.message
            oef_search_dialogue = self.oef_search_dialogues.update(oef_search_response)
            assert (
                oef_search_response.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert oef_search_dialogue == sending_dialogue_2
            assert oef_search_response.agents == ()

        @classmethod
        def teardown_class(cls):
            """Teardown the test."""
            cls.multiplexer.disconnect()


class TestFIPA(UseOef):
    """Test that the FIPA protocol is correctly implemented by the OEF channel."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.connection1 = _make_oef_connection(
            FETCHAI_ADDRESS_ONE, DUMMY_PUBLIC_KEY, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.connection2 = _make_oef_connection(
            FETCHAI_ADDRESS_TWO, DUMMY_PUBLIC_KEY, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.multiplexer1 = Multiplexer(
            [cls.connection1], protocols=[FipaMessage, DefaultMessage]
        )
        cls.multiplexer2 = Multiplexer(
            [cls.connection2], protocols=[FipaMessage, DefaultMessage]
        )
        cls.multiplexer1.connect()
        cls.multiplexer2.connect()

    def test_cfp(self):
        """Test that a CFP can be sent correctly."""
        cfp_message = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_message.to = FETCHAI_ADDRESS_TWO
        cfp_message.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(to=cfp_message.to, sender=cfp_message.sender, message=cfp_message,)
        )
        envelope = self.multiplexer2.get(block=True, timeout=5.0)
        expected_cfp_message = FipaMessage.serializer.decode(envelope.message)
        expected_cfp_message.to = cfp_message.to
        expected_cfp_message.sender = cfp_message.sender
        assert expected_cfp_message == cfp_message

        cfp_none = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_none.to = FETCHAI_ADDRESS_TWO
        cfp_none.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(to=cfp_none.to, sender=cfp_none.sender, message=cfp_none,)
        )
        envelope = self.multiplexer2.get(block=True, timeout=5.0)
        expected_cfp_none = FipaMessage.serializer.decode(envelope.message)
        expected_cfp_none.to = cfp_none.to
        expected_cfp_none.sender = cfp_none.sender
        assert expected_cfp_none == cfp_none

    def test_propose(self):
        """Test that a Propose can be sent correctly."""
        propose_empty = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo": "bar"}),
        )
        propose_empty.to = FETCHAI_ADDRESS_TWO
        propose_empty.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(
                to=propose_empty.to, sender=propose_empty.sender, message=propose_empty,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_propose_empty = FipaMessage.serializer.decode(envelope.message)
        expected_propose_empty.to = propose_empty.to
        expected_propose_empty.sender = propose_empty.sender
        assert expected_propose_empty == propose_empty

        propose_descriptions = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description(
                {"foo": "bar"}, DataModel("foobar", [Attribute("foo", str, True)])
            ),
        )

        propose_descriptions.to = FETCHAI_ADDRESS_TWO
        propose_descriptions.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(
                to=propose_descriptions.to,
                sender=propose_descriptions.sender,
                message=propose_descriptions,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_propose_descriptions = FipaMessage.serializer.decode(envelope.message)
        expected_propose_descriptions.to = propose_descriptions.to
        expected_propose_descriptions.sender = propose_descriptions.sender
        assert expected_propose_descriptions == propose_descriptions

    def test_accept(self):
        """Test that an Accept can be sent correctly."""
        accept = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        accept.to = FETCHAI_ADDRESS_TWO
        accept.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(to=accept.to, sender=accept.sender, message=accept,)
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_accept = FipaMessage.serializer.decode(envelope.message)
        expected_accept.to = accept.to
        expected_accept.sender = accept.sender
        assert expected_accept == accept

    def test_match_accept(self):
        """Test that a match accept can be sent correctly."""
        # NOTE since the OEF SDK doesn't support the match accept, we have to use a fixed message id!
        match_accept = FipaMessage(
            message_id=4,
            dialogue_reference=(str(0), ""),
            target=3,
            performative=FipaMessage.Performative.MATCH_ACCEPT,
        )
        match_accept.to = FETCHAI_ADDRESS_TWO
        match_accept.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(
                to=match_accept.to, sender=match_accept.sender, message=match_accept,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_match_accept = FipaMessage.serializer.decode(envelope.message)
        expected_match_accept.to = match_accept.to
        expected_match_accept.sender = match_accept.sender
        assert expected_match_accept == match_accept

    def test_decline(self):
        """Test that a Decline can be sent correctly."""
        decline = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.DECLINE,
        )
        decline.to = FETCHAI_ADDRESS_TWO
        decline.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(to=decline.to, sender=decline.sender, message=decline,)
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_decline = FipaMessage.serializer.decode(envelope.message)
        expected_decline.to = decline.to
        expected_decline.sender = decline.sender
        assert expected_decline == decline

    def test_match_accept_w_inform(self):
        """Test that a match accept with inform can be sent correctly."""
        match_accept_w_inform = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"address": "my_address"},
        )
        match_accept_w_inform.to = FETCHAI_ADDRESS_TWO
        match_accept_w_inform.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(
                to=match_accept_w_inform.to,
                sender=match_accept_w_inform.sender,
                message=match_accept_w_inform,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_match_accept_w_inform = FipaMessage.serializer.decode(envelope.message)
        returned_match_accept_w_inform.to = match_accept_w_inform.to
        returned_match_accept_w_inform.sender = match_accept_w_inform.sender
        assert returned_match_accept_w_inform == match_accept_w_inform

    def test_accept_w_inform(self):
        """Test that an accept with address can be sent correctly."""
        accept_w_inform = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            info={"address": "my_address"},
        )
        accept_w_inform.to = FETCHAI_ADDRESS_TWO
        accept_w_inform.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(
                to=accept_w_inform.to,
                sender=accept_w_inform.sender,
                message=accept_w_inform,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_accept_w_inform = FipaMessage.serializer.decode(envelope.message)
        returned_accept_w_inform.to = accept_w_inform.to
        returned_accept_w_inform.sender = accept_w_inform.sender
        assert returned_accept_w_inform == accept_w_inform

    def test_inform(self):
        """Test that an inform can be sent correctly."""
        payload = {"foo": "bar"}
        inform = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.INFORM,
            info=payload,
        )
        inform.to = FETCHAI_ADDRESS_TWO
        inform.sender = FETCHAI_ADDRESS_ONE
        self.multiplexer1.put(
            Envelope(to=inform.to, sender=inform.sender, message=inform,)
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_inform = FipaMessage.serializer.decode(envelope.message)
        returned_inform.to = inform.to
        returned_inform.sender = inform.sender
        assert returned_inform == inform

    def test_serialisation_fipa(self):
        """Tests a Value Error flag for wrong CFP query."""

        def _encode_fipa_cfp(msg: FipaMessage) -> bytes:
            """Helper function to serialize FIPA CFP message."""
            message_pb = ProtobufMessage()
            dialogue_message_pb = DialogueMessage()
            fipa_msg = fipa_pb2.FipaMessage()

            dialogue_message_pb.message_id = msg.message_id
            dialogue_reference = msg.dialogue_reference
            dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
            dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
            dialogue_message_pb.target = msg.target

            performative = fipa_pb2.FipaMessage.Cfp_Performative()  # type: ignore
            # the following are commented to make the decoding to fail.
            # query = msg.query  # noqa: E800
            # Query.encode(performative.query, query)  # noqa: E800
            fipa_msg.cfp.CopyFrom(performative)
            dialogue_message_pb.content = fipa_msg.SerializeToString()

            message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
            fipa_bytes = message_pb.SerializeToString()
            return fipa_bytes

        with pytest.raises(ValueError):
            msg = FipaMessage(
                performative=FipaMessage.Performative.CFP,
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            )
            with mock.patch.object(
                FipaMessage, "Performative"
            ) as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                FipaMessage.serializer.encode(msg), "Raises Value Error"
        # with pytest.raises(EOFError):  # noqa: E800
        #     cfp_msg = FipaMessage(  # noqa: E800
        #         message_id=1,  # noqa: E800
        #         dialogue_reference=(str(0), ""),  # noqa: E800
        #         target=0,  # noqa: E800
        #         performative=FipaMessage.Performative.CFP,  # noqa: E800
        #         query=Query([Constraint("something", ConstraintType(">", 1))]),  # noqa: E800
        #     )  # noqa: E800
        #     cfp_msg.set("query", "hello")  # noqa: E800
        #     fipa_bytes = _encode_fipa_cfp(cfp_msg)  # noqa: E800

        #     # The encoded message is not a valid FIPA message.  # noqa: E800
        #     FipaMessage.serializer.decode(fipa_bytes)  # noqa: E800
        with pytest.raises(ValueError):
            cfp_msg = FipaMessage(
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
                performative=FipaMessage.Performative.CFP,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            )
            with mock.patch.object(
                FipaMessage, "Performative"
            ) as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                fipa_bytes = _encode_fipa_cfp(cfp_msg)
                # The encoded message is not a FIPA message
                FipaMessage.serializer.decode(fipa_bytes)

    def test_on_oef_error(self):
        """Test the oef error."""
        oef_connection = self.multiplexer1.connections[0]
        oef_channel = oef_connection.channel

        oef_channel.oef_msg_id += 1
        dialogue_reference = ("1", "")
        query = Query(
            constraints=[Constraint("foo", ConstraintType("==", "bar"))], model=None,
        )
        dialogues = oef_channel.oef_search_dialogues
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=dialogue_reference,
            query=query,
        )
        oef_search_msg.to = str(oef_connection.connection_id)
        oef_search_msg.sender = SOME_SKILL_ID
        dialogue = dialogues.update(oef_search_msg)
        assert dialogue is not None
        oef_channel.oef_msg_id_to_dialogue[oef_channel.oef_msg_id] = dialogue
        oef_channel.on_oef_error(
            answer_id=oef_channel.oef_msg_id,
            operation=OEFErrorOperation.SEARCH_SERVICES,
        )
        envelope = self.multiplexer1.get(block=True, timeout=5.0)
        dec_msg = envelope.message
        assert dec_msg.dialogue_reference[0] == dialogue_reference[0]
        assert (
            dec_msg.performative is OefSearchMessage.Performative.OEF_ERROR
        ), "It should be an error message"

    def test_send(self):
        """Test the send method."""
        envelope = Envelope(
            to=str(self.connection1.connection_id),
            sender=SOME_SKILL_ID,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=b"Hello",
        )
        self.multiplexer1.put(envelope)
        received_envelope = self.multiplexer1.get(block=True, timeout=5.0)
        assert received_envelope is not None

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()


class TestOefConnection(UseOef):
    """Tests the con.connection_status.is_connected property."""

    def test_connection(self):
        """Test that an OEF connection can be established to the OEF."""
        connection = _make_oef_connection(
            FETCHAI_ADDRESS_ONE, DUMMY_PUBLIC_KEY, oef_addr="127.0.0.1", oef_port=10000,
        )
        multiplexer = Multiplexer([connection], protocols=[FipaMessage, DefaultMessage])
        multiplexer.connect()
        multiplexer.disconnect()


class TestOefConstraint:
    """Tests oef_constraint expressions."""

    @classmethod
    def setup_class(cls):
        """
        Set the test up.

        Steps:
        - Register a service
        - Check that the registration worked.
        """
        cls.obj_transaltor = OEFObjectTranslator()

    def test_oef_constraint_types(self):
        """Test the constraint types of the OEF."""
        with pytest.raises(ValueError):
            m_constraint = self.obj_transaltor.from_oef_constraint_type(
                ConstraintType(ConstraintTypes.EQUAL, "==")
            )
            eq = self.obj_transaltor.to_oef_constraint_type(m_constraint)
            assert eq.value == "=="

        m_constraint = ConstraintType(ConstraintTypes.NOT_EQUAL, "!=")
        neq = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(neq)
        assert m_constraint == m_constr
        assert neq.value == "!="
        m_constraint = ConstraintType(ConstraintTypes.LESS_THAN, "<")
        lt = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(lt)
        assert m_constraint == m_constr
        assert lt.value == "<"
        m_constraint = ConstraintType(ConstraintTypes.LESS_THAN_EQ, "<=")
        lt_eq = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(lt_eq)
        assert m_constraint == m_constr
        assert lt_eq.value == "<="
        m_constraint = ConstraintType(ConstraintTypes.GREATER_THAN, ">")
        gt = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(gt)
        assert m_constraint == m_constr
        assert gt.value == ">"
        m_constraint = ConstraintType(ConstraintTypes.GREATER_THAN_EQ, ">=")
        gt_eq = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(gt_eq)
        assert m_constraint == m_constr
        assert gt_eq.value == ">="
        m_constraint = ConstraintType("within", (-10.0, 10.0))
        with_in = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(with_in)
        assert m_constraint == m_constr
        assert with_in._value[0] <= 10 <= with_in._value[1]
        m_constraint = ConstraintType("in", (1, 2, 3))
        in_set = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(in_set)
        assert m_constraint == m_constr
        assert 2 in in_set._value
        m_constraint = ConstraintType("not_in", ("C", "Java", "Python"))
        not_in = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(not_in)
        assert m_constraint == m_constr
        assert "C++" not in not_in._value
        location = Location(47.692180, 10.039470)
        distance_float = 0.2
        m_constraint = ConstraintType("distance", (location, distance_float))
        distance = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(distance)
        assert m_constraint == m_constr
        assert (
            distance.center == self.obj_transaltor.to_oef_location(location)
            and distance.distance == distance_float
        )

        with pytest.raises(ValueError):
            m_constraint = ConstraintType(ConstraintTypes.EQUAL, "foo")
            with mock.patch.object(
                m_constraint, "type", return_value="unknown_constraint_type"
            ):
                eq = self.obj_transaltor.to_oef_constraint_type(m_constraint)

        with pytest.raises(ValueError):
            self.obj_transaltor.from_oef_constraint_expr(
                oef_constraint_expr=cast(ConstraintExpr, DummyConstrainExpr())
            )

    def test_oef_constraint_expr(self):
        """Test the value error of constraint type."""
        with pytest.raises(ValueError):
            self.obj_transaltor.to_oef_constraint_expr(
                constraint_expr=cast(ConstraintExpr, DummyConstrainExpr())
            )

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        pass


class DummyConstrainExpr(ConstraintExpr):
    """This class is used to represent a constraint expression."""

    def check(self, description: Description) -> bool:
        """
        Check if a description satisfies the constraint expression.

        :param description: the description to check.
        :return: ``True`` if the description satisfy the constraint expression, ``False`` otherwise.
        """
        pass

    def is_valid(self, data_model: DataModel) -> bool:
        """
        Check whether a constraint expression is valid wrt a data model. Specifically, check the following conditions.

        - If all the attributes referenced by the constraints are correctly associated with the Data Model attributes.

        :param data_model: the data model used to check the validity of the constraint expression.
        :return: ``True`` if the constraint expression is valid wrt the data model, ``False`` otherwise.
        """
        pass

    def _check_validity(self) -> None:
        """Check whether a Constraint Expression satisfies some basic requirements.

        E.g. an :class:`~oef.query.And` expression must have at least 2 subexpressions.
        :return ``None``
        :raises ValueError: if the object does not satisfy some requirements.
        """
        return

    @property
    def _node(self):
        pass


class TestSendWithOEF(UseOef):
    """Test other usecases with OEF."""

    @pytest.mark.asyncio
    async def test_send_oef_message(self, pytestconfig, caplog):
        """Test the send oef message."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            oef_connection = _make_oef_connection(
                address=FETCHAI_ADDRESS_ONE,
                public_key=DUMMY_PUBLIC_KEY,
                oef_addr="127.0.0.1",
                oef_port=10000,
            )
            await oef_connection.connect()
            oef_search_dialogues = OefSearchDialogues(SOME_SKILL_ID)
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.OEF_ERROR,
                dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
                oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
            )
            msg.to = str(oef_connection.connection_id)
            msg.sender = SOME_SKILL_ID
            envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
            with caplog.at_level(logging.DEBUG, "aea.packages.fetchai.connections.oef"):
                await oef_connection.send(envelope)
                assert "Could not create dialogue for message=" in caplog.text

            data_model = DataModel("foobar", attributes=[Attribute("foo", str, True)])
            query = Query(
                constraints=[Constraint("foo", ConstraintType("==", "bar"))],
                model=data_model,
            )

            msg, sending_dialogue = oef_search_dialogues.create(
                counterparty=str(oef_connection.connection_id),
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=query,
            )
            envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
            await oef_connection.send(envelope)
            envelope = await oef_connection.receive()
            search_result = envelope.message
            response_dialogue = oef_search_dialogues.update(search_result)
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert sending_dialogue == response_dialogue
            await asyncio.sleep(2.0)
            await oef_connection.disconnect()

    @pytest.mark.asyncio
    async def test_cancelled_receive(self, pytestconfig, caplog):
        """Test the case when a receive request is cancelled."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE,
            public_key=DUMMY_PUBLIC_KEY,
            oef_addr="127.0.0.1",
            oef_port=10000,
        )
        await oef_connection.connect()

        with caplog.at_level(logging.DEBUG, "aea.packages.fetchai.connections.oef"):

            async def receive():
                await oef_connection.receive()

            task = asyncio.ensure_future(receive(), loop=asyncio.get_event_loop())
            await asyncio.sleep(0.1)
            task.cancel()
            await asyncio.sleep(0.1)
            await oef_connection.disconnect()

            assert "Receive cancelled." in caplog.text

    @pytest.mark.asyncio
    async def test_exception_during_receive(self, pytestconfig):
        """Test the case when there is an exception during a receive request."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE,
            public_key=DUMMY_PUBLIC_KEY,
            oef_addr="127.0.0.1",
            oef_port=10000,
        )
        await oef_connection.connect()

        with unittest.mock.patch.object(
            oef_connection.channel._in_queue, "get", side_effect=Exception
        ):
            result = await oef_connection.receive()
            assert result is None

        await oef_connection.disconnect()

    @pytest.mark.asyncio
    async def test_connecting_twice_is_ok(self, pytestconfig):
        """Test that calling 'connect' twice works as expected."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE,
            public_key=DUMMY_PUBLIC_KEY,
            oef_addr="127.0.0.1",
            oef_port=10000,
        )

        assert not oef_connection.is_connected
        await oef_connection.connect()
        assert oef_connection.is_connected
        await oef_connection.connect()
        assert oef_connection.is_connected

        await oef_connection.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Python version < 3.7 not supported by the OEF."
)
async def test_cannot_connect_to_oef():
    """Test the case when we can't connect to the OEF."""
    oef_connection = _make_oef_connection(
        address=FETCHAI_ADDRESS_ONE,
        public_key=DUMMY_PUBLIC_KEY,
        oef_addr="127.0.0.1",
        oef_port=61234,  # use addr instead of hostname to avoid name resolution
    )

    with mock.patch.object(oef_connection.logger, "warning") as mock_logger:

        task = asyncio.ensure_future(
            oef_connection.connect(), loop=asyncio.get_event_loop()
        )
        await asyncio.sleep(3.0)
        mock_logger.assert_any_call(
            "Cannot connect to OEFChannel. Retrying in 5 seconds..."
        )
        with suppress(asyncio.CancelledError):
            task.cancel()
            await task
        await oef_connection.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Python version < 3.7 not supported by the OEF."
)
async def test_methods_with_logging_only():
    """Test the case when we can't connect to the OEF."""
    oef_connection = _make_oef_connection(
        address=FETCHAI_ADDRESS_ONE,
        public_key=DUMMY_PUBLIC_KEY,
        oef_addr="127.0.0.1",
        oef_port=61234,  # use addr instead of hostname to avoid name resolution
    )

    with patch.object(oef_connection.channel, "_oef_agent_connect", return_value=True):
        await oef_connection.connect()

    oef_connection.channel.on_cfp(
        msg_id=1, dialogue_id=1, origin="some", target=1, query=b""
    )
    oef_connection.channel.on_decline(msg_id=1, dialogue_id=1, origin="some", target=1)
    oef_connection.channel.on_propose(
        msg_id=1, dialogue_id=1, origin="some", target=1, proposals=b""
    )
    oef_connection.channel.on_accept(msg_id=1, dialogue_id=1, origin="some", target=1)

    try:
        await oef_connection.disconnect()
    except Exception:  # nosec
        pass
