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
import logging
import time
import urllib
from threading import Thread
from typing import Any, Dict, Optional, Tuple, cast
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from defusedxml import ElementTree as ET  # pylint: disable=wrong-import-order

from aea.configurations.base import ConnectionConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.soef.connection import SOEFConnection
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from .test_soef import OefSearchDialogues
from tests.common.utils import wait_for_condition
from tests.test_packages.test_connections.test_soef import models


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def make_multiplexer_and_dialogues() -> Tuple[
    Multiplexer, OefSearchDialogues, Crypto, SOEFConnection
]:
    """Return multplexer, dialogues and crypto instances."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity(
        "identity", address=crypto.address, public_key=crypto.public_key
    )
    skill_id = "some/skill:0.1.0"
    oef_search_dialogues = OefSearchDialogues(skill_id)

    # create the connection and multiplexer objects
    configuration = ConnectionConfig(
        api_key="TwiCIriSl0mLahw17pyqoA",
        soef_addr="s-oef.fetch.ai",
        soef_port=443,
        restricted_to_protocols={
            OefSearchMessage.protocol_specification_id,
            OefSearchMessage.protocol_id,
        },
        connection_id=SOEFConnection.connection_id,
    )
    soef_connection = SOEFConnection(
        configuration=configuration, data_dir=MagicMock(), identity=identity,
    )
    multiplexer = Multiplexer([soef_connection])
    return multiplexer, oef_search_dialogues, crypto, soef_connection


class Instance:
    """Test agent instance."""

    def __init__(self, location: Location) -> None:
        """Init instance with location provided."""
        self.location = location
        (
            self.multiplexer,
            self.oef_search_dialogues,
            self.crypto,
            self.connection,
        ) = make_multiplexer_and_dialogues()
        self.thread = Thread(target=self.multiplexer.connect)

    @property
    def address(self) -> str:
        """Get agent adress."""
        return self.crypto.address

    def start(self) -> None:
        """Start multipelxer."""
        self.thread.start()
        wait_for_condition(lambda: self.multiplexer.is_connected, timeout=5)
        self.register_location()

    def stop(self):
        """Stop multipelxer and wait."""
        self.multiplexer.disconnect()
        self.thread.join()

    def register_location(self, disclosure_accuracy: Optional[str] = None) -> None:
        """Register location."""
        service_instance: Dict[str, Any] = {"location": self.location}

        if disclosure_accuracy:
            service_instance["disclosure_accuracy"] = disclosure_accuracy

        service_description = Description(
            service_instance, data_model=models.AGENT_LOCATION_MODEL
        )
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        logger.info(
            "Registering agent at location=({},{}) by agent={}".format(
                self.location.latitude, self.location.longitude, self.crypto.address,
            )
        )
        self.multiplexer.put(envelope)
        # check for register results
        envelope = self.get()
        assert envelope
        message = cast(OefSearchMessage, envelope.message)
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    def wait_registered(self) -> None:
        """Wait connection gets unique_page_address."""
        wait_for_condition(
            lambda: self.connection.channel.unique_page_address, timeout=10
        )

    def register_personality_pieces(
        self, piece: str = "genus", value: str = "service"
    ) -> None:
        """Register personality pieces."""
        service_instance = {"piece": piece, "value": value}
        service_description = Description(
            service_instance, data_model=models.AGENT_PERSONALITY_MODEL
        )
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        logger.info("Registering agent personality")
        self.multiplexer.put(envelope)
        # check for register results
        envelope = self.get()
        assert envelope
        message = cast(OefSearchMessage, envelope.message)
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    def register_service_key(self, key: str, value: str) -> None:
        """Register service key."""
        service_instance = {"key": "test", "value": "test"}
        service_description = Description(
            service_instance, data_model=models.SET_SERVICE_KEY_MODEL
        )
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        logger.info("Registering agent service key")
        self.multiplexer.put(envelope)
        # check for register results
        envelope = self.get()
        assert envelope
        message = cast(OefSearchMessage, envelope.message)
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue

    def search(self, query: Query) -> OefSearchMessage:
        """Perform search with query provided."""
        message, sending_dialogue = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=query,
        )
        search_envelope = Envelope(
            to=message.to, sender=message.sender, message=message,
        )
        logger.info(f"Searching for agents with query: {query}")
        self.multiplexer.put(search_envelope)

        # check for search results
        envelope = self.get()
        assert envelope
        message = cast(OefSearchMessage, envelope.message)
        receiving_dialogue = self.oef_search_dialogues.update(message)
        assert sending_dialogue == receiving_dialogue
        return message

    def get(self):
        """Get an instance."""
        wait_for_condition(lambda: not self.multiplexer.in_queue.empty(), timeout=20)
        return self.multiplexer.get()

    def generic_command(self, command: str, parameters: Optional[dict] = None) -> None:
        """Register personality pieces."""
        service_instance = {"command": command}

        if parameters:
            service_instance["parameters"] = urlencode(parameters)

        service_description = Description(
            service_instance, data_model=models.AGENT_GENERIC_COMMAND_MODEL
        )
        message, _ = self.oef_search_dialogues.create(
            counterparty=str(SOEFConnection.connection_id.to_any()),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=service_description,
        )
        envelope = Envelope(to=message.to, sender=message.sender, message=message,)
        logger.info(f"Send generic command {command} {parameters}")
        self.multiplexer.put(envelope)


class TestRealNetwork:
    """Perform tests using real soef server."""

    LOCATION = (52.2057092, 2.1183431)

    @pytest.mark.integration
    def test_search_no_filters(self):
        """Perform tests over real networ with no filters."""
        agent_location = Location(*self.LOCATION)
        agent = Instance(agent_location)
        agent2 = Instance(agent_location)

        try:
            agent.start()
            agent2.start()
            agent.wait_registered()
            agent2.wait_registered()
            time.sleep(2)
            # find agents near me
            radius = 0.1
            close_to_my_service = Constraint(
                "location", ConstraintType("distance", (agent_location, radius))
            )
            closeness_query = Query(
                [close_to_my_service], model=models.AGENT_LOCATION_MODEL
            )

            # search for agents close to me
            message = agent.search(closeness_query)
            assert message.performative == OefSearchMessage.Performative.SEARCH_RESULT
            assert len(message.agents) >= 1

            # second message in a raw to check we dont hit limit
            message = agent.search(closeness_query)
            assert message.performative == OefSearchMessage.Performative.SEARCH_RESULT
            assert len(message.agents) >= 1

            assert agent2.address in message.agents
        finally:
            agent.stop()
            agent2.stop()

    @pytest.mark.integration
    def test_search_filters(self):
        """Test find agents near me with filter."""
        agent_location = Location(*self.LOCATION)
        agent = Instance(agent_location)
        agent2 = Instance(agent_location)
        agent3 = Instance(agent_location)
        agent.start()
        agent2.start()
        agent3.start()

        try:
            agent2.register_personality_pieces(piece="genus", value="service")
            agent2.register_service_key(key="test", value="test")
            agent2.register_location(disclosure_accuracy="medium")

            agent3.register_personality_pieces(piece="genus", value="service")
            agent3.register_service_key(key="test", value="test")
            time.sleep(3)

            radius = 0.1
            close_to_my_service = Constraint(
                "location", ConstraintType("distance", (agent_location, radius))
            )
            personality_filters = [
                Constraint("genus", ConstraintType("==", "service")),
            ]
            service_key_filters = [
                Constraint("test", ConstraintType("==", "test")),
            ]
            constraints = (
                [close_to_my_service] + personality_filters + service_key_filters
            )

            closeness_query = Query(constraints)
            logger.info(
                "Searching for agents in radius={} of myself at location=({},{}) with personality filters".format(
                    radius, agent_location.latitude, agent_location.longitude,
                )
            )
            message = agent.search(closeness_query)
            assert message.performative == OefSearchMessage.Performative.SEARCH_RESULT
            assert len(message.agents) >= 1
            assert agent2.address in message.agents
            assert agent3.address in message.agents

            agent2_info = message.agents_info.get_info_for_agent(agent2.address)
            assert agent2_info
            assert "name" in agent2_info
            assert "location" in agent2_info
            assert agent2_info["genus"] == "service"

            agent3_info = message.agents_info.get_info_for_agent(agent3.address)
            assert agent3_info
            assert "name" in agent3_info
            assert "location" not in agent3_info
            assert agent3_info["genus"] == "service"

        finally:
            agent.stop()
            agent2.stop()
            agent3.stop()

    @pytest.mark.integration
    def test_ping(self):
        """Test ping command."""
        agent_location = Location(*self.LOCATION)
        agent = Instance(agent_location)
        agent.start()
        try:
            service_description = Description({}, data_model=models.PING_MODEL)
            message, _ = agent.oef_search_dialogues.create(
                counterparty=str(SOEFConnection.connection_id.to_any()),
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=service_description,
            )
            envelope = Envelope(
                to=message.to, sender="some/skill:0.1.0", message=message,
            )
            logger.info("Pinging")
            agent.multiplexer.put(envelope)
            envelope = agent.get()
            assert (
                envelope.message.performative == OefSearchMessage.Performative.SUCCESS
            )

        finally:
            agent.stop()

    @pytest.mark.integration
    def test_generic_command(self):
        """Test generic command."""
        agent_location = Location(*self.LOCATION)
        agent = Instance(agent_location)
        agent.start()

        try:
            agent.generic_command("set_service_key", {"key": "test", "value": "test"})
            envelope = agent.get()
            assert (
                envelope.message.performative == OefSearchMessage.Performative.SUCCESS
            )
            ET.fromstring(envelope.message.agents_info.body["response"]["content"])

            agent.generic_command("bad_command")
            envelope = agent.get()
            assert (
                envelope.message.performative == OefSearchMessage.Performative.OEF_ERROR
            )

        finally:
            agent.stop()

    @pytest.mark.integration
    def test_generic_command_set_declared_name(self):
        """Test generic command."""
        agent_location = Location(*self.LOCATION)
        agent1 = Instance(agent_location)
        agent1.start()
        agent2 = Instance(agent_location)
        agent2.start()

        declared_name = "new_declared_name"
        try:
            # send generic command."""
            service_description = Description(
                {
                    "command": "set_declared_name",
                    "parameters": urllib.parse.urlencode({"name": declared_name}),
                },
                data_model=models.AGENT_GENERIC_COMMAND_MODEL,
            )
            message, _ = agent1.oef_search_dialogues.create(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=service_description,
                counterparty=str(SOEFConnection.connection_id.to_any()),
            )

            envelope = Envelope(to=message.to, sender=message.sender, message=message,)
            agent1.multiplexer.put(envelope)

            envelope = agent1.get()
            assert (
                envelope.message.performative == OefSearchMessage.Performative.SUCCESS
            )

            radius = 0.1
            close_to_my_service = Constraint(
                "location", ConstraintType("distance", (agent_location, radius))
            )
            closeness_query = Query(
                [close_to_my_service], model=models.AGENT_LOCATION_MODEL
            )

            message = agent2.search(closeness_query)
            assert message.performative == OefSearchMessage.Performative.SEARCH_RESULT
            assert len(message.agents) >= 1

            assert agent1.address in message.agents_info.body
            assert message.agents_info.body[agent1.address]["name"] == declared_name

        finally:
            agent1.stop()
            agent2.stop()
