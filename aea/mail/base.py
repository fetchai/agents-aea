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
import queue
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop, CancelledError
from concurrent.futures import Future
from threading import Lock, Thread
from typing import Dict, List, Optional, Sequence, Tuple, cast
from urllib.parse import urlparse

from aea.configurations.base import ProtocolId, PublicId, SkillId
from aea.connections.base import Connection, ConnectionStatus
from aea.mail import base_pb2

logger = logging.getLogger(__name__)


Address = str


class AEAConnectionError(Exception):
    """Exception class for connection errors."""


class Empty(Exception):
    """Exception for when the inbox is empty."""


class URI:
    """URI following RFC3986."""

    def __init__(self, uri_raw: str):
        """
        Initialize the URI.

        Must follow: https://tools.ietf.org/html/rfc3986.html

        :param uri_raw: the raw form uri
        :raises ValueError: if uri_raw is not RFC3986 compliant
        """
        self.uri_raw = uri_raw
        parsed = urlparse(uri_raw)
        self._scheme = parsed.scheme
        self._netloc = parsed.netloc
        self._path = parsed.path
        self._params = parsed.params
        self._query = parsed.query
        self._fragment = parsed.fragment
        self._username = parsed.username
        self._password = parsed.password
        self._host = parsed.hostname
        self._port = parsed.port

    @property
    def scheme(self) -> str:
        """Get the scheme."""
        return self._scheme

    @property
    def netloc(self) -> str:
        """Get the netloc."""
        return self._netloc

    @property
    def path(self) -> str:
        """Get the path."""
        return self._path

    @property
    def params(self) -> str:
        """Get the params."""
        return self._params

    @property
    def query(self) -> str:
        """Get the query."""
        return self._query

    @property
    def fragment(self) -> str:
        """Get the fragment."""
        return self._fragment

    @property
    def username(self) -> Optional[str]:
        """Get the username."""
        return self._username

    @property
    def password(self) -> Optional[str]:
        """Get the password."""
        return self._password

    @property
    def host(self) -> Optional[str]:
        """Get the host."""
        return self._host

    @property
    def port(self) -> Optional[int]:
        """Get the port."""
        return self._port

    def __str__(self):
        """Get string representation."""
        return self.uri_raw

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, URI)
            and self.scheme == other.scheme
            and self.netloc == other.netloc
            and self.path == other.path
            and self.params == other.params
            and self.query == other.query
            and self.fragment == other.fragment
            and self.username == other.username
            and self.password == other.password
            and self.host == other.host
            and self.port == other.port
        )


class EnvelopeContext:
    """Extra information for the handling of an envelope."""

    def __init__(
        self, connection_id: Optional[PublicId] = None, uri: Optional[URI] = None
    ):
        """
        Initialize the envelope context.

        :param connection_id: the connection id used for routing the outgoing envelope in the multiplexer.
        :param uri: the URI sent with the envelope.
        """
        self.connection_id = connection_id
        self.uri = uri

    @property
    def uri_raw(self) -> str:
        """Get uri in string format."""
        return str(self.uri)

    def __str__(self):
        """Get the string representation."""
        return "EnvelopeContext(connection_id={connection_id}, uri_raw={uri_raw})".format(
            connection_id=str(self.connection_id), uri_raw=str(self.uri),
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, EnvelopeContext)
            and self.connection_id == other.connection_id
            and self.uri == other.uri
        )


class EnvelopeSerializer(ABC):
    """Abstract class to specify the serialization layer for the envelope."""

    @abstractmethod
    def encode(self, envelope: "Envelope") -> bytes:
        """
        Encode the envelope.

        :param envelope: the envelope to encode
        :return: the encoded envelope
        """

    @abstractmethod
    def decode(self, envelope_bytes: bytes) -> "Envelope":
        """
        Decode the envelope.

        :param envelope_bytes: the encoded envelope
        :return: the envelope
        """


