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
from typing import Any, Callable, Dict, Optional, Tuple, Union, cast

import gym

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.helpers.base import locate
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.gym.dialogues import GymDialogue
from packages.fetchai.protocols.gym.dialogues import GymDialogues as BaseGymDialogues
from packages.fetchai.protocols.gym.message import GymMessage


_default_logger = logging.getLogger("aea.packages.fetchai.connections.gym")

PUBLIC_ID = PublicId.from_str("fetchai/gym:0.19.0")


class GymDialogues(BaseGymDialogues):
    """The dialogues class keeps track of all gym dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The gym connection maintains the dialogue on behalf of the environment
            return GymDialogue.Role.ENVIRONMENT

        BaseGymDialogues.__init__(
            self,
            self_address=str(PUBLIC_ID),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


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
        self.logger: Union[logging.Logger, logging.LoggerAdapter] = _default_logger
        self._dialogues = GymDialogues()

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[GymMessage, Optional[GymDialogue]]:
        """
        Get a message copy and dialogue related to this message.

        :param envelope: incoming envelope

        :return: Tuple[Message, Optional[Dialogue]]
        """
        message = cast(GymMessage, envelope.message)
        dialogue = cast(GymDialogue, self._dialogues.update(message))
        return message, dialogue

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

        :param envelope: the envelope
        """
        sender = envelope.sender
        self.logger.debug("Processing message from {}: {}".format(sender, envelope))
        if envelope.protocol_specification_id != GymMessage.protocol_specification_id:
            raise ValueError("This protocol is not valid for gym.")
        await self.handle_gym_message(envelope)

    async def _run_in_executor(
        self, fn: Callable, *args: Any
    ) -> Tuple[Any, float, bool, Dict]:
        if self._loop is None:  # pragma: nocover
            raise ValueError("Loop not set!")
        return await self._loop.run_in_executor(self._threaded_pool, fn, *args)

    async def handle_gym_message(self, envelope: Envelope) -> None:
        """
        Forward a message to gym.

        :param envelope: the envelope
        """
        enforce(
            isinstance(envelope.message, GymMessage), "Message not of type GymMessage"
        )
        gym_message, dialogue = self._get_message_and_dialogue(envelope)

        if dialogue is None:
            self.logger.warning(
                "Could not create dialogue from message={}".format(gym_message)
            )
            return

        if gym_message.performative == GymMessage.Performative.ACT:
            action = gym_message.action.any
            step_id = gym_message.step_id

            observation, reward, done, info = await self._run_in_executor(
                self.gym_env.step, action
            )

            msg = dialogue.reply(
                performative=GymMessage.Performative.PERCEPT,
                target_message=gym_message,
                observation=GymMessage.AnyObject(observation),
                reward=reward,
                done=done,
                info=GymMessage.AnyObject(info),
                step_id=step_id,
            )
        elif gym_message.performative == GymMessage.Performative.RESET:
            await self._run_in_executor(self.gym_env.reset)
            msg = dialogue.reply(
                performative=GymMessage.Performative.STATUS,
                target_message=gym_message,
                content={"reset": "success"},
            )
        elif gym_message.performative == GymMessage.Performative.CLOSE:
            await self._run_in_executor(self.gym_env.close)
            return
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        await self._send(envelope)

    async def _send(self, envelope: Envelope) -> None:
        """Send a message.

        :param envelope: the envelope
        """
        await self.queue.put(envelope)

    async def disconnect(self) -> None:
        """Disconnect."""
        if self._queue is not None:
            await self._queue.put(None)
            self._queue = None

    async def get(self) -> Optional[Envelope]:
        """Get incoming envelope."""
        return await self.queue.get()


class GymConnection(Connection):
    """Proxy to the functionality of the gym."""

    connection_id = PUBLIC_ID

    def __init__(self, gym_env: Optional[gym.Env] = None, **kwargs: Any) -> None:
        """
        Initialize a connection to a local gym environment.

        :param gym_env: the gym environment (this cannot be loaded by AEA loader).
        :param kwargs: the keyword arguments of the parent class.
        """
        super().__init__(**kwargs)
        if gym_env is None:
            gym_env_package = cast(str, self.configuration.config.get("env"))
            if gym_env_package is None:  # pragma: nocover
                raise ValueError("`env` must be set in configuration!")
            gym_env_class = locate(gym_env_package)
            gym_env = gym_env_class()
        self.channel = GymChannel(self.address, gym_env)
        self._connection = None  # type: Optional[asyncio.Queue]

    async def connect(self) -> None:
        """Connect to the gym."""
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            self.channel.logger = self.logger
            await self.channel.connect()

    async def disconnect(self) -> None:
        """Disconnect from the gym."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        """
        self._ensure_connected()
        await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """Receive an envelope."""
        self._ensure_connected()
        try:
            envelope = await self.channel.get()
            return envelope
        except CancelledError:  # pragma: no cover
            return None
