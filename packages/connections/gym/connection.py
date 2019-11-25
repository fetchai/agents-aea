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
import sys
import threading
from asyncio import CancelledError
from typing import Dict, Optional, cast, TYPE_CHECKING

import gym

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.helpers.base import locate
from aea.mail.base import Envelope

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.gym.message import GymMessage
    from packages.protocols.gym.serialization import GymSerializer
else:
    from gym_protocol.message import GymMessage
    from gym_protocol.serialization import GymSerializer

logger = logging.getLogger(__name__)


"""default 'to' field for Gym envelopes."""
DEFAULT_GYM = "gym"


class GymChannel:
    """A wrapper of the gym environment."""

    def __init__(self, public_key: str, gym_env: gym.Env):
        """Initialize a gym channel."""
        self.public_key = public_key
        self.gym_env = gym_env
        self._lock = threading.Lock()

        self._queues = {}  # type: Dict[str, asyncio.Queue]

    def connect(self) -> Optional[asyncio.Queue]:
        """
        Connect a public key to the gym.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if self.public_key in self._queues:
            return None

        assert len(self._queues.keys()) == 0, "Only one public key can register to a gym."
        q = asyncio.Queue()  # type: asyncio.Queue
        self._queues[self.public_key] = q
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
        if envelope.protocol_id == "gym":
            self.handle_gym_message(envelope)
        else:
            raise ValueError('This protocol is not valid for gym.')

    def handle_gym_message(self, envelope: Envelope) -> None:
        """
        Forward a message to gym.

        :param envelope: the envelope
        :return: None
        """
        gym_message = GymSerializer().decode(envelope.message)
        performative = gym_message.get("performative")
        if GymMessage.Performative(performative) == GymMessage.Performative.ACT:
            action = gym_message.get("action")
            step_id = gym_message.get("step_id")
            observation, reward, done, info = self.gym_env.step(action)  # type: ignore
            msg = GymMessage(performative=GymMessage.Performative.PERCEPT, observation=observation, reward=reward, done=done, info=info, step_id=step_id)
            msg_bytes = GymSerializer().encode(msg)
            envelope = Envelope(to=envelope.sender, sender=DEFAULT_GYM, protocol_id=GymMessage.protocol_id, message=msg_bytes)
            self._send(envelope)
        elif GymMessage.Performative(performative) == GymMessage.Performative.RESET:
            self.gym_env.reset()  # type: ignore
        elif GymMessage.Performative(performative) == GymMessage.Performative.CLOSE:
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
            self._queues.pop(self.public_key, None)


class GymConnection(Connection):
    """Proxy to the functionality of the gym."""

    restricted_to_protocols = {"gym"}

    def __init__(self, public_key: str, gym_env: gym.Env, connection_id: str = "gym", **kwargs):
        """
        Initialize a connection to a local gym environment.

        :param public_key: the public key used in the protocols.
        :param gym_env: the gym environment.
        :param connection_id: the connection id.
        """
        super().__init__(connection_id=connection_id, **kwargs)
        self.public_key = public_key
        self.channel = GymChannel(public_key, gym_env)

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
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """Receive an envelope."""
        if not self.connection_status.is_connected:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        try:
            assert self._connection is not None
            envelope = await self._connection.get()
            if envelope is None:
                return None
            return envelope
        except CancelledError:
            return None

    def stop(self) -> None:
        """
        Tear down the connection.

        :return: None
        """
        self._connection = None

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the Gym connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        gym_env_package = cast(str, connection_configuration.config.get('env'))
        gym_env = locate(gym_env_package)
        return GymConnection(public_key, gym_env(),
                             connection_id=connection_configuration.name,
                             restricted_to_protocols=set(connection_configuration.restricted_to_protocols))
