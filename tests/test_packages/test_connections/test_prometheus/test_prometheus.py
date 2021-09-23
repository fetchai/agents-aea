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
"""This module contains the tests of the prometheus connection module."""
import asyncio
from typing import cast
from unittest.mock import MagicMock, Mock

import pytest

from aea.common import Address
from aea.configurations.base import ConnectionConfig, PublicId
from aea.exceptions import AEAEnforceError
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.prometheus.connection import (
    ConnectionStates,
    PrometheusConnection,
)
from packages.fetchai.protocols.prometheus.dialogues import PrometheusDialogue
from packages.fetchai.protocols.prometheus.dialogues import (
    PrometheusDialogues as BasePrometheusDialogues,
)
from packages.fetchai.protocols.prometheus.message import PrometheusMessage


class PrometheusDialogues(BasePrometheusDialogues):
    """The dialogues class keeps track of all prometheus dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

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
            return PrometheusDialogue.Role.AGENT

        BasePrometheusDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


class TestPrometheusConnection:
    """Test the packages/connection/prometheus/connection.py."""

    def setup(self):
        """Initialise the class."""
        self.metrics = {}
        configuration = ConnectionConfig(
            connection_id=PrometheusConnection.connection_id, port=9090,
        )
        self.some_skill = "some/skill:0.1.0"
        self.agent_address = "my_address"
        self.agent_public_key = "my_public_key"
        self.protocol_specification_id = PublicId.from_str("fetchai/prometheus:1.0.0")
        identity = Identity(
            "name", address=self.agent_address, public_key=self.agent_public_key
        )
        self.prometheus_con = PrometheusConnection(
            identity=identity, configuration=configuration, data_dir=MagicMock()
        )
        self.loop = asyncio.get_event_loop()
        self.prometheus_address = str(PrometheusConnection.connection_id)
        self.dialogues = PrometheusDialogues(self.some_skill)

    async def send_add_metric(self, title: str, metric_type: str) -> None:
        """Send an add_metric message."""
        msg, sending_dialogue = self.dialogues.create(
            counterparty=self.prometheus_address,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            title=title,
            type=metric_type,
            description="a gauge",
            labels={},
        )
        assert sending_dialogue is not None

        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        await self.prometheus_con.send(envelope)

    async def send_update_metric(self, title: str, update_func: str) -> None:
        """Send an update_metric message."""
        msg, sending_dialogue = self.dialogues.create(
            counterparty=self.prometheus_address,
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            title=title,
            callable=update_func,
            value=1.0,
            labels={},
        )
        assert sending_dialogue is not None
        assert sending_dialogue.last_message is not None

        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        await self.prometheus_con.send(envelope)

    def teardown(self):
        """Clean up after tests."""
        self.loop.run_until_complete(self.prometheus_con.disconnect())

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test connect."""
        assert (
            self.prometheus_con.state == ConnectionStates.disconnected
        ), "should not be connected yet"
        await self.prometheus_con.connect()
        assert (
            self.prometheus_con.state == ConnectionStates.connected
        ), "should be connected"

        # test add metric (correct)
        await self.send_add_metric("some_metric", "Gauge")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 200
        assert msg.message == "New Gauge successfully added: some_metric."

        # test add metric (already exists)
        await self.send_add_metric("some_metric", "Gauge")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 409
        assert msg.message == "Metric already exists."

        # test add metric (wrong type)
        await self.send_add_metric("cool_metric", "CoolBar")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 404
        assert msg.message == "CoolBar is not a recognized prometheus metric."

        # test update metric (inc: correct)
        await self.send_update_metric("some_metric", "inc")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 200
        assert msg.message == "Metric some_metric successfully updated."

        # test update metric (set: correct)
        await self.send_update_metric("some_metric", "set")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 200
        assert msg.message == "Metric some_metric successfully updated."

        # test update metric (doesn't exist)
        await self.send_update_metric("cool_metric", "inc")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 404
        assert msg.message == "Metric cool_metric not found."

        # test update metric (bad update function: not found in attr)
        await self.send_update_metric("some_metric", "go")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 400
        assert msg.message == "Update function go not found for metric some_metric."

        # test update metric (bad update function: found in getattr, not a method)
        await self.send_update_metric("some_metric", "name")
        envelope = await self.prometheus_con.receive()
        msg = cast(PrometheusMessage, envelope.message)
        assert msg.performative == PrometheusMessage.Performative.RESPONSE
        assert msg.code == 400
        assert (
            msg.message
            == "Failed to update metric some_metric: name is not a valid update function."
        )

        # Test that invalid message is rejected.
        with pytest.raises(AEAEnforceError):
            envelope = Envelope(
                to="some_address", sender="me", message=Mock(spec=Message),
            )
            await self.prometheus_con.channel.send(envelope)

        # Test that envelope without dialogue produces warning.
        msg = PrometheusMessage(
            PrometheusMessage.Performative.RESPONSE, code=0, message=""
        )
        envelope = Envelope(
            to=self.prometheus_address, sender=self.some_skill, message=msg,
        )
        await self.prometheus_con.channel.send(envelope)

        # Test that envelope with invalid protocol_specification_id raises error.
        with pytest.raises(ValueError):
            msg, _ = self.dialogues.create(
                counterparty=self.prometheus_address,
                performative=PrometheusMessage.Performative.UPDATE_METRIC,
                title="",
                callable="",
                value=1.0,
                labels={},
            )
            envelope = Envelope(
                to=self.prometheus_address, sender=self.some_skill, message=msg,
            )
            envelope._protocol_specification_id = "bad_id"
            await self.prometheus_con.channel.send(envelope)

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect."""
        await self.prometheus_con.disconnect()
        assert (
            self.prometheus_con.state == ConnectionStates.disconnected
        ), "should be disconnected"
