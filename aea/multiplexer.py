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
"""Module for the multiplexer class and related classes."""
import asyncio
import queue
from asyncio.events import AbstractEventLoop
from concurrent.futures._base import CancelledError, Future
from threading import Lock, Thread
from typing import Dict, List, Optional, Sequence, Tuple, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStatus
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.mail.base import (
    AEAConnectionError,
    Address,
    Empty,
    Envelope,
    EnvelopeContext,
    logger,
)
from aea.protocols.base import Message


class Multiplexer:
    """This class can handle multiple connections at once."""

    def __init__(
        self,
        connections: Optional[Sequence[Connection]] = None,
        default_connection_index: int = 0,
        loop: Optional[AbstractEventLoop] = None,
    ):
        """
        Initialize the connection multiplexer.

        :param connections: a sequence of connections.
        :param default_connection_index: the index of the connection to use as default.
            This information is used for envelopes which don't specify any routing context.
            If connections is None, this parameter is ignored.
        :param loop: the event loop to run the multiplexer. If None, a new event loop is created.
        """
        self._connections: List[Connection] = []
        self._id_to_connection: Dict[PublicId, Connection] = {}
        self.default_connection: Optional[Connection] = None
        self._initialize_connections_if_any(connections, default_connection_index)

        self._connection_status = ConnectionStatus()

        self._lock = Lock()
        self._loop = loop if loop is not None else asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop)

        self._in_queue = AsyncFriendlyQueue()  # type: AsyncFriendlyQueue
        self._out_queue = None  # type: Optional[asyncio.Queue]

        self._connect_all_task = None  # type: Optional[Future]
        self._disconnect_all_task = None  # type: Optional[Future]
        self._recv_loop_task = None  # type: Optional[Future]
        self._send_loop_task = None  # type: Optional[Future]
        self._default_routing = {}  # type: Dict[PublicId, PublicId]

    def _initialize_connections_if_any(
        self, connections: Optional[Sequence[Connection]], default_connection_index: int
    ):
        if connections is not None and len(connections) > 0:
            assert (
                0 <= default_connection_index <= len(connections) - 1
            ), "Default connection index out of range."
            for idx, connection in enumerate(connections):
                self.add_connection(connection, idx == default_connection_index)

    @property
    def in_queue(self) -> AsyncFriendlyQueue:
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
    def connections(self) -> Tuple[Connection, ...]:
        """Get the connections."""
        return tuple(self._connections)

    @property
    def is_connected(self) -> bool:
        """Check whether the multiplexer is processing envelopes."""
        return self._loop.is_running() and all(
            c.connection_status.is_connected for c in self._connections
        )

    @property
    def default_routing(self) -> Dict[PublicId, PublicId]:
        """Get the default routing."""
        return self._default_routing

    @default_routing.setter
    def default_routing(self, default_routing: Dict[PublicId, PublicId]):
        """Set the default routing."""
        self._default_routing = default_routing

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get the connection status."""
        return self._connection_status

    def connect(self) -> None:
        """Connect the multiplexer."""
        self._connection_consistency_checks()
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
        connection_id = None  # type: Optional[PublicId]
        envelope_context = envelope.context
        # first, try to route by context
        if envelope_context is not None:
            connection_id = envelope_context.connection_id

        # second, try to route by default routing
        if connection_id is None and envelope.protocol_id in self.default_routing:
            connection_id = self.default_routing[envelope.protocol_id]
            logger.debug("Using default routing: {}".format(connection_id))

        if connection_id is not None and connection_id not in self._id_to_connection:
            raise AEAConnectionError(
                "No connection registered with id: {}.".format(connection_id)
            )

        if connection_id is None:
            logger.debug("Using default connection: {}".format(self.default_connection))
            connection = self.default_connection
        else:
            connection = self._id_to_connection[connection_id]

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

    async def async_get(self) -> Envelope:
        """
        Get an envelope async way.

        :return: the envelope
        """
        try:
            return await self.in_queue.async_get()
        except queue.Empty:
            raise Empty

    async def async_wait(self) -> None:
        """
        Get an envelope async way.

        :return: the envelope
        """
        return await self.in_queue.async_wait()

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

    def add_connection(self, connection: Connection, is_default: bool = False) -> None:
        """
        Add a connection to the mutliplexer.

        :param connection: the connection to add.
        :param is_default: whether the connection added should be the default one.
        :return: None
        """
        if connection.connection_id in self._id_to_connection:
            logger.warning(
                f"A connection with id {connection.connection_id} was already added. Replacing it..."
            )

        self._connections.append(connection)
        self._id_to_connection[connection.connection_id] = connection
        if is_default:
            self.default_connection = connection

    def _connection_consistency_checks(self):
        """
        Do some consistency checks on the multiplexer connections.

        :return: None
        :raise AssertionError: if an inconsistency is found.
        """
        assert len(self.connections) > 0, "List of connections cannot be empty."

        assert len(set(c.connection_id for c in self.connections)) == len(
            self.connections
        ), "Connection names must be unique."


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

    async def async_get(self) -> Envelope:
        """
        Check for a envelope on the in queue.

        :return: the envelope object.
        """
        logger.debug("Checks for envelope from the in queue async way...")
        envelope = await self._multiplexer.async_get()
        if envelope is None:
            raise Empty()
        logger.debug(
            "Incoming envelope: to='{}' sender='{}' protocol_id='{}' message='{!r}'".format(
                envelope.to, envelope.sender, envelope.protocol_id, envelope.message
            )
        )
        return envelope

    async def async_wait(self) -> None:
        """
        Check for a envelope on the in queue.

        :return: the envelope object.
        """
        logger.debug("Checks for envelope presents in queue async way...")
        await self._multiplexer.async_wait()


class OutBox:
    """A queue from where you can only enqueue envelopes."""

    def __init__(self, multiplexer: Multiplexer, default_address: Address):
        """
        Initialize the outbox.

        :param multiplexer: the multiplexer
        :param default_address: the default address of the agent
        """
        super().__init__()
        self._multiplexer = multiplexer
        self._default_address = default_address

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
            "Put an envelope in the queue: to='{}' sender='{}' protocol_id='{}' message='{!r}' context='{}'...".format(
                envelope.to,
                envelope.sender,
                envelope.protocol_id,
                envelope.message,
                envelope.context,
            )
        )
        assert isinstance(
            envelope.message, Message
        ), "Only Message type allowed in envelope message field when putting into outbox."
        self._multiplexer.put(envelope)

    def put_message(
        self,
        message: Message,
        sender: Optional[Address] = None,
        context: Optional[EnvelopeContext] = None,
    ) -> None:
        """
        Put a message in the outbox.

        This constructs an envelope with the input arguments.

        :param sender: the sender of the envelope (optional field only necessary when the non-default address is used for sending).
        :param message: the message.
        :param context: the envelope context
        :return: None
        """
        assert isinstance(message, Message), "Provided message not of type Message."
        assert (
            message.counterparty
        ), "Provided message has message.counterparty not set."
        envelope = Envelope(
            to=message.counterparty,
            sender=sender or self._default_address,
            protocol_id=message.protocol_id,
            message=message,
            context=context,
        )
        self.put(envelope)
