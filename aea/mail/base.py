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
import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop, Queue
from concurrent.futures import CancelledError, TimeoutError
from threading import Thread, Lock
from typing import Optional, TYPE_CHECKING, List, Tuple, Dict

from aea.configurations.base import Address, ProtocolId
from aea.mail import base_pb2

if TYPE_CHECKING:
    from aea.connections.base import Connection, AEAConnectionError  # pragma: no cover

logger = logging.getLogger(__name__)


class Empty(Exception):
    """Exception for when the inbox is empty."""


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
            and self.message == other.message \
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


class Multiplexer:
    """This class can handle multiple connections at once."""

    def __init__(self, connections: List['Connection'], default_connection_index: int = 0,
                 loop: Optional[AbstractEventLoop] = None):
        """
        Initialize the connection multiplexer.

        :param connections: the connections.
        """
        assert len(connections) > 0, "List of connections cannot be empty."
        assert 0 <= default_connection_index <= len(connections) - 1, "Default connection index out of range."
        assert len(set(c.connection_id for c in connections)) == len(connections), "Connection names must be unique."
        self._connections = connections  # type: List[Connection]
        self._name_to_connection = {c.connection_id: c for c in connections}  # type: Dict[str, Connection]
        self.default_connection = self._connections[default_connection_index]  # type: Connection

        self._lock = Lock()
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._thread = Thread(target=self._run_loop)

        self._in_queue = Queue()
        self._out_queue = Queue()

    @property
    def in_queue(self) -> Queue:
        """Get the in queue"""
        return self._in_queue

    @property
    def out_queue(self) -> Queue:
        """Get the out queue"""
        return self._out_queue

    @property
    def connections(self) -> Tuple['Connection']:
        """Get the connections."""
        return tuple(self._connections)

    @property
    def is_connected(self) -> bool:
        """Check whether the multiplexer is processing messages."""
        with self._lock:
            return self._thread.is_alive() and all(c.is_established for c in self._connections)

    def connect(self) -> None:
        """Connect the multiplexer."""
        with self._lock:
            self._start()
            asyncio.run_coroutine_threadsafe(self._connect_all(), loop=self._loop).result()
            asyncio.run_coroutine_threadsafe(self._recv_loop(), loop=self._loop)
            asyncio.run_coroutine_threadsafe(self._send_loop(), loop=self._loop)

    def disconnect(self) -> None:
        """Disconnect the multiplexer."""
        with self._lock:
            asyncio.run_coroutine_threadsafe(self._disconnect_all(), loop=self._loop).result()
            self._stop()

    def _run_loop(self):
        """Run the asyncio loop.

        This method is supposed to be run only in the Multiplexer thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _start(self):
        """Start the multiplexer."""
        if not self._loop.is_running() and not self._thread.is_alive():
            self._thread.start()
        logger.debug("Multiplexer started.")

    def _stop(self):
        """Start the multiplexer."""
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive():
            self._thread.join()
        logger.debug("Multiplexer stopped.")

    async def _connect_all(self):
        """Set all the connection up."""
        logger.debug("Start multiplexer connections.")
        for connection_id, connection in self._name_to_connection.items():
            try:
                await self._connect_one(connection_id)
            except Exception as e:
                logger.error("Error while connecting {}: {}".format(str(type(connection)), str(e)))

    async def _connect_one(self, connection_id: str) -> None:
        """
        Set a connection up.

        :param connection_id: the id of the connection.
        :return: None
        """
        connection = self._name_to_connection[connection_id]
        logger.debug("Processing connection {}".format(connection.connection_id))
        if connection.is_established:
            logger.debug("Connection {} already established.".format(connection.connection_id))
        else:
            await connection.connect()
            logger.debug("Connection {} has been set up successfully.".format(connection.connection_id))

    async def _disconnect_all(self):
        """Tear all the connections down."""
        logger.debug("Tear the multiplexer connections down.")
        for connection_id, connection in self._name_to_connection.items():
            try:
                await self._disconnect_one(connection_id)
            except Exception as e:
                logger.error("Error while connecting {}: {}".format(str(type(connection)), str(e)))

    async def _disconnect_one(self, connection_id: str) -> None:
        """
        Tear a connection down.

        :param connection_id: the id of the connection.
        :return: None
        """
        connection = self._name_to_connection[connection_id]
        logger.debug("Processing connection {}".format(connection.connection_id))
        if not connection.is_established:
            logger.debug("Connection {} already disconnected.".format(connection.connection_id))
        else:
            await connection.disconnect()
            logger.debug("Connection {} has been disconnected successfully.".format(connection.connection_id))

    async def _send_loop(self):
        """Process the outgoing messages."""
        loop = asyncio.get_running_loop()
        try:
            logger.debug("Waiting for outgoing messages...")
            envelope = await self.out_queue.get()
            logger.debug("Sending envelope {}".format(str(envelope)))
            await self._send(envelope)
        except asyncio.CancelledError:
            logger.debug("Sending loop cancelled.")
            return
        except Exception as e:
            logger.error("Error: {}".format(str(e)))

        await self._send_loop()

    async def _recv_loop(self):
        """Process incoming messages."""
        loop = asyncio.get_running_loop()
        logger.debug("Waiting for incoming messages...")
        task_to_connection = {asyncio.ensure_future(conn.recv()): conn for conn in self.connections}

        while True:
            try:
                done, pending = await asyncio.wait(task_to_connection.keys(),
                                                   return_when=asyncio.FIRST_COMPLETED,
                                                   loop=loop)

                for task in done:
                    envelope = task.result()
                    self.in_queue.put_nowait(envelope)
                    connection = task_to_connection.pop(task)
                    new_task = asyncio.ensure_future(connection.recv())
                    task_to_connection[new_task] = connection

            except asyncio.CancelledError:
                logger.debug("Receiving loop cancelled.")
            except Exception as e:
                logger.error("Error in the receiving loop: {}".format(str(e)))
                await asyncio.sleep(1.0)

    async def _send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        :raises ValueError: if the connection id provided is not valid.
        :raises AEAConnectionError: if the connection id provided is not valid.
        """
        envelope_context = envelope.context
        connection_id = envelope_context.connection_id

        if connection_id is not None and connection_id not in self._name_to_connection:
            raise AEAConnectionError("No connection registered with id: {}.".format(connection_id))

        connection = self._name_to_connection.get(connection_id, None)
        if connection is None:
            logger.debug("Using default connection.".format(connection_id))
            connection = self.default_connection

        try:
            await connection.send(envelope)
        except Exception as e:
            raise AEAConnectionError(e)

    def get(self, timeout: float = 0.0) -> Optional[Envelope]:
        """
        Get an envelope within a timeout.

        :param timeout: the timeout to wait until an envelope is received.
        :return: the envelope, or None if no envelope is available within a timeout.
        """
        future = asyncio.run_coroutine_threadsafe(self._in_queue.get(), self._loop)
        try:
            return future.result(timeout)
        except (CancelledError, TimeoutError):
            return None


