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
"""This module contains the tests of the gym connection module."""
import asyncio
import logging
import os
from unittest.mock import patch

import gym

import pytest

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.gym.connection import GymConnection
from packages.fetchai.protocols.gym.message import GymMessage

from tests.conftest import ROOT_DIR, UNKNOWN_PROTOCOL_PUBLIC_ID

logger = logging.getLogger(__name__)


class TestGymConnection:
    """Test the packages/connection/gym/connection.py."""

    def setup(self):
        """Initialise the class."""
        self.env = gym.GoalEnv()
        configuration = ConnectionConfig(connection_id=GymConnection.connection_id)
        self.my_address = "my_key"
        identity = Identity("name", address=self.my_address)
        self.gym_con = GymConnection(
            gym_env=self.env, identity=identity, configuration=configuration
        )
        self.loop = asyncio.get_event_loop()

    def teardown(self):
        """Clean up after tests."""
        self.loop.run_until_complete(self.gym_con.disconnect())

    @pytest.mark.asyncio
    async def test_gym_connection_connect(self):
        """Test the connection None return value after connect()."""
        assert self.gym_con.channel._queue is None
        await self.gym_con.channel.connect()
        assert self.gym_con.channel._queue is not None

    @pytest.mark.asyncio
    async def test_decode_envelope_error(self):
        """Test the decoding error for the envelopes."""
        await self.gym_con.connect()
        envelope = Envelope(
            to="_to_key",
            sender=self.my_address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"hello",
        )

        with pytest.raises(ValueError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_connection_error(self):
        """Test send connection error."""
        msg = GymMessage(
            performative=GymMessage.Performative.ACT,
            action=GymMessage.AnyObject("any_action"),
            step_id=1,
        )
        msg.counterparty = "_to_key"
        envelope = Envelope(
            to="_to_key",
            sender="_from_key",
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )

        with pytest.raises(ConnectionError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_act(self):
        """Test send act message."""
        msg = GymMessage(
            performative=GymMessage.Performative.ACT,
            action=GymMessage.AnyObject("any_action"),
            step_id=1,
        )
        msg.counterparty = "_to_key"
        envelope = Envelope(
            to="_to_key",
            sender=self.my_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        with patch.object(
            self.env, "step", return_value=(1, 1.0, True, "some info")
        ) as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

        assert await asyncio.wait_for(self.gym_con.receive(), timeout=3) is not None

    @pytest.mark.asyncio
    async def test_send_reset(self):
        """Test send reset message."""
        msg = GymMessage(performative=GymMessage.Performative.RESET,)
        msg.counterparty = "_to_key"
        envelope = Envelope(
            to="_to_key",
            sender=self.my_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        with pytest.raises(gym.error.Error):
            await self.gym_con.send(envelope)

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(self.gym_con.receive(), timeout=0.5)

    @pytest.mark.asyncio
    async def test_send_close(self):
        """Test send close message."""
        msg = GymMessage(performative=GymMessage.Performative.CLOSE,)
        msg.counterparty = "_to_key"
        envelope = Envelope(
            to="_to_key",
            sender=self.my_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        await self.gym_con.send(envelope)

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(self.gym_con.receive(), timeout=0.5)

    @pytest.mark.asyncio
    async def test_receive_connection_error(self):
        """Test receive connection error and Cancel Error."""
        with pytest.raises(ConnectionError):
            await self.gym_con.receive()

    def test_gym_env_load(self):
        """Load gym env from file."""
        curdir = os.getcwd()
        os.chdir(os.path.join(ROOT_DIR, "examples", "gym_ex"))
        gym_env_path = "gyms.env.BanditNArmedRandom"
        configuration = ConnectionConfig(
            connection_id=GymConnection.connection_id, env=gym_env_path
        )
        identity = Identity("name", address=self.my_address)
        gym_con = GymConnection(
            gym_env=None, identity=identity, configuration=configuration
        )
        assert gym_con.channel.gym_env is not None
        os.chdir(curdir)
