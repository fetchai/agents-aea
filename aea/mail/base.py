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

"""Mail module abstract base classes."""

import logging
from abc import abstractmethod, ABC
from queue import Queue
from typing import Optional

from aea.mail import base_pb2
from aea.configurations.base import ConnectionConfig, Address, ProtocolId

logger = logging.getLogger(__name__)


class Envelope:
    """The top level message class."""

    def __init__(self, to: Address,
                 sender: Address,
                 protocol_id: ProtocolId,
                 message: bytes):
        """
        Initialize a Message object.

        :param to: the public key of the receiver.
        :param sender: the public key of the sender.
        :param protocol_id: the protocol id.
        :param message: the protocol-specific message
        """
        self._to = to
        self._sender = sender
        self._protocol_id = protocol_id
        self._message = message
        assert type(self._to) == str or self._to is None
        try:
            if self._to is not None and type(self._to) == str:
                self._to.encode('utf-8')
        except Exception:
            assert False

    @property
    def to(self) -> Address:
        """Get public key of receiver."""
        return self._to

    @to.setter
    def to(self, to: Address) -> None:
        """Set public key of receiver."""
        self._to = to

    @property
    def sender(self) -> Address:
        """Get public key of sender."""
        return self._sender

    @sender.setter
    def sender(self, sender: Address) -> None:
        """Set public key of sender."""
        self._sender = sender

    @property
    def protocol_id(self) -> ProtocolId:
        """Get protocol id."""
        return self._protocol_id

    @protocol_id.setter
    def protocol_id(self, protocol_id: ProtocolId) -> None:
        """Set the protocol id."""
        self._protocol_id = protocol_id

    @property
    def message(self) -> bytes:
        """Get the Message."""
        return self._message

    @message.setter
    def message(self, message: bytes) -> None:
        """Set the message."""
        self._message = message

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Envelope) \
            and self.to == other.to \
            and self.sender == other.sender \
            and self.protocol_id == other.protocol_id \
            and self._message == other._message

    def encode(self) -> bytes:
        """
        Encode the envelope.

        :return: the encoded envelope.
        """
        envelope = self
        envelope_pb = base_pb2.Envelope()
        envelope_pb.to = envelope.to
        envelope_pb.sender = envelope.sender
        envelope_pb.protocol_id = envelope.protocol_id
        envelope_pb.message = envelope.message

        envelope_bytes = envelope_pb.SerializeToString()
        return envelope_bytes

    @classmethod
    def decode(cls, envelope_bytes: bytes) -> 'Envelope':
        """
        Decode the envelope.

        :param envelope_bytes: the bytes to be decoded.
        :return: the decoded envelope.
        """
        envelope_pb = base_pb2.Envelope()
        envelope_pb.ParseFromString(envelope_bytes)

        to = envelope_pb.to
        sender = envelope_pb.sender
        protocol_id = envelope_pb.protocol_id
        message = envelope_pb.message

        envelope = Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)
        return envelope


class InBox(object):
    """A queue from where you can only consume messages."""

    def __init__(self, queue: Queue):
        """
        Initialize the inbox.

        :param queue: the queue.
        """
        super().__init__()
        self._queue = queue

    def empty(self) -> bool:
        """
        Check for a message on the in queue.

        :return: boolean indicating whether there is a message or not
        """
        return self._queue.empty()

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Envelope:
        """
        Check for a message on the in queue.

        :param block: if true makes it blocking.
        :param timeout: times out the block after timeout seconds.

        :return: the message object.
        :raises Empty: if the attempt to get a message fails.
        """
        logger.debug("Checks for message from the in queue...")
        msg = self._queue.get(block=block, timeout=timeout)
        logger.debug("Incoming message: to='{}' sender='{}' protocol_id='{}' message='{}'"
                     .format(msg.to, msg.sender, msg.protocol_id, msg.message))
        return msg

    def get_nowait(self) -> Optional[Envelope]:
        """
        Check for a message on the in queue and wait for no time.

        :return: the message object
        """
        item = self._queue.get_nowait()
        return item


class OutBox(object):
    """A queue from where you can only enqueue messages."""

    def __init__(self, queue: Queue) -> None:
        """
        Initialize the outbox.

        :param queue: the queue.
        """
        super().__init__()
        self._queue = queue

    def empty(self) -> bool:
        """
        Check for a message on the out queue.

        :return: boolean indicating whether there is a message or not
        """
        return self._queue.empty()

    def put(self, item: Envelope) -> None:
        """
        Put an item into the queue.

        :param item: the message.
        :return: None
        """
        logger.debug("Put a message in the queue: to='{}' sender='{}' protocol_id='{}' message='{}'..."
                     .format(item.to, item.sender, item.protocol_id, item.message))
        self._queue.put(item)

    def put_message(self, to: Address, sender: Address,
                    protocol_id: ProtocolId, message: bytes) -> None:
        """
        Put a message in the outbox.

        :param to: the recipient of the message.
        :param sender: the sender of the message.
        :param protocol_id: the protocol id.
        :param message: the content of the message.
        :return: None
        """
        envelope = Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)
        self._queue.put(envelope)


class Channel(ABC):
    """Abstract definition of a channel."""

    @abstractmethod
    def connect(self) -> Optional[Queue]:
        """
        Set up the connection.

        :return: A queue or None.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """

    @abstractmethod
    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """


class Connection(ABC):
    """Abstract definition of a connection."""

    channel: Channel

    def __init__(self):
        """Initialize the connection."""
        self.in_queue = Queue()
        self.out_queue = Queue()

    @abstractmethod
    def connect(self):
        """Set up the connection."""

    @abstractmethod
    def disconnect(self):
        """Tear down the connection."""

    @property
    @abstractmethod
    def is_established(self) -> bool:
        """Check if the connection is established."""

    @abstractmethod
    def send(self, envelope: Envelope):
        """Send a message."""

    @classmethod
    @abstractmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Initialize a connection instance from a configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration.
        :return: an instance of the concrete connection class.
        """


class MailBox(object):
    """Abstract definition of a mailbox."""

    def __init__(self, connection: Connection):
        """Initialize the mailbox."""
        self._connection = connection

        self.inbox = InBox(self._connection.in_queue)
        self.outbox = OutBox(self._connection.out_queue)

    @property
    def is_connected(self) -> bool:
        """Check whether the mailbox is processing messages."""
        return self._connection.is_established

    def connect(self) -> None:
        """Connect."""
        self._connection.connect()

    def disconnect(self) -> None:
        """Disconnect."""
        self._connection.disconnect()

    def send(self, out: Envelope) -> None:
        """Send."""
        self.outbox.put(out)
