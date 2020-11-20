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
import threading
from asyncio.events import AbstractEventLoop
from concurrent.futures._base import CancelledError
from concurrent.futures._base import TimeoutError as FuturesTimeoutError
from contextlib import suppress
from typing import Callable, Collection, Dict, List, Optional, Sequence, Tuple, cast

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.helpers.async_utils import AsyncState, Runnable, ThreadedAsyncRunner
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.logging import WithLogger, get_logger
from aea.mail.base import AEAConnectionError, Empty, Envelope, EnvelopeContext
from aea.protocols.base import Message


class MultiplexerStatus(AsyncState):
    """The connection status class."""

    def __init__(self):
        """Initialize the connection status."""
        super().__init__(
            initial_state=ConnectionStates.disconnected, states_enum=ConnectionStates
        )

    @property
    def is_connected(self) -> bool:  # pragma: nocover
        """Return is connected."""
        return self.get() == ConnectionStates.connected

    @property
    def is_connecting(self) -> bool:  # pragma: nocover
        """Return is connecting."""
        return self.get() == ConnectionStates.connecting

    @property
    def is_disconnected(self) -> bool:  # pragma: nocover
        """Return is disconnected."""
        return self.get() == ConnectionStates.disconnected

    @property
    def is_disconnecting(self) -> bool:  # pragma: nocover
        """Return is disconnected."""
        return self.get() == ConnectionStates.disconnecting


