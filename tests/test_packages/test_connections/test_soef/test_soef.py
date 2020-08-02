# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the tests of the soef connection module."""

import asyncio
import copy
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.connections.soef.connection import SOEFConnection, SOEFException
from packages.fetchai.protocols.oef_search.dialogues import OefSearchDialogue
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.conftest import UNKNOWN_PROTOCOL_PUBLIC_ID

from . import models


def make_async(return_value: Any) -> Callable:
    """Wrap value into async function."""
    # pydocstyle
    async def fn(*args, **kwargs):
        return return_value

    return fn


def wrap_future(return_value: Any) -> asyncio.Future:
    """Wrap value into future."""
    f: asyncio.Future = asyncio.Future()
    f.set_result(return_value)
    return f


class OefSearchDialogues(BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, agent_address: str) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        BaseOefSearchDialogues.__init__(self, agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming/outgoing first message.

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return OefSearchDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> OefSearchDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = OefSearchDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class TestSoef:
    """Set of unit tests for soef connection."""

    search_success_response = """<?xml version="1.0" encoding="UTF-8"?><response><success>1</success><total>2</total><capped>0</capped><results><agent name="8c25cc02fd0c45f8895a3d4b3895376a" genus="" classification=""><identities><identity chain_identifier="fetchai">2ayYmgrCg76R1mzr2zWCmivzJG31hXtFVwQvR4XrXrD88Rc3sT</identity></identities><range_in_km>0</range_in_km></agent><agent name="9b61f3d2217b4d4f995e779db775fbdd" genus="" classification=""><identities><identity chain_identifier="fetchai">2DvN8QNXKE2tjnKgMKvBy9ZFyC6JaFYFrcLyWSS4A9RDWeTP4k</identity></identities><range_in_km>0</range_in_km></agent></results></response>"""
    search_empty_response = """<?xml version="1.0" encoding="UTF-8"?><response><success>1</success><total>0</total><capped>0</capped><results></results></response>"""
    search_fail_response = (
        """<?xml version="1.0" encoding="UTF-8"?><notaresponse></notaresponse>"""
    )
    generic_success_response = """<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>"""

    def setup(self):
        """Set up."""
        self.crypto = make_crypto(DEFAULT_LEDGER)
        self.crypto2 = make_crypto(DEFAULT_LEDGER)
        identity = Identity("", address=self.crypto.address)
        self.oef_search_dialogues = OefSearchDialogues(self.crypto.address)

        # create the connection and multiplexer objects
        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="soef.fetch.ai",
            soef_port=9002,
            restricted_to_protocols={PublicId.from_str("fetchai/oef_search:0.3.0")},
            connection_id=SOEFConnection.connection_id,
        )
        self.connection = SOEFConnection(
            configuration=configuration, identity=identity,
        )
        self.connection.channel.unique_page_address = "some addr"
        self.connection2 = SOEFConnection(
            configuration=configuration,
            identity=Identity("", address=self.crypto2.address),
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.connection.connect())
        self.loop.run_until_complete(self.connection2.connect())

    @pytest.mark.asyncio
    async def test_set_service_key(self):
        """Test set service key."""
        service_instance = {"key": "test", "value": "test"}
        service_description = Description(
            service_instance, data_model=models.SET_SERVICE_KEY_MODEL
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        with pytest.raises(asyncio.TimeoutError):  # got no message back
            await asyncio.wait_for(self.connection.receive(), timeout=1)

    @pytest.mark.asyncio
    async def test_remove_service_key(self):
        """Test remove service key."""
        await self.test_set_service_key()
        service_instance = {"key": "test"}
        service_description = Description(
            service_instance, data_model=models.REMOVE_SERVICE_KEY_MODEL
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        with pytest.raises(asyncio.TimeoutError):  # got no message back
            await asyncio.wait_for(self.connection.receive(), timeout=1)

    def test_connected(self):
        """Test connected==True."""
        assert self.connection.connection_status.is_connected

    @pytest.mark.asyncio
    async def test_disconnected(self):
        """Test disconnect."""
        assert self.connection.connection_status.is_connected
        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async("<response><message>Goodbye!</message></response>"),
        ):
            await self.connection.disconnect()
        assert not self.connection.connection_status.is_connected

    @pytest.mark.asyncio
    async def test_register_service(self):
        """Test register service."""
        agent_location = Location(52.2057092, 2.1183431)
        service_instance = {"location": agent_location}
        service_description = Description(
            service_instance, data_model=models.AGENT_LOCATION_MODEL
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        with pytest.raises(asyncio.TimeoutError):  # got no message back
            await asyncio.wait_for(self.connection.receive(), timeout=1)

        assert self.connection.channel.agent_location == agent_location

    @pytest.mark.asyncio
    async def test_bad_register_service(self):
        """Test register service fails on bad values provided."""
        bad_location_model = DataModel(
            "not_location_agent",
            [
                Attribute(
                    "non_location", Location, True, "The location where the agent is."
                )
            ],
            "A data model to describe location of an agent.",
        )
        agent_location = Location(52.2057092, 2.1183431)
        service_instance = {"non_location": agent_location}
        service_description = Description(
            service_instance, data_model=bad_location_model
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )
        await self.connection.send(envelope)

        expected_envelope = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert expected_envelope
        assert (
            expected_envelope.message.performative
            == OefSearchMessage.Performative.OEF_ERROR
        )
        orig = expected_envelope.message
        message = copy.copy(orig)
        message.is_incoming = True  # TODO: fix
        message.counterparty = orig.sender  # TODO; fix
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    @pytest.mark.asyncio
    async def test_unregister_service(self):
        """Test unregister service."""
        agent_location = Location(52.2057092, 2.1183431)
        service_instance = {"location": agent_location}
        service_description = Description(
            service_instance, data_model=models.AGENT_LOCATION_MODEL
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )
        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async("<response><message>Goodbye!</message></response>"),
        ):
            await self.connection.send(envelope)

        assert self.connection.channel.unique_page_address is None

    @pytest.mark.asyncio
    async def test_register_personailty_pieces(self):
        """Test register service with personality pieces."""
        service_instance = {"piece": "genus", "value": "service"}
        service_description = Description(
            service_instance, data_model=models.AGENT_PERSONALITY_MODEL
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )
        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        with pytest.raises(asyncio.TimeoutError):  # got no message back
            await asyncio.wait_for(self.connection.receive(), timeout=1)

    @pytest.mark.asyncio
    async def test_send_excluded_protocol(self, caplog):
        """Test fail on unsupported protocol."""
        envelope = Envelope(
            to="soef",
            sender=self.crypto.address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"some msg",
        )
        self.connection.channel.excluded_protocols = [UNKNOWN_PROTOCOL_PUBLIC_ID]
        with pytest.raises(
            ValueError, match=r"Cannot send message, invalid protocol:.*"
        ):
            await self.connection.send(envelope)

    @pytest.mark.asyncio
    async def test_bad_message(self, caplog):
        """Test fail on bad message."""
        envelope = Envelope(
            to="soef",
            sender=self.crypto.address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"some msg",
        )
        with pytest.raises(ValueError):
            await self.connection.send(envelope)

    @pytest.mark.asyncio
    async def test_bad_performative(self, caplog):
        """Test fail on bad perfromative."""
        agent_location = Location(52.2057092, 2.1183431)
        service_instance = {"location": agent_location}
        service_description = Description(
            service_instance, data_model=models.AGENT_LOCATION_MODEL
        )
        message = OefSearchMessage(
            performative="oef_error",
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is None
        message.sender = self.crypto.address
        envelope = Envelope(
            to=message.counterparty,
            sender=message.sender,
            protocol_id=message.protocol_id,
            message=message,
        )
        with pytest.raises(ValueError):
            await self.connection.send(envelope)

    @pytest.mark.asyncio
    async def test_bad_search_query(self, caplog):
        """Test fail on invalid query for search."""
        await self.test_register_service()
        closeness_query = Query([], model=models.AGENT_LOCATION_MODEL)
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            query=closeness_query,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.search_empty_response),
        ):
            await self.connection.send(envelope)

        expected_envelope = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert expected_envelope
        message = expected_envelope.message
        assert message.performative == OefSearchMessage.Performative.OEF_ERROR
        orig = expected_envelope.message
        message = copy.copy(orig)
        message.is_incoming = True  # TODO: fix
        message.counterparty = orig.sender  # TODO; fix
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    @pytest.mark.asyncio
    async def test_search(self):
        """Test search."""
        agent_location = Location(52.2057092, 2.1183431)
        radius = 0.1
        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (agent_location, radius))
        )
        personality_filters = [
            Constraint("genus", ConstraintType("==", "vehicle")),
            Constraint(
                "classification", ConstraintType("==", "mobility.railway.train")
            ),
        ]
        service_key_filters = [
            Constraint("custom_key", ConstraintType("==", "custom_value")),
        ]
        closeness_query = Query(
            [close_to_my_service] + personality_filters + service_key_filters
        )
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            query=closeness_query,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.search_success_response),
        ):
            await self.connection.send(envelope)
            expected_envelope = await asyncio.wait_for(
                self.connection.receive(), timeout=1
            )

        assert expected_envelope
        message = expected_envelope.message
        assert len(message.agents) >= 1
        orig = expected_envelope.message
        message = copy.copy(orig)
        message.is_incoming = True  # TODO: fix
        message.counterparty = orig.sender  # TODO; fix
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    @pytest.mark.asyncio
    async def test_find_around_me(self):
        """Test internal method find around me."""
        agent_location = Location(52.2057092, 2.1183431)
        radius = 0.1
        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (agent_location, radius))
        )
        personality_filters = [
            Constraint("genus", ConstraintType("==", "vehicle")),
            Constraint(
                "classification", ConstraintType("==", "mobility.railway.train")
            ),
        ]
        service_key_filters = [
            Constraint("custom_key", ConstraintType("==", "custom_value")),
        ]
        closeness_query = Query(
            [close_to_my_service] + personality_filters + service_key_filters
        )

        message_1 = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            query=closeness_query,
        )
        message_1.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message_1)
        assert sending_dialogue is not None

        internal_msg_1 = copy.copy(message_1)
        internal_msg_1.is_incoming = True
        internal_msg_1.counterparty = message_1.sender
        internal_dialogue_1 = self.connection.channel.oef_search_dialogues.update(
            internal_msg_1
        )
        assert internal_dialogue_1 is not None

        message_2 = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            query=closeness_query,
        )
        message_2.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message_2)
        assert sending_dialogue is not None

        internal_msg_2 = copy.copy(message_2)
        internal_msg_2.is_incoming = True
        internal_msg_2.counterparty = message_2.sender
        internal_dialogue_2 = self.connection.channel.oef_search_dialogues.update(
            internal_msg_2
        )
        assert internal_dialogue_2 is not None

        message_3 = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            query=closeness_query,
        )
        message_3.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message_3)
        assert sending_dialogue is not None

        internal_msg_3 = copy.copy(message_3)
        internal_msg_3.is_incoming = True
        internal_msg_3.counterparty = message_3.sender
        internal_dialogue_3 = self.connection.channel.oef_search_dialogues.update(
            internal_msg_3
        )
        assert internal_dialogue_3 is not None

        with patch.object(
            self.connection.channel,
            "_request_text",
            new_callable=MagicMock,
            side_effect=[
                wrap_future(self.search_empty_response),
                wrap_future(self.search_success_response),
                wrap_future(self.search_fail_response),
            ],
        ):
            await self.connection.channel._find_around_me_handle_requet(
                internal_msg_1, internal_dialogue_1, 1, {}
            )
            await self.connection.channel._find_around_me_handle_requet(
                internal_msg_2, internal_dialogue_2, 1, {}
            )
            with pytest.raises(SOEFException, match=r"`find_around_me` error: .*"):
                await self.connection.channel._find_around_me_handle_requet(
                    internal_msg_3, internal_dialogue_3, 1, {}
                )

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Test internal method register agent."""
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(
                SOEFException,
                match="Agent registration error - page address or token not received",
            ):
                await self.connection.channel._register_agent()

        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response><encrypted>0</encrypted><token>672DB3B67780F98984ABF1123BD11</token><page_address>oef_C95B21A4D5759C8FE7A6304B62B726AB8077BEE4BA191A7B92B388F9B1</page_address></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(
                SOEFException, match=r"`acknowledge` error: .*",
            ):
                await self.connection.channel._register_agent()

        resp_text1 = '<?xml version="1.0" encoding="UTF-8"?><response><encrypted>0</encrypted><token>672DB3B67780F98984ABF1123BD11</token><page_address>oef_C95B21A4D5759C8FE7A6304B62B726AB8077BEE4BA191A7B92B388F9B1</page_address></response>'
        resp_text2 = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        resp_text3 = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        with patch.object(
            self.connection.channel,
            "_request_text",
            new_callable=MagicMock,
            side_effect=[
                wrap_future(resp_text1),
                wrap_future(resp_text2),
                wrap_future(resp_text3),
            ],
        ):
            await self.connection.channel._register_agent()
            assert self.connection.channel._ping_periodic_task is not None

    @pytest.mark.asyncio
    async def test_request(self):
        """Test internal method request_text."""
        with patch("requests.request"):
            await self.connection.channel._request_text("get", "http://not-exists.com")

    @pytest.mark.asyncio
    async def test_set_location(self):
        """Test internal method set location."""
        agent_location = Location(52.2057092, 2.1183431)
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(SOEFException, match=r"`set_position` error: .*"):
                await self.connection.channel._set_location(agent_location)

        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            await self.connection.channel._set_location(agent_location)

    @pytest.mark.asyncio
    async def test_set_personality_piece(self):
        """Test internal method set_personality_piece."""
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(
                SOEFException, match=r"`set_personality_piece` error: .*"
            ):
                await self.connection.channel._set_personality_piece(1, 1)

        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            await self.connection.channel._set_personality_piece(1, 1)

    def teardown(self):
        """Clean up."""
        try:
            with patch.object(
                self.connection.channel,
                "_request_text",
                make_async("<response><message>Goodbye!</message></response>"),
            ):
                self.loop.run_until_complete(self.connection.disconnect())
        except Exception:  # nosec
            pass

    @pytest.mark.asyncio
    async def test__set_value(self):
        """Test set pieces."""
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(SOEFException, match=r"`set_personality_piece` error:"):
                await self.connection.channel._set_personality_piece(1, 1)

        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            await self.connection.channel._set_personality_piece(1, 1)

    def test_chain_identifier_fail(self):
        """Test fail on invalid chain id."""
        chain_identifier = "test"
        identity = Identity("", "")

        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="soef.fetch.ai",
            soef_port=9002,
            restricted_to_protocols={PublicId.from_str("fetchai/oef_search:0.3.0")},
            connection_id=SOEFConnection.connection_id,
            chain_identifier=chain_identifier,
        )
        with pytest.raises(ValueError, match="Unsupported chain_identifier"):
            SOEFConnection(
                configuration=configuration, identity=identity,
            )

    def test_chain_identifier_ok(self):
        """Test set valid chain id."""
        chain_identifier = "fetchai_cosmos"
        identity = Identity("", "")

        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="soef.fetch.ai",
            soef_port=9002,
            restricted_to_protocols={PublicId.from_str("fetchai/oef_search:0.3.0")},
            connection_id=SOEFConnection.connection_id,
            chain_identifier=chain_identifier,
        )
        connection = SOEFConnection(configuration=configuration, identity=identity,)

        assert connection.channel.chain_identifier == chain_identifier

    @pytest.mark.asyncio
    async def test_ping_command(self):
        """Test set service key."""
        service_description = Description({}, data_model=models.PING_MODEL)
        message = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=self.oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=service_description,
        )
        message.counterparty = SOEFConnection.connection_id.latest
        sending_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=message.counterparty,
            sender=self.crypto.address,
            protocol_id=message.protocol_id,
            message=message,
        )

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        with pytest.raises(asyncio.TimeoutError):  # got no message back
            await asyncio.wait_for(self.connection.receive(), timeout=1)

    @pytest.mark.asyncio
    async def test_periodic_ping_task_is_set(self):
        """Test periodic ping task is set on agent register."""
        resp_text1 = '<?xml version="1.0" encoding="UTF-8"?><response><encrypted>0</encrypted><token>672DB3B67780F98984ABF1123BD11</token><page_address>oef_C95B21A4D5759C8FE7A6304B62B726AB8077BEE4BA191A7B92B388F9B1</page_address></response>'
        resp_text2 = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        resp_text3 = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        self.connection.channel.PING_PERIOD = 0.1

        with patch.object(
            self.connection.channel,
            "_request_text",
            new_callable=MagicMock,
            side_effect=[
                wrap_future(resp_text1),
                wrap_future(resp_text2),
                wrap_future(resp_text3),
            ],
        ):
            with patch.object(self.connection.channel, "_ping_command",) as mocked_ping:
                await self.connection.channel._register_agent()

                assert self.connection.channel._ping_periodic_task is not None
                await asyncio.sleep(0.3)
                assert mocked_ping.call_count > 1