class ProtobufEnvelopeSerializer(EnvelopeSerializer):
    """Envelope serializer using Protobuf."""

    def encode(self, envelope: "Envelope") -> bytes:
        """
        Encode the envelope.

        :param envelope: the envelope to encode
        :return: the encoded envelope
        """
        envelope_pb = base_pb2.Envelope()
        envelope_pb.to = envelope.to
        envelope_pb.sender = envelope.sender
        envelope_pb.protocol_id = str(envelope.protocol_id)
        envelope_pb.message = envelope.message
        if envelope.context is not None:
            envelope_pb.uri = envelope.context.uri_raw

        envelope_bytes = envelope_pb.SerializeToString()
        return envelope_bytes

    def decode(self, envelope_bytes: bytes) -> "Envelope":
        """
        Decode the envelope.

        :param envelope_bytes: the encoded envelope
        :return: the envelope
        """
        envelope_pb = base_pb2.Envelope()
        envelope_pb.ParseFromString(envelope_bytes)

        to = envelope_pb.to
        sender = envelope_pb.sender
        protocol_id = PublicId.from_str(envelope_pb.protocol_id)
        message = envelope_pb.message
        if envelope_pb.uri == "":  # empty string means this field is not set in proto3
            uri_raw = envelope_pb.uri
            uri = URI(uri_raw=uri_raw)
            context = EnvelopeContext(uri=uri)
            envelope = Envelope(
                to=to,
                sender=sender,
                protocol_id=protocol_id,
                message=message,
                context=context,
            )
        else:
            envelope = Envelope(
                to=to, sender=sender, protocol_id=protocol_id, message=message,
            )

        return envelope


DefaultEnvelopeSerializer = ProtobufEnvelopeSerializer


class Envelope:
    """The top level message class for agent to agent communication."""

    default_serializer = DefaultEnvelopeSerializer()

    def __init__(
        self,
        to: Address,
        sender: Address,
        protocol_id: ProtocolId,
        message: bytes,
        context: Optional[EnvelopeContext] = None,
    ):
        """
        Initialize a Message object.

        :param to: the address of the receiver.
        :param sender: the address of the sender.
        :param protocol_id: the protocol id.
        :param message: the protocol-specific message.
        :param context: the optional envelope context.
        """
        self._to = to
        self._sender = sender
        self._protocol_id = protocol_id
        self._message = message
        self._context = context if context is not None else EnvelopeContext()

    @property
    def to(self) -> Address:
        """Get address of receiver."""
        return self._to

    @to.setter
    def to(self, to: Address) -> None:
        """Set address of receiver."""
        self._to = to

    @property
    def sender(self) -> Address:
        """Get address of sender."""
        return self._sender

    @sender.setter
    def sender(self, sender: Address) -> None:
        """Set address of sender."""
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
        """Get the protocol-specific message."""
        return self._message

    @message.setter
    def message(self, message: bytes) -> None:
        """Set the protocol-specific message."""
        self._message = message

    @property
    def context(self) -> EnvelopeContext:
        """Get the envelope context."""
        return self._context

    @property
    def skill_id(self) -> Optional[SkillId]:
        """
        Get the skill id from an envelope context, if set.

        :return: skill id
        """
        skill_id = None  # Optional[PublicId]
        if self.context is not None and self.context.uri is not None:
            uri_path = self.context.uri.path
            try:
                skill_id = PublicId.from_uri_path(uri_path)
            except ValueError:
                logger.debug("URI - {} - not a valid skill id.".format(uri_path))
        return skill_id

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Envelope)
            and self.to == other.to
            and self.sender == other.sender
            and self.protocol_id == other.protocol_id
            and self.message == other.message
            and self.context == other.context
        )

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
    def decode(
        cls, envelope_bytes: bytes, serializer: Optional[EnvelopeSerializer] = None
    ) -> "Envelope":
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
        return "Envelope(to={to}, sender={sender}, protocol_id={protocol_id}, message={message})".format(
            to=self.to,
            sender=self.sender,
            protocol_id=self.protocol_id,
            message=self.message,
        )


