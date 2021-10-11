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
from typing import cast
from unittest.mock import MagicMock, patch

import gym
import pytest

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.gym.connection import GymConnection
from packages.fetchai.protocols.gym.dialogues import GymDialogue
from packages.fetchai.protocols.gym.dialogues import GymDialogues as BaseGymDialogues
from packages.fetchai.protocols.gym.message import GymMessage

from tests.conftest import ROOT_DIR, UNKNOWN_PROTOCOL_PUBLIC_ID


logger = logging.getLogger(__name__)


class GymDialogues(BaseGymDialogues):
    """The dialogues class keeps track of all gym dialogues."""

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
            return GymDialogue.Role.AGENT

        BaseGymDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


class TestGymConnection:
    """Test the packages/connection/gym/connection.py."""

    def setup(self):
        """Initialise the class."""
        self.env = gym.GoalEnv()
        configuration = ConnectionConfig(connection_id=GymConnection.connection_id)
        self.agent_address = "my_address"
        self.agent_public_key = "my_public_key"
        identity = Identity(
            "name", address=self.agent_address, public_key=self.agent_public_key
        )
        self.gym_con = GymConnection(
            gym_env=self.env,
            identity=identity,
            configuration=configuration,
            data_dir=MagicMock(),
        )
        self.loop = asyncio.get_event_loop()
        self.gym_address = str(GymConnection.connection_id)
        self.skill_id = "some/skill:0.1.0"
        self.dialogues = GymDialogues(self.skill_id)

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
            sender=self.skill_id,
            protocol_specification_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=b"hello",
        )

        with pytest.raises(ValueError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_connection_error(self):
        """Test send connection error."""
        msg, sending_dialogue = self.dialogues.create(
            counterparty=self.gym_address, performative=GymMessage.Performative.RESET,
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)

        with pytest.raises(ConnectionError):
            await self.gym_con.send(envelope)

    @pytest.mark.asyncio
    async def test_send_act(self):
        """Test send act message."""
        sending_dialogue = await self.send_reset()
        assert sending_dialogue.last_message is not None
        msg = sending_dialogue.reply(
            performative=GymMessage.Performative.ACT,
            action=GymMessage.AnyObject("any_action"),
            step_id=1,
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
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
        response_msg = cast(GymMessage, response.message)
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
        assert sending_dialogue.last_message is not None
        msg = sending_dialogue.reply(performative=GymMessage.Performative.CLOSE,)
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        await self.gym_con.connect()

        with patch.object(self.env, "close") as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

    @pytest.mark.asyncio
    async def test_send_close_negative(self):
        """Test send close message with invalid reference and message id and target."""
        incorrect_msg = GymMessage(
            performative=GymMessage.Performative.CLOSE,
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
        )
        incorrect_msg.to = self.gym_address
        incorrect_msg.sender = self.skill_id

        # the incorrect message cannot be sent into a dialogue, so this is omitted.

        envelope = Envelope(
            to=incorrect_msg.to,
            sender=incorrect_msg.sender,
            protocol_specification_id=incorrect_msg.protocol_specification_id,
            message=incorrect_msg,
        )
        await self.gym_con.connect()

        with patch.object(self.gym_con.channel.logger, "warning") as mock_logger:
            await self.gym_con.send(envelope)
            mock_logger.assert_any_call(
                f"Could not create dialogue from message={incorrect_msg}"
            )

    async def send_reset(self) -> GymDialogue:
        """Send a reset."""
        msg, sending_dialogue = self.dialogues.create(
            counterparty=self.gym_address, performative=GymMessage.Performative.RESET,
        )
        assert sending_dialogue is not None
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        await self.gym_con.connect()

        with patch.object(self.env, "reset") as mock:
            await self.gym_con.send(envelope)
            mock.assert_called()

        response = await asyncio.wait_for(self.gym_con.receive(), timeout=3)
        response_msg = cast(GymMessage, response.message)
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
        identity = Identity(
            "name", address=self.agent_address, public_key=self.agent_public_key
        )
        gym_con = GymConnection(
            gym_env=None,
            identity=identity,
            configuration=configuration,
            data_dir=MagicMock(),
        )
        assert gym_con.channel.gym_env is not None
        os.chdir(curdir)
