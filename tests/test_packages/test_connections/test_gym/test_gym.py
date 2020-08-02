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
import copy
import logging
import os
from typing import cast
from unittest.mock import patch

import gym

import pytest

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope


from packages.fetchai.connections.gym.connection import GymConnection
from packages.fetchai.protocols.gym.dialogues import GymDialogue, GymDialogues
from packages.fetchai.protocols.gym.message import GymMessage

from tests.conftest import ROOT_DIR, UNKNOWN_PROTOCOL_PUBLIC_ID

logger = logging.getLogger(__name__)


class TestGymConnection:
    """Test the packages/connection/gym/connection.py."""

    def setup(self):
        """Initialise the class."""
        self.env = gym.GoalEnv()
        configuration = ConnectionConfig(connection_id=GymConnection.connection_id)
        self.agent_address = "my_address"
        identity = Identity("name", address=self.agent_address)
        self.gym_con = GymConnection(
            gym_env=self.env, identity=identity, configuration=configuration
        )
        self.loop = asyncio.get_event_loop()
        self.gym_address = str(GymConnection.connection_id)
        self.dialogues = GymDialogues(self.gym_address)

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
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"hello",
        )

        with pytest.raises(ValueError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_connection_error(self):
        """Test send connection error."""
        msg = GymMessage(
            performative=GymMessage.Performative.RESET,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
        )
        msg.counterparty = self.gym_address
        sending_dialogue = self.dialogues.update(msg)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )

        with pytest.raises(ConnectionError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_act(self):
        """Test send act message."""
        sending_dialogue = await self.send_reset()
        last_message = sending_dialogue.last_message
        assert last_message is not None
        msg = GymMessage(
            performative=GymMessage.Performative.ACT,
            action=GymMessage.AnyObject("any_action"),
            step_id=1,
            dialogue_reference=sending_dialogue.dialogue_label.dialogue_reference,
            message_id=last_message.message_id + 1,
            target=last_message.message_id,
        )
        msg.counterparty = self.gym_address
        assert sending_dialogue.update(msg)
        envelope = Envelope(
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        observation = 1
        reward = 1.0
        done = True
        info = "some info"
        with patch.object(
            self.env, "step", return_value=(observation, reward, done, info)
        ) as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

        response = await asyncio.wait_for(self.gym_con.receive(), timeout=3)
        response_msg_orig = cast(GymMessage, response.message)
        response_msg = copy.copy(response_msg_orig)
        response_msg.is_incoming = True
        response_msg.counterparty = response_msg_orig.sender
        response_dialogue = self.dialogues.update(response_msg)

        assert response_msg.performative == GymMessage.Performative.PERCEPT
        assert response_msg.step_id == msg.step_id
        assert response_msg.observation.any == observation
        assert response_msg.reward == reward
        assert response_msg.done == done
        assert response_msg.info.any == info
        assert sending_dialogue == response_dialogue

    @pytest.mark.asyncio
    async def test_send_reset(self):
        """Test send reset message."""
        _ = await self.send_reset()

    @pytest.mark.asyncio
    async def test_send_close(self):
        """Test send close message."""
        sending_dialogue = await self.send_reset()
        last_message = sending_dialogue.last_message
        assert last_message is not None
        msg = GymMessage(
            performative=GymMessage.Performative.CLOSE,
            dialogue_reference=sending_dialogue.dialogue_label.dialogue_reference,
            message_id=last_message.message_id + 1,
            target=last_message.message_id,
        )
        msg.counterparty = self.gym_address
        assert sending_dialogue.update(msg)
        envelope = Envelope(
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        with patch.object(self.env, "close") as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

    @pytest.mark.asyncio
    async def test_send_close_negative(self, caplog):
        """Test send close message with invalid reference and message id and target."""
        msg = GymMessage(
            performative=GymMessage.Performative.CLOSE,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
        )
        msg.counterparty = self.gym_address
        envelope = Envelope(
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        with caplog.at_level(logging.DEBUG, "aea.packages.fetchai.connections.gym"):
            await self.gym_con.send(envelope)
            assert "Could not create dialogue for message=" in caplog.text

    async def send_reset(self) -> GymDialogue:
        """Send a reset."""
        msg = GymMessage(
            performative=GymMessage.Performative.RESET,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
        )
        msg.counterparty = self.gym_address
        sending_dialogue = self.dialogues.update(msg)
        assert sending_dialogue is not None
        envelope = Envelope(
            to=self.gym_address,
            sender=self.agent_address,
            protocol_id=GymMessage.protocol_id,
            message=msg,
        )
        await self.gym_con.connect()

        with patch.object(self.env, "reset") as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

        response = await asyncio.wait_for(self.gym_con.receive(), timeout=3)
        response_msg_orig = cast(GymMessage, response.message)
        response_msg = copy.copy(response_msg_orig)
        response_msg.is_incoming = True
        response_msg.counterparty = response_msg_orig.sender
        response_dialogue = self.dialogues.update(response_msg)

        assert response_msg.performative == GymMessage.Performative.STATUS
        assert response_msg.content == {"reset": "success"}
        assert sending_dialogue == response_dialogue
        return sending_dialogue

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
        identity = Identity("name", address=self.agent_address)
        gym_con = GymConnection(
            gym_env=None, identity=identity, configuration=configuration
        )
        assert gym_con.channel.gym_env is not None
        os.chdir(curdir)