class Multiplexer:
    """This class can handle multiple connections at once."""

    def __init__(
        self,
        connections: Sequence["Connection"],
        default_connection_index: int = 0,
        loop: Optional[AbstractEventLoop] = None,
    ):
        """
        Initialize the connection multiplexer.

        :param connections: a sequence of connections.
        :param default_connection_index: the index of the connection to use as default.
                                       | this information is used for envelopes which
                                       | don't specify any routing context.
        :param loop: the event loop to run the multiplexer. If None, a new event loop is created.
        """
        assert len(connections) > 0, "List of connections cannot be empty."
        assert (
            0 <= default_connection_index <= len(connections) - 1
        ), "Default connection index out of range."
        assert len(set(c.connection_id for c in connections)) == len(
            connections
        ), "Connection names must be unique."
        self._connections = connections  # type: Sequence[Connection]
        self._id_to_connection = {
            c.connection_id: c for c in connections
        }  # type: Dict[PublicId, Connection]
        self.default_connection = self._connections[
            default_connection_index
        ]  # type: Connection
        self._connection_status = ConnectionStatus()

        self._lock = Lock()
        self._loop = loop if loop is not None else asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop)

        self._in_queue = queue.Queue()  # type: queue.Queue
        self._out_queue = None  # type: Optional[asyncio.Queue]

        self._connect_all_task = None  # type: Optional[Future]
        self._disconnect_all_task = None  # type: Optional[Future]
        self._recv_loop_task = None  # type: Optional[Future]
        self._send_loop_task = None  # type: Optional[Future]

    @property
    def in_queue(self) -> queue.Queue:
        """Get the in queue."""
        return self._in_queue

    @property
    def out_queue(self) -> asyncio.Queue:
        """Get the out queue."""
        assert (
            self._out_queue is not None
        ), "Accessing out queue before loop is started."
        return self._out_queue

    @property
    def connections(self) -> Tuple["Connection"]:
        """Get the connections."""
        return cast(Tuple["Connection"], tuple(self._connections))

    @property
    def is_connected(self) -> bool:
        """Check whether the multiplexer is processing envelopes."""
        return self._loop.is_running() and all(
            c.connection_status.is_connected for c in self._connections
        )

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get the connection status."""
        return self._connection_status

    def connect(self) -> None:
        """Connect the multiplexer."""
        with self._lock:
            if self.connection_status.is_connected:
                logger.debug("Multiplexer already connected.")
                return
            self._start_loop_threaded_if_not_running()
            try:
                self._connect_all_task = asyncio.run_coroutine_threadsafe(
                    self._connect_all(), loop=self._loop
                )
                self._connect_all_task.result()
                self._connect_all_task = None
                assert self.is_connected, "At least one connection failed to connect!"
                self._connection_status.is_connected = True
                self._recv_loop_task = asyncio.run_coroutine_threadsafe(
                    self._receiving_loop(), loop=self._loop
                )
                self._send_loop_task = asyncio.run_coroutine_threadsafe(
                    self._send_loop(), loop=self._loop
                )
            except (CancelledError, Exception):
                self._connection_status.is_connected = False
                self._stop()
                raise AEAConnectionError("Failed to connect the multiplexer.")

    def disconnect(self) -> None:
        """Disconnect the multiplexer."""
        with self._lock:
            if not self.connection_status.is_connected:
                logger.debug("Multiplexer already disconnected.")
                self._stop()
                return
            try:
                logger.debug("Disconnecting the multiplexer...")
                self._disconnect_all_task = asyncio.run_coroutine_threadsafe(
                    self._disconnect_all(), loop=self._loop
                )
                self._disconnect_all_task.result()
                self._disconnect_all_task = None
                self._stop()
                self._connection_status.is_connected = False
            except (CancelledError, Exception):
                raise AEAConnectionError("Failed to disconnect the multiplexer.")

    def _run_loop(self):
        """
        Run the asyncio loop.

        This method is supposed to be run only in the Multiplexer thread.
        """
        logger.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._out_queue = asyncio.Queue()
        self._loop.run_forever()
        logger.debug("Asyncio loop has been stopped.")

    def _start_loop_threaded_if_not_running(self):
        """Start the multiplexer."""
        if not self._loop.is_running() and not self._thread.is_alive():
            self._thread.start()
        logger.debug("Multiplexer started.")

    def _stop(self):
        """Stop the multiplexer."""
        if self._recv_loop_task is not None and not self._recv_loop_task.done():
            self._recv_loop_task.cancel()

        if self._send_loop_task is not None and not self._send_loop_task.done():
            # send a 'stop' token (a None value) to wake up the coroutine waiting for outgoing envelopes.
            asyncio.run_coroutine_threadsafe(
                self.out_queue.put(None), self._loop
            ).result()
            self._send_loop_task.cancel()

        if self._connect_all_task is not None:
            self._connect_all_task.cancel()
        if self._disconnect_all_task is not None:
            self._disconnect_all_task.cancel()

        for connection in [
            c
            for c in self.connections
            if c.connection_status.is_connected or c.connection_status.is_connecting
        ]:
            asyncio.run_coroutine_threadsafe(
                connection.disconnect(), self._loop
            ).result()

        if self._loop.is_running() and not self._thread.is_alive():
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop.stop()
        elif self._loop.is_running() and self._thread.is_alive():
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
        logger.debug("Multiplexer stopped.")

    async def _connect_all(self):
        """Set all the connection up."""
        logger.debug("Start multiplexer connections.")
        connected = []  # type: List[PublicId]
        for connection_id, connection in self._id_to_connection.items():
            try:
                await self._connect_one(connection_id)
                connected.append(connection_id)
            except Exception as e:
                logger.error(
                    "Error while connecting {}: {}".format(
                        str(type(connection)), str(e)
                    )
                )
                for c in connected:
                    await self._disconnect_one(c)
                break

    async def _connect_one(self, connection_id: PublicId) -> None:
        """
        Set a connection up.

        :param connection_id: the id of the connection.
        :return: None
        """
        connection = self._id_to_connection[connection_id]
        logger.debug("Processing connection {}".format(connection.connection_id))
        if connection.connection_status.is_connected:
            logger.debug(
                "Connection {} already established.".format(connection.connection_id)
            )
        else:
            connection.loop = self._loop
            await connection.connect()
            logger.debug(
                "Connection {} has been set up successfully.".format(
                    connection.connection_id
                )
            )

    async def _disconnect_all(self):
        """Tear all the connections down."""
        logger.debug("Tear the multiplexer connections down.")
        for connection_id, connection in self._id_to_connection.items():
            try:
                await self._disconnect_one(connection_id)
            except Exception as e:
                logger.error(
                    "Error while disconnecting {}: {}".format(
                        str(type(connection)), str(e)
                    )
                )

    async def _disconnect_one(self, connection_id: PublicId) -> None:
        """
        Tear a connection down.

        :param connection_id: the id of the connection.
        :return: None
        """
        connection = self._id_to_connection[connection_id]
        logger.debug("Processing connection {}".format(connection.connection_id))
        if not connection.connection_status.is_connected:
            logger.debug(
                "Connection {} already disconnected.".format(connection.connection_id)
            )
        else:
            await connection.disconnect()
            logger.debug(
                "Connection {} has been disconnected successfully.".format(
                    connection.connection_id
                )
            )

    async def _send_loop(self):
        """Process the outgoing envelopes."""
        if not self.is_connected:
            logger.debug("Sending loop not started. The multiplexer is not connected.")
            return

        while self.is_connected:
            try:
                logger.debug("Waiting for outgoing envelopes...")
                envelope = await self.out_queue.get()
                if envelope is None:
                    logger.debug(
                        "Received empty envelope. Quitting the sending loop..."
                    )
                    return None
                logger.debug("Sending envelope {}".format(str(envelope)))
                await self._send(envelope)
            except asyncio.CancelledError:
                logger.debug("Sending loop cancelled.")
                return
            except AEAConnectionError as e:
                logger.error(str(e))
            except Exception as e:
                logger.error("Error in the sending loop: {}".format(str(e)))
                return

    async def _receiving_loop(self):
        """Process incoming envelopes."""
        logger.debug("Starting receving loop...")
        task_to_connection = {
            asyncio.ensure_future(conn.receive()): conn for conn in self.connections
        }

        while self.connection_status.is_connected and len(task_to_connection) > 0:
            try:
                logger.debug("Waiting for incoming envelopes...")
                done, _pending = await asyncio.wait(
                    task_to_connection.keys(), return_when=asyncio.FIRST_COMPLETED
                )

                # process completed receiving tasks.
                for task in done:
                    envelope = task.result()
                    if envelope is not None:
                        self.in_queue.put_nowait(envelope)

                    # reinstantiate receiving task, but only if the connection is still up.
                    connection = task_to_connection.pop(task)
                    if connection.connection_status.is_connected:
                        new_task = asyncio.ensure_future(connection.receive())
                        task_to_connection[new_task] = connection

            except asyncio.CancelledError:
                logger.debug("Receiving loop cancelled.")
                break
            except Exception as e:
                logger.error("Error in the receiving loop: {}".format(str(e)))
                break

        # cancel all the receiving tasks.
        for t in task_to_connection.keys():
            t.cancel()
        logger.debug("Receiving loop terminated.")

    async def _send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        :raises ValueError: if the connection id provided is not valid.
        :raises AEAConnectionError: if the connection id provided is not valid.
        """
        envelope_context = envelope.context
        connection_id = (
            envelope_context.connection_id if envelope_context is not None else None
        )

        if connection_id is not None and connection_id not in self._id_to_connection:
            raise AEAConnectionError(
                "No connection registered with id: {}.".format(connection_id)
            )

        connection = self._id_to_connection.get(connection_id, None)  # type: ignore
        if connection_id is None:
            logger.debug("Using default connection: {}".format(self.default_connection))
            connection = self.default_connection

        connection = cast(Connection, connection)
        if (
            len(connection.restricted_to_protocols) > 0
            and envelope.protocol_id not in connection.restricted_to_protocols
        ):
            logger.warning(
                "Connection {} cannot handle protocol {}. Cannot send the envelope.".format(
                    connection.connection_id, envelope.protocol_id
                )
            )
            return

        try:
            await connection.send(envelope)
        except Exception as e:  # pragma: no cover
            raise e

    def get(
        self, block: bool = False, timeout: Optional[float] = None
    ) -> Optional[Envelope]:
        """
        Get an envelope within a timeout.

        :param block: make the call blocking (ignore the timeout).
        :param timeout: the timeout to wait until an envelope is received.
        :return: the envelope, or None if no envelope is available within a timeout.
        """
        try:
            return self.in_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            raise Empty

    def put(self, envelope: Envelope) -> None:
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        :return: None
        """
        fut = asyncio.run_coroutine_threadsafe(self.out_queue.put(envelope), self._loop)
        fut.result()


class InBox:
    """A queue from where you can only consume envelopes."""

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

        :return: boolean indicating whether there is an envelope or not
        """
        return self._multiplexer.in_queue.empty()

    def get(self, block: bool = False, timeout: Optional[float] = None) -> Envelope:
        """
        Check for a envelope on the in queue.

        :param block: make the call blocking (ignore the timeout).
        :param timeout: times out the block after timeout seconds.

        :return: the envelope object.
        :raises Empty: if the attempt to get an envelope fails.
        """
        logger.debug("Checks for envelope from the in queue...")
        envelope = self._multiplexer.get(block=block, timeout=timeout)
        if envelope is None:
            raise Empty()
        logger.debug(
            "Incoming envelope: to='{}' sender='{}' protocol_id='{}' message='{!r}'".format(
                envelope.to, envelope.sender, envelope.protocol_id, envelope.message
            )
        )
        return envelope

    def get_nowait(self) -> Optional[Envelope]:
        """
        Check for a envelope on the in queue and wait for no time.

        :return: the envelope object
        """
        try:
            envelope = self.get()
        except Empty:
            return None
        return envelope


class OutBox:
    """A queue from where you can only enqueue envelopes."""

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

        :return: boolean indicating whether there is an envelope or not
        """
        return self._multiplexer.out_queue.empty()

    def put(self, envelope: Envelope) -> None:
        """
        Put an envelope into the queue.

        :param envelope: the envelope.
        :return: None
        """
        logger.debug(
            "Put an envelope in the queue: to='{}' sender='{}' protocol_id='{}' message='{!r}'...".format(
                envelope.to, envelope.sender, envelope.protocol_id, envelope.message
            )
        )
        self._multiplexer.put(envelope)

    def put_message(
        self, to: Address, sender: Address, protocol_id: ProtocolId, message: bytes
    ) -> None:
        """
        Put a message in the outbox.

        This constructs an envelope with the input arguments.

        :param to: the recipient of the envelope.
        :param sender: the sender of the envelope.
        :param protocol_id: the protocol id.
        :param message: the content of the message.
        :return: None
        """
        envelope = Envelope(
            to=to, sender=sender, protocol_id=protocol_id, message=message
        )
        self._multiplexer.put(envelope)