class InBox(object):
    """A queue from where you can only consume messages."""

    def __init__(self, multiplexer: Multiplexer):
        """
        Initialize the inbox.

        :param multiplexer: the multiplexer
        """
        super().__init__()
        self._multiplexer = multiplexer

    def empty(self) -> bool:
        """
        Check for a envelope on the in queue.

        :return: boolean indicating whether there is a message or not
        """
        return self._multiplexer.in_queue.empty()

    def get(self, timeout: float = 0.0) -> Envelope:
        """
        Check for a envelope on the in queue.

        :param timeout: times out the block after timeout seconds.

        :return: the envelope object.
        :raises Empty: if the attempt to get a message fails.
        """
        logger.debug("Checks for message from the in queue...")
        envelope = self._multiplexer.get(timeout=timeout)
        if envelope is None:
            raise Empty()
        logger.debug("Incoming message: to='{}' sender='{}' protocol_id='{}' message='{}'"
                     .format(envelope.to, envelope.sender, envelope.protocol_id, envelope.message))
        return envelope

    def get_nowait(self) -> Optional[Envelope]:
        """
        Check for a envelope on the in queue and wait for no time.

        :return: the envelope object
        """
        envelope = self.get(0.0)
        return envelope


class OutBox(object):
    """A queue from where you can only enqueue messages."""

    def __init__(self, multiplexer: Multiplexer):
        """
        Initialize the outbox.

        :param multiplexer: the multiplexer
        """
        super().__init__()
        self._multiplexer = multiplexer

    def empty(self) -> bool:
        """
        Check for a envelope on the in queue.

        :return: boolean indicating whether there is a message or not
        """
        return self._multiplexer.out_queue.empty()

    def put(self, envelope: Envelope) -> None:
        """
        Put an envelope into the queue.

        :param envelope: the envelope.
        :return: None
        """
        logger.debug("Put an envelope in the queue: to='{}' sender='{}' protocol_id='{}' message='{!r}'..."
                     .format(envelope.to, envelope.sender, envelope.protocol_id, envelope.message))
        self._multiplexer.out_queue.put_nowait(envelope)

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
        self._multiplexer.out_queue.put(envelope)


class MailBox(object):
    """Abstract definition of a mailbox."""

    def __init__(self, connections: List['Connection']):
        """Initialize the mailbox."""
        self._connections = connections

        self._multiplexer = Multiplexer(connections)
        self.inbox = InBox(self._multiplexer)
        self.outbox = OutBox(self._multiplexer)

    @property
    def is_connected(self) -> bool:
        """Check whether the mailbox is processing messages."""
        return self._multiplexer.is_connected

    def connect(self) -> None:
        """Connect."""
        self._multiplexer.connect()

    def disconnect(self) -> None:
        """Disconnect."""
        self._multiplexer.disconnect()

    def send(self, out: Envelope) -> None:
        """Send an envelope."""
        self.outbox.put(out)
