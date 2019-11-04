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
from abc import ABC, abstractmethod
from queue import Queue
from typing import Optional, TYPE_CHECKING, List

from aea.configurations.base import Address, ProtocolId
from aea.mail import base_pb2
if TYPE_CHECKING:
    from aea.connections.base import Connection  # pragma: no cover

logger = logging.getLogger(__name__)


class EnvelopeContext:
    """Extra information for the handling of an envelope."""

    def __init__(self, connection_id: Optional[str] = None):
        """Initialize the envelope context."""
        self.connection_id = connection_id

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, EnvelopeContext) \
            and self.connection_id == other.connection_id


class EnvelopeSerializer(ABC):
    """This abstract class let the devloper to specify serialization layer for the envelope."""

    @abstractmethod
    def encode(self, envelope: 'Envelope') -> bytes:
        """Encode the envelope."""

    @abstractmethod
    def decode(self, envelope_bytes: bytes) -> 'Envelope':
        """Decode the envelope."""


class ProtobufEnvelopeSerializer(EnvelopeSerializer):
    """Envelope serializer using Protobuf."""

    def encode(self, envelope: 'Envelope') -> bytes:
        """Encode the envelope."""
        envelope_pb = base_pb2.Envelope()
        envelope_pb.to = envelope.to
        envelope_pb.sender = envelope.sender
        envelope_pb.protocol_id = envelope.protocol_id
        envelope_pb.message = envelope.message

        envelope_bytes = envelope_pb.SerializeToString()
        return envelope_bytes

    def decode(self, envelope_bytes: bytes) -> 'Envelope':
        """Decode the envelope."""
        envelope_pb = base_pb2.Envelope()
        envelope_pb.ParseFromString(envelope_bytes)

        to = envelope_pb.to
        sender = envelope_pb.sender
        protocol_id = envelope_pb.protocol_id
        message = envelope_pb.message

        envelope = Envelope(to=to, sender=sender,
                            protocol_id=protocol_id, message=message)
        return envelope


DefaultEnvelopeSerializer = ProtobufEnvelopeSerializer


class Envelope:
    """The top level message class."""

    default_serializer = DefaultEnvelopeSerializer()

    def __init__(self, to: Address,
                 sender: Address,
                 protocol_id: ProtocolId,
                 message: bytes,
                 context: Optional[EnvelopeContext] = None):
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
        self._context = context if context is not None else EnvelopeContext()  # type: Optional[EnvelopeContext]

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

    @property
    def context(self) -> Optional[EnvelopeContext]:
        """Get the envelope context."""
        return self._context

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Envelope) \
            and self.to == other.to \
            and self.sender == other.sender \
            and self.protocol_id == other.protocol_id \
            and self._message == other._message \
            and self.context == other.context

    def encode(self, serializer: Optional[EnvelopeSerializer] = None) -> bytes:
        """
        Encode the envelope.

        :param serializer: the serializer that implements the encoding procedure.
        :return: the encoded envelope.
        """
        if serializer is None:
            serializer = self.default_serializer
        envelope_bytes = serializer.encode(self)
        return envelope_bytes

    @classmethod
    def decode(cls, envelope_bytes: bytes, serializer: Optional[EnvelopeSerializer] = None) -> 'Envelope':
        """
        Decode the envelope.

        :param envelope_bytes: the bytes to be decoded.
        :param serializer: the serializer that implements the decoding procedure.
        :return: the decoded envelope.
        """
        if serializer is None:
            serializer = cls.default_serializer
        envelope = serializer.decode(envelope_bytes)
        return envelope

    def __str__(self):
        """Get the string representation of an envelope."""
        return "Envelope(to={to}, sender={sender}, protocol_id={protocol_id}, message={message})"\
            .format(to=self.to, sender=self.sender, protocol_id=self.protocol_id, message=self.message)


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
        Check for a envelope on the in queue.

        :return: boolean indicating whether there is a message or not
        """
        return self._queue.empty()

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Envelope:
        """
        Check for a envelope on the in queue.

        :param block: if true makes it blocking.
        :param timeout: times out the block after timeout seconds.

        :return: the envelope object.
        :raises Empty: if the attempt to get a message fails.
        """
        logger.debug("Checks for message from the in queue...")
        envelope = self._queue.get(block=block, timeout=timeout)
        logger.debug("Incoming message: to='{}' sender='{}' protocol_id='{}' message='{}'"
                     .format(envelope.to, envelope.sender, envelope.protocol_id, envelope.message))
        return envelope

    def get_nowait(self) -> Optional[Envelope]:
        """
        Check for a envelope on the in queue and wait for no time.

        :return: the envelope object
        """
        envelope = self._queue.get_nowait()
        return envelope


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
        Check for a envelope on the out queue.

        :return: boolean indicating whether there is a envelope or not
        """
        return self._queue.empty()

    def put(self, envelope: Envelope) -> None:
        """
        Put an envelope into the queue.

        :param envelope: the envelope.
        :return: None
        """
        logger.debug("Put an envelope in the queue: to='{}' sender='{}' protocol_id='{}' message='{!r}'..."
                     .format(envelope.to, envelope.sender, envelope.protocol_id, envelope.message))
        self._queue.put(envelope)

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


class Multiplexer:
    """This class can handle multiple connections at once."""

    def __init__(self, connections: List['Connection']):
        """
        Initialize the connection multiplexer.

        :param connections: the connections.
        """
        self.connections = connections


class MailBox(object):
    """Abstract definition of a mailbox."""

    def __init__(self, connection: 'Connection'):
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
