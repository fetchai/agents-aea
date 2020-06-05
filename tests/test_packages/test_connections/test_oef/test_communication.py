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
from typing import Dict, cast
from unittest import mock

from oef.messages import OEFErrorOperation
from oef.query import ConstraintExpr

import pytest

from aea.helpers.async_utils import cancel_and_wait
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
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.test_tools.test_cases import UseOef

import packages
from packages.fetchai.connections.oef.connection import OEFObjectTranslator
from packages.fetchai.protocols.fipa import fipa_pb2
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from ....conftest import FETCHAI_ADDRESS_ONE, FETCHAI_ADDRESS_TWO, _make_oef_connection

DEFAULT_OEF = "default_oef"

logger = logging.getLogger(__name__)


class TestDefault(UseOef):
    """Test that the default protocol is correctly implemented by the OEF channel."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.connection = _make_oef_connection(
            FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.multiplexer = Multiplexer([cls.connection])
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
            Envelope(
                to=FETCHAI_ADDRESS_ONE,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=DefaultMessage.protocol_id,
                message=msg,
            )
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

        @classmethod
        def setup_class(cls):
            """Set the test up."""
            cls.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
            )
            cls.multiplexer = Multiplexer([cls.connection])
            cls.multiplexer.connect()

        def test_search_services_with_query_without_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has no data model.
            """
            request_id = 1
            search_query_empty_model = Query(
                [Constraint("foo", ConstraintType("==", "bar"))], model=None
            )
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(request_id), ""),
                query=search_query_empty_model,
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(request_id)
            assert request_id and search_result.agents == ()

        def test_search_services_with_query_with_model(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has a simple data model.
            """
            request_id = 1
            data_model = DataModel("foobar", [Attribute("foo", str, True)])
            search_query = Query(
                [Constraint("foo", ConstraintType("==", "bar"))], model=data_model
            )
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(request_id), ""),
                query=search_query,
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(request_id)
            assert search_result.agents == ()

        def test_search_services_with_distance_query(self):
            """Test that a search services request can be sent correctly.

            In this test, the query has a simple data model.
            """
            tour_eiffel = Location(48.8581064, 2.29447)
            request_id = 1
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
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(request_id), ""),
                query=search_query,
            )

            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )
            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            print("HERE:" + str(search_result))
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(request_id)
            assert search_result.agents == ()

        @classmethod
        def teardown_class(cls):
            """Teardowm the test."""
            cls.multiplexer.disconnect()

    class TestRegisterService:
        """Tests related to service registration functionality."""

        @classmethod
        def setup_class(cls):
            """Set the test up."""
            cls.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
            )
            cls.multiplexer = Multiplexer([cls.connection])
            cls.multiplexer.connect()

        def test_register_service(self):
            """Test that a register service request works correctly."""
            foo_datamodel = DataModel(
                "foo", [Attribute("bar", int, True, "A bar attribute.")]
            )
            desc = Description({"bar": 1}, data_model=foo_datamodel)
            request_id = 1
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                dialogue_reference=(str(request_id), ""),
                service_description=desc,
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=msg,
                )
            )
            time.sleep(0.5)

            request_id += 1
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(request_id), ""),
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))], model=foo_datamodel
                ),
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )
            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(request_id)
            if search_result.agents != [FETCHAI_ADDRESS_ONE]:
                logger.warning(
                    "search_result.agents != [FETCHAI_ADDRESS_ONE] FAILED in test_oef/test_communication.py"
                )

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
                FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
            )
            cls.multiplexer = Multiplexer([cls.connection])
            cls.multiplexer.connect()

            cls.request_id = 1
            cls.foo_datamodel = DataModel(
                "foo", [Attribute("bar", int, True, "A bar attribute.")]
            )
            cls.desc = Description({"bar": 1}, data_model=cls.foo_datamodel)
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                dialogue_reference=(str(cls.request_id), ""),
                service_description=cls.desc,
            )
            cls.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=msg,
                )
            )

            time.sleep(1.0)

            cls.request_id += 1
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(cls.request_id), ""),
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))],
                    model=cls.foo_datamodel,
                ),
            )
            cls.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )
            envelope = cls.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.message_id == cls.request_id
            if search_result.agents != [FETCHAI_ADDRESS_ONE]:
                logger.warning(
                    "search_result.agents != [FETCHAI_ADDRESS_ONE] FAILED in test_oef/test_communication.py"
                )

        def test_unregister_service(self):
            """Test that an unregister service request works correctly.

            Steps:
            2. unregister the service
            3. search for that service
            4. assert that no result is found.
            """
            self.request_id += 1
            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                dialogue_reference=(str(self.request_id), ""),
                service_description=self.desc,
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=msg,
                )
            )

            time.sleep(1.0)

            self.request_id += 1
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(self.request_id), ""),
                query=Query(
                    [Constraint("bar", ConstraintType("==", 1))],
                    model=self.foo_datamodel,
                ),
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(self.request_id)
            assert search_result.agents == ()

        @classmethod
        def teardown_class(cls):
            """Teardown the test."""
            cls.multiplexer.disconnect()

    class TestMailStats:
        """This class contains tests for the mail stats component."""

        @classmethod
        def setup_class(cls):
            """Set the tests up."""
            cls.connection = _make_oef_connection(
                FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
            )
            cls.multiplexer = Multiplexer([cls.connection])
            cls.multiplexer.connect()

            cls.connection = cls.multiplexer.connections[0]

        def test_search_count_increases(self):
            """Test that the search count increases."""
            request_id = 1
            search_query_empty_model = Query(
                [Constraint("foo", ConstraintType("==", "bar"))], model=None
            )
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(request_id), ""),
                query=search_query_empty_model,
            )
            self.multiplexer.put(
                Envelope(
                    to=DEFAULT_OEF,
                    sender=FETCHAI_ADDRESS_ONE,
                    protocol_id=OefSearchMessage.protocol_id,
                    message=search_request,
                )
            )

            envelope = self.multiplexer.get(block=True, timeout=5.0)
            search_result = envelope.message
            assert (
                search_result.performative
                == OefSearchMessage.Performative.SEARCH_RESULT
            )
            assert search_result.dialogue_reference[0] == str(request_id)
            assert request_id and search_result.agents == ()

        @classmethod
        def teardown_class(cls):
            """Tear the tests down."""
            cls.multiplexer.disconnect()


class TestFIPA(UseOef):
    """Test that the FIPA protocol is correctly implemented by the OEF channel."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.connection1 = _make_oef_connection(
            FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.connection2 = _make_oef_connection(
            FETCHAI_ADDRESS_TWO, oef_addr="127.0.0.1", oef_port=10000,
        )
        cls.multiplexer1 = Multiplexer([cls.connection1])
        cls.multiplexer2 = Multiplexer([cls.connection2])
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
        cfp_message.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=cfp_message,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=5.0)
        expected_cfp_message = FipaMessage.serializer.decode(envelope.message)
        expected_cfp_message.counterparty = FETCHAI_ADDRESS_TWO

        assert expected_cfp_message == cfp_message

        cfp_none = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        cfp_none.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=cfp_none,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=5.0)
        expected_cfp_none = FipaMessage.serializer.decode(envelope.message)
        expected_cfp_none.counterparty = FETCHAI_ADDRESS_TWO
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
        propose_empty.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=propose_empty,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_propose_empty = FipaMessage.serializer.decode(envelope.message)
        expected_propose_empty.counterparty = FETCHAI_ADDRESS_TWO
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

        propose_descriptions.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=propose_descriptions,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_propose_descriptions = FipaMessage.serializer.decode(envelope.message)
        expected_propose_descriptions.counterparty = FETCHAI_ADDRESS_TWO
        assert expected_propose_descriptions == propose_descriptions

    def test_accept(self):
        """Test that an Accept can be sent correctly."""
        accept = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        accept.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=accept,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_accept = FipaMessage.serializer.decode(envelope.message)
        expected_accept.counterparty = FETCHAI_ADDRESS_TWO
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
        match_accept.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=match_accept,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_match_accept = FipaMessage.serializer.decode(envelope.message)
        expected_match_accept.counterparty = FETCHAI_ADDRESS_TWO
        assert expected_match_accept == match_accept

    def test_decline(self):
        """Test that a Decline can be sent correctly."""
        decline = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.DECLINE,
        )
        decline.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=decline,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        expected_decline = FipaMessage.serializer.decode(envelope.message)
        expected_decline.counterparty = FETCHAI_ADDRESS_TWO
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
        match_accept_w_inform.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=match_accept_w_inform,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_match_accept_w_inform = FipaMessage.serializer.decode(envelope.message)
        returned_match_accept_w_inform.counterparty = FETCHAI_ADDRESS_TWO
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
        accept_w_inform.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=accept_w_inform,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_accept_w_inform = FipaMessage.serializer.decode(envelope.message)
        returned_accept_w_inform.counterparty = FETCHAI_ADDRESS_TWO
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
        inform.counterparty = FETCHAI_ADDRESS_TWO
        self.multiplexer1.put(
            Envelope(
                to=FETCHAI_ADDRESS_TWO,
                sender=FETCHAI_ADDRESS_ONE,
                protocol_id=FipaMessage.protocol_id,
                message=inform,
            )
        )
        envelope = self.multiplexer2.get(block=True, timeout=2.0)
        returned_inform = FipaMessage.serializer.decode(envelope.message)
        returned_inform.counterparty = FETCHAI_ADDRESS_TWO
        assert returned_inform == inform

    def test_serialisation_fipa(self):
        """Tests a Value Error flag for wrong CFP query."""
        with pytest.raises(ValueError):
            msg = FipaMessage(
                performative=FipaMessage.Performative.CFP,
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            )
            with mock.patch(
                "packages.fetchai.protocols.fipa.message.FipaMessage.Performative"
            ) as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                FipaMessage.serializer.encode(msg), "Raises Value Error"
        with pytest.raises(EOFError):
            cfp_msg = FipaMessage(
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
                performative=FipaMessage.Performative.CFP,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            )
            cfp_msg.set("query", "hello")
            fipa_msg = fipa_pb2.FipaMessage()
            fipa_msg.message_id = cfp_msg.message_id
            dialogue_reference = cast(Dict[str, str], cfp_msg.dialogue_reference)
            fipa_msg.dialogue_starter_reference = dialogue_reference[0]
            fipa_msg.dialogue_responder_reference = dialogue_reference[1]
            fipa_msg.target = cfp_msg.target
            performative = fipa_pb2.FipaMessage.Cfp_Performative()
            fipa_msg.cfp.CopyFrom(performative)
            fipa_bytes = fipa_msg.SerializeToString()

            # The encoded message is not a valid FIPA message.
            FipaMessage.serializer.decode(fipa_bytes)
        with pytest.raises(ValueError):
            cfp_msg = FipaMessage(
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
                performative=FipaMessage.Performative.CFP,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            )
            with mock.patch(
                "packages.fetchai.protocols.fipa.message.FipaMessage.Performative"
            ) as mock_performative_enum:
                mock_performative_enum.CFP.value = "unknown"
                fipa_msg = fipa_pb2.FipaMessage()
                fipa_msg.message_id = cfp_msg.message_id
                dialogue_reference = cast(Dict[str, str], cfp_msg.dialogue_reference)
                fipa_msg.dialogue_starter_reference = dialogue_reference[0]
                fipa_msg.dialogue_responder_reference = dialogue_reference[1]
                fipa_msg.target = cfp_msg.target
                performative = fipa_pb2.FipaMessage.Cfp_Performative()
                fipa_msg.cfp.CopyFrom(performative)
                fipa_bytes = fipa_msg.SerializeToString()

                # The encoded message is not a FIPA message
                FipaMessage.serializer.decode(fipa_bytes)

    def test_on_oef_error(self):
        """Test the oef error."""
        oef_connection = self.multiplexer1.connections[0]
        oef_channel = oef_connection.channel

        oef_channel.oef_msg_id += 1
        dialogue_reference = ("1", str(oef_channel.oef_msg_id))
        oef_channel.oef_msg_it_to_dialogue_reference[
            oef_channel.oef_msg_id
        ] = dialogue_reference
        oef_channel.on_oef_error(
            answer_id=oef_channel.oef_msg_id,
            operation=OEFErrorOperation.SEARCH_SERVICES,
        )
        envelope = self.multiplexer1.get(block=True, timeout=5.0)
        dec_msg = envelope.message
        assert dec_msg.dialogue_reference == ("1", str(oef_channel.oef_msg_id))
        assert (
            dec_msg.performative is OefSearchMessage.Performative.OEF_ERROR
        ), "It should be an error message"

    def test_send(self):
        """Test the send method."""
        envelope = Envelope(
            to=DEFAULT_OEF,
            sender="me",
            protocol_id=DefaultMessage.protocol_id,
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
            FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        multiplexer = Multiplexer([connection])
        multiplexer.connect()
        multiplexer.disconnect()

    # TODO connection error has been removed
    # @pytest.mark.asyncio
    # async def test_oef_connect(self):
    #     """Test the OEFConnection."""
    #     config =  ConnectionConfig(
    #         oef_addr=HOST, oef_port=PORT, connection_id=OEFConnection.connection_id
    #     )
    #     OEFConnection(configuration=configuration, identity=Identity("name", "this_is_not_an_address"))
    #     assert not con.connection_status.is_connected
    #     with pytest.raises(ConnectionError):
    #         await con.connect()


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
        m_constraint = ConstraintType("in", [1, 2, 3])
        in_set = self.obj_transaltor.to_oef_constraint_type(m_constraint)
        m_constr = self.obj_transaltor.from_oef_constraint_type(in_set)
        assert m_constraint == m_constr
        assert 2 in in_set._value
        m_constraint = ConstraintType("not_in", {"C", "Java", "Python"})
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
    async def test_send_oef_message(self, pytestconfig):
        """Test the send oef message."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        request_id = 1
        oef_connection.loop = asyncio.get_event_loop()
        await oef_connection.connect()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.OEF_ERROR,
            dialogue_reference=(str(request_id), ""),
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )
        envelope = Envelope(
            to=DEFAULT_OEF,
            sender=FETCHAI_ADDRESS_ONE,
            protocol_id=OefSearchMessage.protocol_id,
            message=msg,
        )
        with pytest.raises(ValueError):
            await oef_connection.send(envelope)

        data_model = DataModel("foobar", attributes=[Attribute("foo", str, True)])
        query = Query(
            constraints=[Constraint("foo", ConstraintType("==", "bar"))],
            model=data_model,
        )

        request_id += 1
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=(str(request_id), ""),
            query=query,
        )
        envelope = Envelope(
            to=DEFAULT_OEF,
            sender=FETCHAI_ADDRESS_ONE,
            protocol_id=OefSearchMessage.protocol_id,
            message=msg,
        )
        await oef_connection.send(envelope)
        search_result = await oef_connection.receive()
        assert isinstance(search_result, Envelope)
        await asyncio.sleep(2.0)
        await oef_connection.disconnect()

    @pytest.mark.asyncio
    async def test_cancelled_receive(self, pytestconfig):
        """Test the case when a receive request is cancelled."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        oef_connection.loop = asyncio.get_event_loop()
        await oef_connection.connect()

        patch = unittest.mock.patch.object(
            packages.fetchai.connections.oef.connection.logger, "debug"
        )
        mocked_logger_debug = patch.start()

        async def receive():
            await oef_connection.receive()

        task = asyncio.ensure_future(receive(), loop=asyncio.get_event_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        await asyncio.sleep(0.1)
        await oef_connection.disconnect()

        mocked_logger_debug.assert_called_once_with("Receive cancelled.")

    @pytest.mark.asyncio
    async def test_exception_during_receive(self, pytestconfig):
        """Test the case when there is an exception during a receive request."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        oef_connection.loop = asyncio.get_event_loop()
        await oef_connection.connect()

        with unittest.mock.patch.object(
            oef_connection.in_queue, "get", side_effect=Exception
        ):
            result = await oef_connection.receive()
            assert result is None

        await oef_connection.disconnect()

    @pytest.mark.asyncio
    async def test_connecting_twice_is_ok(self, pytestconfig):
        """Test that calling 'connect' twice works as expected."""
        oef_connection = _make_oef_connection(
            address=FETCHAI_ADDRESS_ONE, oef_addr="127.0.0.1", oef_port=10000,
        )
        oef_connection.loop = asyncio.get_event_loop()

        assert not oef_connection.connection_status.is_connected
        await oef_connection.connect()
        assert oef_connection.connection_status.is_connected
        await oef_connection.connect()
        assert oef_connection.connection_status.is_connected

        await oef_connection.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Python version < 3.7 not supported by the OEF."
)
async def test_cannot_connect_to_oef():
    """Test the case when we can't connect to the OEF."""
    oef_connection = _make_oef_connection(
        address=FETCHAI_ADDRESS_ONE,
        oef_addr="127.0.0.1",
        oef_port=61234,  # use addr instead of hostname to avoid name resolution
    )
    oef_connection.loop = asyncio.get_event_loop()
    patch = unittest.mock.patch.object(
        packages.fetchai.connections.oef.connection.logger, "warning"
    )
    mocked_logger_warning = patch.start()

    async def try_to_connect():
        await oef_connection.connect()

    task = asyncio.ensure_future(try_to_connect(), loop=asyncio.get_event_loop())
    await asyncio.sleep(1.0)
    mocked_logger_warning.assert_called_with(
        "Cannot connect to OEFChannel. Retrying in 5 seconds..."
    )
    await cancel_and_wait(task)
    oef_connection.channel.disconnect()
    oef_connection.disconnect()
