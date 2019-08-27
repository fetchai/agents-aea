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
import logging
import queue
import threading
from queue import Queue
from threading import Thread
from typing import Dict, Optional

from aea.mail.base import Envelope, Connection
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer

logger = logging.getLogger(__name__)


"""default 'to' field for Gym envelopes."""
DEFAULT_GYM = "gym"

gym_Env = object  # typing stub for gym.Env


class GymChannel:
    """A ."""

    def __init__(self, gym_env: gym_Env):
        """Initialize a gym channel."""
        self.gym_env = gym_env
        self._lock = threading.Lock()

        self._queues = {}  # type: Dict[str, Queue]

    def connect(self, public_key: str) -> Optional[Queue]:
        """
        Connect a public key to the gym.

        :param public_key: the public key of the agent.
        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if public_key in self._queues:
            return None

        assert len(self._queues.keys()) <= 1, "Only one public key can register to a gym."
        q = Queue()
        self._queues[public_key] = q
        return q

    def send_envelope(self, envelope: Envelope) -> None:
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
        assert GymMessage.Performative(performative) == GymMessage.Performative.ACT, "This is not a valid message."
        action = gym_message.get("action")
        step_id = gym_message.get("step_id")
        observation, reward, done, info = self.gym_env.step(action)  # type: Tuple[any, any, bool, Dict]
        msg = GymMessage(performative=GymMessage.Performative.PERCEPT, observation=observation, reward=reward, done=done, info=info, step_id=step_id)
        msg_bytes = GymSerializer().encode(msg)
        envelope = Envelope(to=envelope.sender, sender=DEFAULT_GYM, protocol_id=GymMessage.protocol_id, message=msg_bytes)
        self._send(envelope)

    def _send(self, envelope: Envelope) -> None:
        """Send a message.

        :param envelope: the envelope
        :return: None
        """
        destination = envelope.to
        self._queues[destination].put_nowait(envelope)

    def disconnect(self, public_key: str) -> None:
        """
        Disconnect.

        :param public_key: the public key
        :return: None
        """
        with self._lock:
            self._queues.pop(public_key, None)


class GymConnection(Connection):
    """Proxy to the functionality of the gym."""

    def __init__(self, public_key: str, gym_channel: GymChannel):
        """
        Initialize a connection to a local gym environment.

        :param public_key: the public key used in the protocols.
        :param gym: the gym environment.
        """
        super().__init__()
        self.public_key = public_key
        self.gym_channel = gym_channel

        self._connection = None  # type: Optional[Queue]

        self._stopped = True
        self.in_thread = None
        self.out_thread = None

    def _fetch(self) -> None:
        """
        Fetch the envelopes from the outqueue and send them.

        :return: None
        """
        while not self._stopped:
            try:
                envelope = self.out_queue.get(block=True, timeout=2.0)
                self.send(envelope)
            except queue.Empty:
                pass

    def _receive_loop(self) -> None:
        """
        Receive messages.

        :return: None
        """
        while not self._stopped:
            try:
                data = self._connection.get(timeout=2.0)
                self.in_queue.put_nowait(data)
            except queue.Empty:
                pass

    @property
    def is_established(self) -> bool:
        """Return True if the connection has been established, False otherwise."""
        return self._connection is not None

    def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        if self._stopped:
            self._stopped = False
            self._connection = self.gym_channel.connect(self.public_key)
            self.in_thread = Thread(target=self._receive_loop)
            self.out_thread = Thread(target=self._fetch)
            self.in_thread.start()
            self.out_thread.start()

    def disconnect(self) -> None:
        """
        Disconnect from the gym.

        :return: None
        """
        if not self._stopped:
            self._stopped = True
            self.in_thread.join()
            self.out_thread.join()
            self.in_thread = None
            self.out_thread = None
            self.gym_channel.disconnect(self.public_key)
            self.stop()

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        if not self.is_established:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self.gym_channel.send_envelope(envelope)

    def stop(self) -> None:
        """
        Tear down the connection.

        :return: None
        """
        self._connection = None
