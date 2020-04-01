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

"""Gym connector and gym channel."""

import asyncio
import logging
import threading
from asyncio import CancelledError
from typing import Dict, Optional, cast

import gym

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.helpers.base import locate
from aea.mail.base import Address, Envelope

from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.protocols.gym.serialization import GymSerializer

logger = logging.getLogger(__name__)


"""default 'to' field for Gym envelopes."""
DEFAULT_GYM = "gym"


class GymChannel:
    """A wrapper of the gym environment."""

    def __init__(self, address: Address, gym_env: gym.Env):
        """Initialize a gym channel."""
        self.address = address
        self.gym_env = gym_env
        self._lock = threading.Lock()

        self._queues = {}  # type: Dict[str, asyncio.Queue]

    def connect(self) -> Optional[asyncio.Queue]:
        """
        Connect an address to the gym.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if self.address in self._queues:
            return None

        assert len(self._queues.keys()) == 0, "Only one address can register to a gym."
        q = asyncio.Queue()  # type: asyncio.Queue
        self._queues[self.address] = q
        return q

    def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes to the gym.

        :return: None
        """
        sender = envelope.sender
        logger.debug("Processing message from {}: {}".format(sender, envelope))
        self._decode_envelope(envelope)

    def _decode_envelope(self, envelope: Envelope) -> None:
        """
        Decode the envelope.

        :param envelope: the envelope
        :return: None
        """
        if envelope.protocol_id == PublicId.from_str("fetchai/gym:0.1.0"):
            self.handle_gym_message(envelope)
        else:
            raise ValueError("This protocol is not valid for gym.")

    def handle_gym_message(self, envelope: Envelope) -> None:
        """
        Forward a message to gym.

        :param envelope: the envelope
        :return: None
        """
        gym_message = GymSerializer().decode(envelope.message)
        gym_message = cast(GymMessage, gym_message)
        if gym_message.performative == GymMessage.Performative.ACT:
            action = gym_message.action.any
            step_id = gym_message.step_id
            observation, reward, done, info = self.gym_env.step(action)  # type: ignore
            msg = GymMessage(
                performative=GymMessage.Performative.PERCEPT,
                observation=GymMessage.AnyObject(observation),
                reward=reward,
                done=done,
                info=GymMessage.AnyObject(info),
                step_id=step_id,
            )
            msg_bytes = GymSerializer().encode(msg)
            envelope = Envelope(
                to=envelope.sender,
                sender=DEFAULT_GYM,
                protocol_id=GymMessage.protocol_id,
                message=msg_bytes,
            )
            self._send(envelope)
        elif gym_message.performative == GymMessage.Performative.RESET:
            self.gym_env.reset()  # type: ignore
        elif gym_message.performative == GymMessage.Performative.CLOSE:
            self.gym_env.close()  # type: ignore

    def _send(self, envelope: Envelope) -> None:
        """Send a message.

        :param envelope: the envelope
        :return: None
        """
        destination = envelope.to
        self._queues[destination].put_nowait(envelope)

    def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        with self._lock:
            self._queues.pop(self.address, None)


class GymConnection(Connection):
    """Proxy to the functionality of the gym."""

    def load(self) -> None:
        """Load the connection configuration."""
        gym_env_package = cast(str, self.configuration.config.get("env"))
        gym_env_class = locate(gym_env_package)
        self.channel = GymChannel(self.address, gym_env_class())
        self._connection = None  # type: Optional[asyncio.Queue]

    async def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.connection_status.is_connected = True
            self._connection = self.channel.connect()

    async def disconnect(self) -> None:
        """
        Disconnect from the gym.

        :return: None
        """
        if self.connection_status.is_connected:
            assert self._connection is not None
            self.connection_status.is_connected = False
            await self._connection.put(None)
            self.channel.disconnect()
            self._connection = None
            self.stop()

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        if not self.connection_status.is_connected:
            raise ConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )
        self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Receive an envelope."""
        if not self.connection_status.is_connected:
            raise ConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )
        try:
            assert self._connection is not None
            envelope = await self._connection.get()
            if envelope is None:
                return None
            return envelope
        except CancelledError:  # pragma: no cover
            return None

    def stop(self) -> None:
        """
        Tear down the connection.

        :return: None
        """
        self._connection = None