class AsyncMultiplexer(Runnable, WithLogger):
    """This class can handle multiple connections at once."""

    DISCONNECT_TIMEOUT = 5

    def __init__(
        self,
        connections: Optional[Sequence[Connection]] = None,
        default_connection_index: int = 0,
        loop: Optional[AbstractEventLoop] = None,
        exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        threaded: bool = False,
        agent_name: str = "standalone",
    ):
        """
        Initialize the connection multiplexer.

        :param connections: a sequence of connections.
        :param default_connection_index: the index of the connection to use as default.
            This information is used for envelopes which don't specify any routing context.
            If connections is None, this parameter is ignored.
        :param loop: the event loop to run the multiplexer. If None, a new event loop is created.
        :param agent_name: the name of the agent that owns the multiplexer, for logging purposes.
        """
        self._exception_policy: ExceptionPolicyEnum = exception_policy
        logger = get_logger(__name__, agent_name)
        WithLogger.__init__(self, logger=logger)
        Runnable.__init__(self, loop=loop, threaded=threaded)
        self._connections: List[Connection] = []
        self._id_to_connection: Dict[PublicId, Connection] = {}
        self._default_connection: Optional[Connection] = None
        self._initialize_connections_if_any(connections, default_connection_index)

        self._connection_status = MultiplexerStatus()

        self._in_queue = AsyncFriendlyQueue()  # type: AsyncFriendlyQueue
        self._out_queue = None  # type: Optional[asyncio.Queue]

        self._recv_loop_task = None  # type: Optional[asyncio.Task]
        self._send_loop_task = None  # type: Optional[asyncio.Task]
        self._default_routing = {}  # type: Dict[PublicId, PublicId]
        self._loop: asyncio.AbstractEventLoop = loop if loop is not None else asyncio.new_event_loop()
        self._lock: asyncio.Lock = asyncio.Lock(loop=self._loop)
        self.set_loop(self._loop)

    async def run(self) -> None:
        """Run multiplexer connect and recv/send tasks."""
        self.set_loop(asyncio.get_event_loop())
        try:
            await self.connect()

            if not self._recv_loop_task or not self._send_loop_task:
                raise ValueError("Multiplexer is not connected properly.")

            await asyncio.gather(self._recv_loop_task, self._send_loop_task)
        finally:
            await self.disconnect()

    @property
    def default_connection(self) -> Optional[Connection]:
        """Get the default connection."""
        return self._default_connection

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop and all event loopp related objects.

        :param loop: asyncio event loop.
        :return: None
        """
        self._loop = loop
        self._lock = asyncio.Lock(loop=self._loop)

    def _initialize_connections_if_any(
        self, connections: Optional[Sequence[Connection]], default_connection_index: int
    ):
        if connections is not None and len(connections) > 0:
            enforce(
                (0 <= default_connection_index <= len(connections) - 1),
                "Default connection index out of range.",
            )
            for idx, connection in enumerate(connections):
                self.add_connection(connection, idx == default_connection_index)

    def _handle_exception(self, fn: Callable, exc: Exception) -> None:
        """
        Handle exception raised.

        :param fn: a method where it raised .send .connect etc
        :param exc:  exception

        :return: None.
        """
        if self._exception_policy == ExceptionPolicyEnum.just_log:
            self.logger.exception(f"Exception raised in {fn}")
        elif self._exception_policy == ExceptionPolicyEnum.propagate:
            raise exc
        elif self._exception_policy == ExceptionPolicyEnum.stop_and_exit:
            self._loop.create_task(AsyncMultiplexer.disconnect(self))
        else:  # pragma: nocover
            raise ValueError(f"Unknown exception policy: {self._exception_policy}")

    def add_connection(self, connection: Connection, is_default: bool = False) -> None:
        """
        Add a connection to the mutliplexer.

        :param connection: the connection to add.
        :param is_default: whether the connection added should be the default one.
        :return: None
        """
        if connection.connection_id in self._id_to_connection:  # pragma: nocover
            self.logger.warning(
                f"A connection with id {connection.connection_id} was already added. Replacing it..."
            )

        self._connections.append(connection)
        self._id_to_connection[connection.connection_id] = connection
        if is_default:
            self._default_connection = connection

    def _connection_consistency_checks(self):
        """
        Do some consistency checks on the multiplexer connections.

        :return: None
        :raise AEAEnforceError: if an inconsistency is found.
        """
        enforce(len(self.connections) > 0, "List of connections cannot be empty.")

        enforce(
            len(set(c.connection_id for c in self.connections))
            == len(self.connections),
            "Connection names must be unique.",
        )

    def _set_default_connection_if_none(self):
        """Set the default connection if it is none."""
        if self._default_connection is None:
            self._default_connection = self.connections[0]

    @property
    def in_queue(self) -> AsyncFriendlyQueue:
        """Get the in queue."""
        return self._in_queue

    @property
    def out_queue(self) -> asyncio.Queue:
        """Get the out queue."""
        if self._out_queue is None:  # pragma: nocover
            raise ValueError("Accessing out queue before loop is started.")
        return self._out_queue

    @property
    def connections(self) -> Tuple[Connection, ...]:
        """Get the connections."""
        return tuple(self._connections)

    @property
    def is_connected(self) -> bool:
        """Check whether the multiplexer is processing envelopes."""
        return self.connection_status.is_connected

    @property
    def default_routing(self) -> Dict[PublicId, PublicId]:
        """Get the default routing."""
        return self._default_routing

    @default_routing.setter
    def default_routing(self, default_routing: Dict[PublicId, PublicId]):
        """Set the default routing."""
        self._default_routing = default_routing

    @property
    def connection_status(self) -> MultiplexerStatus:
        """Get the connection status."""
        return self._connection_status

    async def connect(self) -> None:
        """Connect the multiplexer."""
        self._loop = asyncio.get_event_loop()
        self.logger.debug("Multiplexer connecting...")
        self._connection_consistency_checks()
        self._set_default_connection_if_none()
        self._out_queue = asyncio.Queue()

        async with self._lock:
            if self.connection_status.is_connected:
                self.logger.debug("Multiplexer already connected.")
                return
            try:
                self.connection_status.set(ConnectionStates.connecting)
                await self._connect_all()

                if all(c.is_connected for c in self._connections):
                    self.connection_status.set(ConnectionStates.connected)
                else:  # pragma: nocover
                    raise AEAConnectionError("Failed to connect the multiplexer.")

                self._recv_loop_task = self._loop.create_task(self._receiving_loop())
                self._send_loop_task = self._loop.create_task(self._send_loop())
                self.logger.debug("Multiplexer connected and running.")
            except (CancelledError, asyncio.CancelledError):  # pragma: nocover
                await self._stop()
                raise asyncio.CancelledError()
            except Exception:
                self.logger.exception("Exception on connect:")
                await self._stop()
                raise AEAConnectionError("Failed to connect the multiplexer.")

    async def disconnect(self) -> None:
        """Disconnect the multiplexer."""
        self.logger.debug("Multiplexer disconnecting...")
        async with self._lock:
            if self.connection_status.is_disconnected:
                self.logger.debug("Multiplexer already disconnected.")
                return
            try:
                self.connection_status.set(ConnectionStates.disconnecting)
                await asyncio.wait_for(self._stop(), timeout=60)
                self.logger.debug("Multiplexer disconnected.")
            except (CancelledError, Exception):
                self.logger.exception("Exception on disconnect:")
                raise AEAConnectionError("Failed to disconnect the multiplexer.")

    async def _stop_receive_send_loops(self) -> None:
        """Stop receive and send loops."""
        self.logger.debug("Stopping recv loop...")

        if self._recv_loop_task:
            self._recv_loop_task.cancel()
            with suppress(Exception, asyncio.CancelledError):
                await self._recv_loop_task

        self._recv_loop_task = None
        self.logger.debug("Recv loop stopped.")

        self.logger.debug("Stopping send loop...")

        if self._send_loop_task:
            # send a 'stop' token (a None value) to wake up the coroutine waiting for outgoing envelopes.
            await self.out_queue.put(None)
            self._send_loop_task.cancel()
            with suppress(Exception, asyncio.CancelledError):
                await self._send_loop_task

        self._send_loop_task = None
        self.logger.debug("Send loop stopped.")

    def _check_and_set_disconnected_state(self) -> None:
        """Check every connection is disconnected and set disconnected state."""
        if all([c.is_disconnected for c in self.connections]):
            self.connection_status.set(ConnectionStates.disconnected)
        else:
            raise AEAConnectionError(
                "Failed to disconnect multiplexer, some connections are not disconnected!"
            )

    async def _stop(self) -> None:
        """
        Stop the multiplexer.

        Stops recv and send loops.
        Disconnect every connection.
        """
        self.logger.debug("Stopping multiplexer...")

        await asyncio.wait_for(self._stop_receive_send_loops(), timeout=60)
        await asyncio.wait_for(self._disconnect_all(), timeout=60)
        self._check_and_set_disconnected_state()

        self.logger.debug("Multiplexer stopped.")

    async def _connect_all(self) -> None:
        """Set all the connection up."""
        self.logger.debug("Starting multiplexer connections.")
        connected = []  # type: List[PublicId]
        for connection_id, connection in self._id_to_connection.items():
            try:
                await self._connect_one(connection_id)
                connected.append(connection_id)
            except Exception as e:  # pylint: disable=broad-except
                if not isinstance(e, (asyncio.CancelledError, CancelledError)):
                    self.logger.exception(
                        "Error while connecting {}: {}".format(
                            str(type(connection)), repr(e)
                        )
                    )
                raise
        self.logger.debug("Multiplexer connections are set.")

    async def _connect_one(self, connection_id: PublicId) -> None:
        """
        Set a connection up.

        :param connection_id: the id of the connection.
        :return: None
        """
        connection = self._id_to_connection[connection_id]
        self.logger.debug("Processing connection {}".format(connection.connection_id))
        if connection.is_connected:
            self.logger.debug(
                "Connection {} already established.".format(connection.connection_id)
            )
        else:
            await connection.connect()
            self.logger.debug(
                "Connection {} has been set up successfully.".format(
                    connection.connection_id
                )
            )

    async def _disconnect_all(self) -> None:
        """Tear all the connections down."""
        self.logger.debug("Tear the multiplexer connections down.")
        for connection_id, connection in self._id_to_connection.items():
            try:
                await asyncio.wait_for(
                    self._disconnect_one(connection_id), timeout=self.DISCONNECT_TIMEOUT
                )
            except FuturesTimeoutError:
                self.logger.debug(  # pragma: nocover
                    f"Disconnection of `{connection_id}` timed out."
                )
            except Exception as e:  # pylint: disable=broad-except
                self.logger.exception(
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
        self.logger.debug("Processing connection {}".format(connection.connection_id))
        if not connection.is_connected:
            self.logger.debug(
                "Connection {} already disconnected.".format(connection.connection_id)
            )
        else:
            await connection.disconnect()
            self.logger.debug(
                "Connection {} has been disconnected successfully.".format(
                    connection.connection_id
                )
            )

    async def _send_loop(self) -> None:
        """Process the outgoing envelopes."""
        if not self.is_connected:
            self.logger.debug(
                "Sending loop not started. The multiplexer is not connected."
            )
            return

        try:
            while self.is_connected:
                self.logger.debug("Waiting for outgoing envelopes...")
                envelope = await self.out_queue.get()
                if envelope is None:  # pragma: nocover
                    self.logger.debug(
                        "Received empty envelope. Quitting the sending loop..."
                    )
                    return None
                self.logger.debug("Sending envelope {}".format(str(envelope)))
                try:
                    await self._send(envelope)
                except AEAConnectionError as e:
                    self.logger.error(str(e))

        except asyncio.CancelledError:
            self.logger.debug("Sending loop cancelled.")
            raise
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            self.logger.exception("Error in the sending loop: {}".format(str(e)))
            raise

    async def _receiving_loop(self) -> None:
        """Process incoming envelopes."""
        self.logger.debug("Starting receving loop...")
        task_to_connection = {
            asyncio.ensure_future(conn.receive()): conn for conn in self.connections
        }

        try:
            while self.connection_status.is_connected and len(task_to_connection) > 0:
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
                    if connection.is_connected:
                        new_task = asyncio.ensure_future(connection.receive())
                        task_to_connection[new_task] = connection

        except asyncio.CancelledError:  # pragma: nocover
            self.logger.debug("Receiving loop cancelled.")
            raise
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception("Error in the receiving loop: {}".format(str(e)))
            raise
        finally:
            # cancel all the receiving tasks.
            for t in task_to_connection.keys():
                t.cancel()
            self.logger.debug("Receiving loop terminated.")

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
            self.logger.debug("Using default routing: {}".format(connection_id))

        if connection_id is not None and connection_id not in self._id_to_connection:
            raise AEAConnectionError(
                "No connection registered with id: {}.".format(connection_id)
            )

        # third, if no other option route by default connection
        if connection_id is None:
            self.logger.debug(
                "Using default connection: {}".format(self.default_connection)
            )
            connection = self.default_connection
        else:
            connection = self._id_to_connection[connection_id]

        connection = cast(Connection, connection)
        if (
            len(connection.restricted_to_protocols) > 0
            and envelope.protocol_id not in connection.restricted_to_protocols
        ):
            self.logger.warning(
                "Connection {} cannot handle protocol {}. Cannot send the envelope.".format(
                    connection.connection_id, envelope.protocol_id
                )
            )
            return

        try:
            await connection.send(envelope)
        except Exception as e:  # pylint: disable=broad-except
            self._handle_exception(self._send, e)

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
        except queue.Empty:  # pragma: nocover
            raise Empty

    async def async_wait(self) -> None:
        """
        Get an envelope async way.

        :return: the envelope
        """
        return await self.in_queue.async_wait()

    async def _put(self, envelope: Envelope) -> None:
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        :return: None
        """
        await self.out_queue.put(envelope)

    def put(self, envelope: Envelope) -> None:
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        :return: None
        """
        if self._threaded:
            self._loop.call_soon_threadsafe(self.out_queue.put_nowait, envelope)
        else:
            self.out_queue.put_nowait(envelope)

    def setup(
        self,
        connections: Collection[Connection],
        default_routing: Optional[Dict[PublicId, PublicId]] = None,
        default_connection: Optional[PublicId] = None,
    ) -> None:
        """
        Set up the multiplexer.

        :param connections: the connections to use. It will replace the other ones.
        :param default_routing: the default routing.
        :param default_connection: the default connection.
        :return: None.
        """
        self.default_routing = default_routing or {}

        # replace connections
        self._connections = []
        self._id_to_connection = {}

        for c in connections:
            self.add_connection(c, c.public_id == default_connection)


class Multiplexer(AsyncMultiplexer):
    """Transit sync multiplexer for compatibility."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the connection multiplexer.

        :param connections: a sequence of connections.
        :param default_connection_index: the index of the connection to use as default.
                                       | this information is used for envelopes which
                                       | don't specify any routing context.
        :param loop: the event loop to run the multiplexer. If None, a new event loop is created.
        """
        super().__init__(*args, **kwargs)
        self._sync_lock = threading.Lock()
        self._thread_was_started = False
        self._is_connected = False

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop and all event loopp related objects.

        :param loop: asyncio event loop.
        :return: None
        """
        super().set_loop(loop)
        self._thread_runner = ThreadedAsyncRunner(self._loop)

    def connect(self) -> None:  # type: ignore # cause overrides coroutine # pylint: disable=invalid-overridden-method
        """
        Connect the multiplexer.

        Synchronously in thread spawned if new loop created.
        """
        with self._sync_lock:
            if not self._loop.is_running():
                self._thread_runner.start()
                self._thread_was_started = True

            self._thread_runner.call(super().connect()).result(240)
            self._is_connected = True

    def disconnect(self) -> None:  # type: ignore # cause overrides coroutine # pylint: disable=invalid-overridden-method
        """
        Disconnect the multiplexer.

        Also stops a dedicated thread for event loop if spawned on connect.
        """
        self.logger.debug("Disconnect called")
        with self._sync_lock:
            if not self._loop.is_running():
                return

            if self._is_connected:
                self._thread_runner.call(super().disconnect()).result(240)
                self._is_connected = False
            self.logger.debug("Disconnect async method executed")

            if self._thread_runner.is_alive() and self._thread_was_started:
                self._thread_runner.stop()
                self.logger.debug("Thread stopped")
            self.logger.debug("Disconnected")

    def put(self, envelope: Envelope) -> None:  # type: ignore  # cause overrides coroutine
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        :return: None
        """
        self._thread_runner.call(super()._put(envelope))  # .result(240)


class InBox:
    """A queue from where you can only consume envelopes."""

    def __init__(self, multiplexer: AsyncMultiplexer):
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
        self._multiplexer.logger.debug("Checks for envelope from the in queue...")
        envelope = self._multiplexer.get(block=block, timeout=timeout)

        if envelope is None:  # pragma: nocover
            raise Empty()

        self._multiplexer.logger.debug(
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
            return self.get()
        except Empty:  # pragma: nocover
            return None

    async def async_get(self) -> Envelope:
        """
        Check for a envelope on the in queue.

        :return: the envelope object.
        """
        self._multiplexer.logger.debug(
            "Checks for envelope from the in queue async way..."
        )
        envelope = await self._multiplexer.async_get()

        if envelope is None:  # pragma: nocover
            raise Empty()

        self._multiplexer.logger.debug(
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
        self._multiplexer.logger.debug(
            "Checks for envelope presents in queue async way..."
        )
        await self._multiplexer.async_wait()


class OutBox:
    """A queue from where you can only enqueue envelopes."""

    def __init__(self, multiplexer: AsyncMultiplexer):
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
        return self._multiplexer.out_queue.empty()  # pragma: nocover

    def put(self, envelope: Envelope) -> None:
        """
        Put an envelope into the queue.

        :param envelope: the envelope.
        :return: None
        """
        self._multiplexer.logger.debug(
            "Put an envelope in the queue: to='{}' sender='{}' protocol_id='{}' message='{!r}' context='{}'.".format(
                envelope.to,
                envelope.sender,
                envelope.protocol_id,
                envelope.message,
                envelope.context,
            )
        )
        if not isinstance(envelope.message, Message):
            raise ValueError(
                "Only Message type allowed in envelope message field when putting into outbox."
            )
        message = cast(Message, envelope.message)
        if not message.has_to:  # pragma: nocover
            raise ValueError("Provided message has message.to not set.")
        if not message.has_sender:  # pragma: nocover
            raise ValueError("Provided message has message.sender not set.")
        self._multiplexer.put(envelope)

    def put_message(
        self, message: Message, context: Optional[EnvelopeContext] = None,
    ) -> None:
        """
        Put a message in the outbox.

        This constructs an envelope with the input arguments.

        :param message: the message
        :param context: the envelope context
        :return: None
        """
        if not isinstance(message, Message):
            raise ValueError("Provided message not of type Message.")
        if not message.has_to:
            raise ValueError("Provided message has message.to not set.")
        if not message.has_sender:
            raise ValueError("Provided message has message.sender not set.")
        envelope = Envelope(
            to=message.to,
            sender=message.sender,
            protocol_id=message.protocol_id,
            message=message,
            context=context,
        )
        self.put(envelope)
