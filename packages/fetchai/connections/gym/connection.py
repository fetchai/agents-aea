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
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional, Union, cast

import gym

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.helpers.base import locate
from aea.mail.base import Address, Envelope

from packages.fetchai.protocols.gym.message import GymMessage

logger = logging.getLogger("aea.packages.fetchai.connections.gym")


"""default 'to' field for Gym envelopes."""
DEFAULT_GYM = "gym"
PUBLIC_ID = PublicId.from_str("fetchai/gym:0.4.0")


class GymChannel:
    """A wrapper of the gym environment."""

    THREAD_POOL_SIZE = 3

    def __init__(self, address: Address, gym_env: gym.Env):
        """Initialize a gym channel."""
        self.address = address
        self.gym_env = gym_env
        self._loop: Optional[AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue] = None
        self._threaded_pool: ThreadPoolExecutor = ThreadPoolExecutor(
            self.THREAD_POOL_SIZE
        )
        self.logger: Union[logging.Logger, logging.LoggerAdapter] = logger

    @property
    def queue(self) -> asyncio.Queue:
        """Check queue is set and return queue."""
        if self._queue is None:  # pragma: nocover
            raise ValueError("Channel is not connected")
        return self._queue

    async def connect(self) -> None:
        """
        Connect an address to the gym.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if self._queue:  # pragma: nocover
            return None
        self._loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()

    async def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes to the gym.

        :return: None
        """
        sender = envelope.sender
        self.logger.debug("Processing message from {}: {}".format(sender, envelope))
        if envelope.protocol_id != GymMessage.protocol_id:
            raise ValueError("This protocol is not valid for gym.")
        await self.handle_gym_message(envelope)

    async def _run_in_executor(self, fn, *args):
        return await self._loop.run_in_executor(self._threaded_pool, fn, *args)

    async def handle_gym_message(self, envelope: Envelope) -> None:
        """
        Forward a message to gym.

        :param envelope: the envelope
        :return: None
        """
        assert isinstance(
            envelope.message, GymMessage
        ), "Message not of type GymMessage"
        gym_message = cast(GymMessage, envelope.message)
        if gym_message.performative == GymMessage.Performative.ACT:
            action = gym_message.action.any
            step_id = gym_message.step_id

            observation, reward, done, info = await self._run_in_executor(
                self.gym_env.step, action
            )

            msg = GymMessage(
                performative=GymMessage.Performative.PERCEPT,
                observation=GymMessage.AnyObject(observation),
                reward=reward,
                done=done,
                info=GymMessage.AnyObject(info),
                step_id=step_id,
            )
            envelope = Envelope(
                to=envelope.sender,
                sender=DEFAULT_GYM,
                protocol_id=GymMessage.protocol_id,
                message=msg,
            )
            await self._send(envelope)
        elif gym_message.performative == GymMessage.Performative.RESET:
            await self._run_in_executor(self.gym_env.reset)
        elif gym_message.performative == GymMessage.Performative.CLOSE:
            await self._run_in_executor(self.gym_env.close)

    async def _send(self, envelope: Envelope) -> None:
        """Send a message.

        :param envelope: the envelope
        :return: None
        """
        assert envelope.to == self.address, "Invalid destination address"
        await self.queue.put(envelope)

    async def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        if self._queue is not None:
            await self._queue.put(None)
            self._queue = None

    async def get(self) -> Optional[Envelope]:
        """Get incoming envelope."""
        return await self.queue.get()


class GymConnection(Connection):
    """Proxy to the functionality of the gym."""

    connection_id = PUBLIC_ID

    def __init__(self, gym_env: Optional[gym.Env] = None, **kwargs):
        """
        Initialize a connection to a local gym environment.

        :param gym_env: the gym environment (this cannot be loaded by AEA loader).
        :param kwargs: the keyword arguments of the parent class.
        """
        super().__init__(**kwargs)
        if gym_env is None:
            gym_env_package = cast(str, self.configuration.config.get("env"))
            assert gym_env_package is not None, "env must be set!"
            gym_env_class = locate(gym_env_package)
            gym_env = gym_env_class()
        self.channel = GymChannel(self.address, gym_env)
        self._connection = None  # type: Optional[asyncio.Queue]

    async def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.connection_status.is_connected = True
            self.channel.logger = self.logger
            await self.channel.connect()

    async def disconnect(self) -> None:
        """
        Disconnect from the gym.

        :return: None
        """
        if self.connection_status.is_connected:
            self.connection_status.is_connected = False
            await self.channel.disconnect()

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
        await self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Receive an envelope."""
        if not self.connection_status.is_connected:
            raise ConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )
        try:
            envelope = await self.channel.get()
            return envelope
        except CancelledError:  # pragma: no cover
            return None
