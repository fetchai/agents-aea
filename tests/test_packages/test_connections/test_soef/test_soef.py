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
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.exceptions import AEAEnforceError
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
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.soef.connection import (
    SOEFConnection,
    SOEFException,
    SOEFNetworkConnectionError,
    SOEFServerBadResponseError,
    requests,
)
from packages.fetchai.protocols.oef_search.dialogues import OefSearchDialogue
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.conftest import UNKNOWN_PROTOCOL_PUBLIC_ID
from tests.test_packages.test_connections.test_soef import models


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


class TestSoefTokenStorage:
    """Set of unit tests for soef connection token storage."""

    def setup(self):
        """Set up."""
        self.skill_id = "some_author/some_skill:0.1.0"
        self.crypto = make_crypto(DEFAULT_LEDGER)
        self.crypto2 = make_crypto(DEFAULT_LEDGER)
        self.data_dir = tempfile.mkdtemp()
        identity = Identity(
            "identity", address=self.crypto.address, public_key=self.crypto.public_key
        )
        self.oef_search_dialogues = OefSearchDialogues(self.skill_id)

        # create the connection and multiplexer objects
        self.token_storage_path = "test.storage"
        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="s-oef.fetch.ai",
            soef_port=443,
            token_storage_path=self.token_storage_path,
            restricted_to_protocols={OefSearchMessage.protocol_specification_id},
            connection_id=SOEFConnection.connection_id,
        )
        self.connection = SOEFConnection(
            configuration=configuration, data_dir=self.data_dir, identity=identity,
        )

    def teardown(self):
        """Tear down."""
        try:
            os.remove(self.token_storage_path)
            shutil.rmtree(self.data_dir)
        except Exception as e:
            print(e)

    def test_unique_page_address_default_no_file(self):
        """Test unique page address does not raise if file not found."""
        assert self.connection.channel.unique_page_address is None

    def test_unique_page_address_default_file(self):
        """Test unique page address is None by default for new file."""
        with open(self.token_storage_path, "w"):
            os.utime(self.token_storage_path, None)
        assert self.connection.channel.unique_page_address is None

    def test_unique_page_address_set_and_get(self):
        """Test unique page address set and get including None."""
        self.connection.channel.unique_page_address = "test"
        assert self.connection.channel._unique_page_address == "test"
        assert self.connection.channel.unique_page_address == "test"
        expected_token_storage_path = Path(self.data_dir) / self.token_storage_path
        with expected_token_storage_path.open() as f:
            in_file = f.read()
        assert in_file == "test"
        self.connection.channel.unique_page_address = None
        assert self.connection.channel._unique_page_address is None
        assert self.connection.channel.unique_page_address is None
        with expected_token_storage_path.open() as f:
            in_file = f.read()
        assert in_file == self.connection.channel.NONE_UNIQUE_PAGE_ADDRESS


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
        self.skill_id = "some_author/some_skill:0.1.0"
        self.crypto = make_crypto(DEFAULT_LEDGER)
        self.crypto2 = make_crypto(DEFAULT_LEDGER)
        identity = Identity(
            "identity", address=self.crypto.address, public_key=self.crypto.public_key
        )
        self.oef_search_dialogues = OefSearchDialogues(self.skill_id)
        self.data_dir = tempfile.mkdtemp()

        # create the connection and multiplexer objects
        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="s-oef.fetch.ai",
            soef_port=443,
            restricted_to_protocols={OefSearchMessage.protocol_specification_id},
            connection_id=SOEFConnection.connection_id,
        )
        self.connection = SOEFConnection(
            configuration=configuration, data_dir=self.data_dir, identity=identity,
        )
        self.connection2 = SOEFConnection(
            configuration=configuration,
            data_dir=self.data_dir,
            identity=Identity(
                "identity",
                address=self.crypto2.address,
                public_key=self.crypto2.public_key,
            ),
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.connection.connect())
        self.loop.run_until_complete(self.connection2.connect())
        self.connection.channel.unique_page_address = "some_addr"

    @pytest.mark.asyncio
    async def test_set_service_key(self):
        """Test set service key."""
        service_instance = {"key": "test", "value": "test"}
        service_description = Description(
            service_instance, data_model=models.SET_SERVICE_KEY_MODEL
        )
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        response = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert response.message.performative == OefSearchMessage.Performative.SUCCESS
        assert response.message.agents_info.body == {}

    @pytest.mark.asyncio
    async def test_remove_service_key(self):
        """Test remove service key."""
        await self.test_set_service_key()
        service_instance = {"key": "test"}
        service_description = Description(
            service_instance, data_model=models.REMOVE_SERVICE_KEY_MODEL
        )
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        response = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert response.message.performative == OefSearchMessage.Performative.SUCCESS
        assert response.message.agents_info.body == {}

    def test_connected(self):
        """Test connected==True."""
        assert self.connection.is_connected

    @pytest.mark.asyncio
    async def test_disconnected(self):
        """Test disconnect."""
        assert self.connection.is_connected
        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async("<response><message>Goodbye!</message></response>"),
        ):
            await self.connection.disconnect()
        assert not self.connection.is_connected

    @pytest.mark.asyncio
    async def test_register_service(self):
        """Test register service."""
        agent_location = Location(52.2057092, 2.1183431)
        service_instance = {"location": agent_location}
        service_description = Description(
            service_instance, data_model=models.AGENT_LOCATION_MODEL
        )
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        response = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert response.message.performative == OefSearchMessage.Performative.SUCCESS
        assert response.message.agents_info.body == {}

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
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        await self.connection.send(envelope)

        expected_envelope = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert expected_envelope
        assert (
            expected_envelope.message.performative
            == OefSearchMessage.Performative.OEF_ERROR
        )
        message = expected_envelope.message
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
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
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
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        response = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert response.message.performative == OefSearchMessage.Performative.SUCCESS
        assert response.message.agents_info.body == {}

    @pytest.mark.asyncio
    async def test_bad_message(self):
        """Test fail on bad message."""
        envelope = Envelope(
            to="soef",
            sender=self.crypto.address,
            protocol_specification_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"some msg",
        )
        with pytest.raises(
            AEAEnforceError, match=r"Message not of type OefSearchMessage"
        ):
            await self.connection.send(envelope)

    @pytest.mark.asyncio
    async def test_bad_performative(self):
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
        message.to = str(SOEFConnection.connection_id.to_any())
        message.sender = self.skill_id
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        with pytest.raises(ValueError):
            await self.connection.send(envelope)

    @pytest.mark.asyncio
    async def test_bad_search_query(self):
        """Test fail on invalid query for search."""
        await self.test_register_service()
        closeness_query = Query([], model=models.AGENT_LOCATION_MODEL)
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

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
        message = expected_envelope.message
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
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

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
        message = expected_envelope.message
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

        message_1, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )

        internal_dialogue_1 = self.connection.channel.oef_search_dialogues.update(
            message_1
        )
        assert internal_dialogue_1 is not None

        message_2, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )

        internal_dialogue_2 = self.connection.channel.oef_search_dialogues.update(
            message_2
        )
        assert internal_dialogue_2 is not None

        message_3, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=closeness_query,
        )

        internal_dialogue_3 = self.connection.channel.oef_search_dialogues.update(
            message_3
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
            await self.connection.channel._find_around_me_handle_request(
                message_1, internal_dialogue_1, 1, {}
            )
            await self.connection.channel._find_around_me_handle_request(
                message_2, internal_dialogue_2, 1, {}
            )
            with pytest.raises(
                SOEFException, match=r".* `find_around_me` .*Exception: .*"
            ):
                await self.connection.channel._find_around_me_handle_request(
                    message_3, internal_dialogue_3, 1, {}
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
                SOEFException, match=r"`acknowledge` .*Exception: .*",
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
    async def test_check_server_reachable(self):
        """Test server can not be reached."""
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<a></a>"

        async def slow_request(*args, **kwargs):
            await asyncio.sleep(10)

        with patch.object(
            self.connection.channel, "_request_text", slow_request
        ), patch.object(self.connection.channel, "connection_check_timeout", 0.01):
            with pytest.raises(
                SOEFNetworkConnectionError,
                match="<SOEF Network Connection Error: Server can not be reached within timeout=",
            ):
                await self.connection.channel._check_server_reachable()

    @pytest.mark.asyncio
    async def test_request_text_ok(self):
        """Test internal method request_text works ok."""
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<a></a>"
        with patch("aea.helpers.http_requests.request", return_value=resp):
            await self.connection.channel._request_text("get", "http://not-exists.com")

    @pytest.mark.asyncio
    async def test_request_text_fail(self):
        """Test internal method request_text fails."""
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "<a></a>"
        with pytest.raises(
            SOEFServerBadResponseError,
            match="<SOEF Server Bad Response Error: Bad server response: code 400 when 2XX expected.",
        ):
            with patch("aea.helpers.http_requests.request", return_value=resp):
                await self.connection.channel._request_text(
                    "get", "http://not-exists.com"
                )

        resp.status_code = 200
        resp.text = ""
        with pytest.raises(
            SOEFServerBadResponseError,
            match="SOEF Server Bad Response Error: Bad server response: empty response. Request data:",
        ):
            with patch("aea.helpers.http_requests.request", return_value=resp):
                await self.connection.channel._request_text(
                    "get", "http://not-exists.com"
                )

        resp.status_code = 200
        resp.text = ""
        with pytest.raises(
            SOEFNetworkConnectionError,
            match="SOEF Network Connection Error:.*expected!",
        ):
            with patch(
                "aea.helpers.http_requests.request",
                side_effect=requests.ConnectionError("expected!"),
            ):
                await self.connection.channel._request_text(
                    "get", "http://not-exists.com"
                )

    @pytest.mark.asyncio
    async def test_set_location(self):
        """Test internal method set location."""
        agent_location = Location(52.2057092, 2.1183431)
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(SOEFException, match=r"`set_position`.*Exception: .*"):
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
                SOEFException, match=r"`set_personality_piece` .*Exception: .*"
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
                shutil.rmtree(self.data_dir)
        except Exception:  # nosec
            pass

    @pytest.mark.asyncio
    async def test__set_value(self):
        """Test set pieces."""
        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            with pytest.raises(
                SOEFException, match=r"`set_personality_piece`.*Exception:"
            ):
                await self.connection.channel._set_personality_piece(1, 1)

        resp_text = '<?xml version="1.0" encoding="UTF-8"?><response><success>1</success></response>'
        with patch.object(
            self.connection.channel, "_request_text", make_async(resp_text)
        ):
            await self.connection.channel._set_personality_piece(1, 1)

    def test_chain_identifier_fail(self):
        """Test fail on invalid chain id."""
        chain_identifier = "test"
        identity = Identity("identity", "", "")

        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="s-oef.fetch.ai",
            soef_port=443,
            restricted_to_protocols={OefSearchMessage.protocol_specification_id},
            connection_id=SOEFConnection.connection_id,
            chain_identifier=chain_identifier,
        )
        with pytest.raises(ValueError, match="Unsupported chain_identifier"):
            SOEFConnection(
                configuration=configuration, data_dir=MagicMock(), identity=identity,
            )

    def test_chain_identifier_ok(self):
        """Test set valid chain id."""
        chain_identifier = "fetchai_cosmos"
        identity = Identity("identity", "", "")

        configuration = ConnectionConfig(
            api_key="TwiCIriSl0mLahw17pyqoA",
            soef_addr="s-oef.fetch.ai",
            soef_port=443,
            restricted_to_protocols={OefSearchMessage.protocol_specification_id},
            connection_id=SOEFConnection.connection_id,
            chain_identifier=chain_identifier,
        )
        connection = SOEFConnection(
            configuration=configuration, data_dir=MagicMock(), identity=identity,
        )

        assert connection.channel.chain_identifier == chain_identifier

    @pytest.mark.asyncio
    async def test_ping_command(self):
        """Test set service key."""
        service_description = Description({}, data_model=models.PING_MODEL)
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)

        with patch.object(
            self.connection.channel,
            "_request_text",
            make_async(self.generic_success_response),
        ):
            await self.connection.send(envelope)

        response = await asyncio.wait_for(self.connection.receive(), timeout=1)
        assert response.message.performative == OefSearchMessage.Performative.SUCCESS
        assert response.message.agents_info.body == {}

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
            with patch.object(
                self.connection.channel, "_ping_command", return_value=wrap_future(None)
            ) as mocked_ping:
                await self.connection.channel._register_agent()

                assert self.connection.channel._ping_periodic_task is not None
                await asyncio.sleep(0.3)
                assert mocked_ping.call_count > 1
