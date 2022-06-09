# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.helpers.async_utils import AsyncState, Runnable, ThreadedAsyncRunner
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.logging import WithLogger, get_logger
from aea.mail.base import AEAConnectionError, Empty, Envelope, EnvelopeContext
from aea.protocols.base import Message, Protocol


class MultiplexerStatus(AsyncState):
    """The connection status class."""

    def __init__(self) -> None:
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
    CONNECT_TIMEOUT = 60
    SEND_TIMEOUT = 60

    _lock: asyncio.Lock

    def __init__(
        self,
        connections: Optional[Sequence[Connection]] = None,
        default_connection_index: int = 0,
        loop: Optional[AbstractEventLoop] = None,
        exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        threaded: bool = False,
        agent_name: str = "standalone",
        default_routing: Optional[Dict[PublicId, PublicId]] = None,
        default_connection: Optional[PublicId] = None,
        protocols: Optional[List[Union[Protocol, Message]]] = None,
    ) -> None:
        """
        Initialize the connection multiplexer.

        :param connections: a sequence of connections.
        :param default_connection_index: the index of the connection to use as default.
            This information is used for envelopes which don't specify any routing context.
            If connections is None, this parameter is ignored.
        :param loop: the event loop to run the multiplexer. If None, a new event loop is created.
        :param exception_policy: the exception policy used for connections.
        :param threaded: if True, run in threaded mode, else async
        :param agent_name: the name of the agent that owns the multiplexer, for logging purposes.
        :param default_routing: default routing map
        :param default_connection: default connection
        :param protocols: protocols used
        """
        self._exception_policy: ExceptionPolicyEnum = exception_policy
        logger = get_logger(__name__, agent_name)
        WithLogger.__init__(self, logger=logger)
        Runnable.__init__(self, loop=loop, threaded=threaded)

        self._connections: List[Connection] = []
        self._id_to_connection: Dict[PublicId, Connection] = {}
        self._default_connection: Optional[Connection] = None

        connections = connections or []
        if not default_connection and connections:
            enforce(
                len(connections) - 1 >= default_connection_index,
                "default_connection_index os out of connections range!",
            )
            default_connection = connections[default_connection_index].connection_id

        if default_connection:
            enforce(
                bool(
                    [
                        i.connection_id.same_prefix(default_connection)
                        for i in connections
                    ]
                ),
                f"Default connection {default_connection} does not present in connections list!",
            )

        self._default_routing = {}  # type: Dict[PublicId, PublicId]

        self._setup(connections or [], default_routing, default_connection)

        self._connection_status = MultiplexerStatus()
        self._specification_id_to_protocol_id = {
            p.protocol_specification_id: p.protocol_id for p in protocols or []
        }
        self._routing_helper: Dict[Address, PublicId] = {}

        self._in_queue = AsyncFriendlyQueue()  # type: AsyncFriendlyQueue
        self._out_queue = None  # type: Optional[asyncio.Queue]

        self._recv_loop_task = None  # type: Optional[asyncio.Task]
        self._send_loop_task = None  # type: Optional[asyncio.Task]

        self._loop: asyncio.AbstractEventLoop = (
            loop if loop is not None else asyncio.new_event_loop()
        )
        self.set_loop(self._loop)

    @property
    def default_connection(self) -> Optional[Connection]:
        """Get the default connection."""
        return self._default_connection

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
    def default_routing(self, default_routing: Dict[PublicId, PublicId]) -> None:
        """Set the default routing."""
        self._default_routing = default_routing

    @property
    def connection_status(self) -> MultiplexerStatus:
        """Get the connection status."""
        return self._connection_status

    async def run(self) -> None:
        """Run multiplexer connect and receive/send tasks."""
        self.set_loop(asyncio.get_event_loop())
        try:
            await self.connect()

            if not self._recv_loop_task or not self._send_loop_task:
                raise ValueError("Multiplexer is not connected properly.")

            await asyncio.gather(self._recv_loop_task, self._send_loop_task)
        finally:
            await self.disconnect()

    def _get_protocol_id_for_envelope(self, envelope: Envelope) -> PublicId:
        """Get protocol id for envelope."""
        if isinstance(envelope.message, Message):
            return cast(Message, envelope.message).protocol_id

        protocol_id = self._specification_id_to_protocol_id.get(
            envelope.protocol_specification_id
        )

        if not protocol_id:
            raise ValueError(
                f"Can not resolve protocol id for {envelope}, pass protocols supported to multipelxer instance {self._specification_id_to_protocol_id}"
            )

        return protocol_id

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop and all event loop related objects.

        :param loop: asyncio event loop.
        """
        self._loop = loop
        self._lock = asyncio.Lock()

    def _handle_exception(self, fn: Callable, exc: Exception) -> None:
        """
        Handle exception raised.

        :param fn: a method where it raised .send .connect etc
        :param exc:  exception
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
        Add a connection to the multiplexer.

        :param connection: the connection to add.
        :param is_default: whether the connection added should be the default one.
        """
        if connection.connection_id in self._id_to_connection:  # pragma: nocover
            self.logger.warning(
                f"A connection with id {connection.connection_id.without_hash()} was already added. Replacing it..."
            )

        self._connections.append(connection)
        self._id_to_connection[connection.connection_id] = connection
        if is_default:
            self._default_connection = connection

    def _connection_consistency_checks(self) -> None:
        """
        Do some consistency checks on the multiplexer connections.

        :raise AEAEnforceError: if an inconsistency is found.
        """
        if len(self.connections) == 0:
            self.logger.debug("List of connections is empty.")

        enforce(
            len(set(c.connection_id for c in self.connections))
            == len(self.connections),
            "Connection names must be unique.",
        )

    def _set_default_connection_if_none(self) -> None:
        """Set the default connection if it is none."""
        if self._default_connection is None and bool(self.connections):
            self._default_connection = self.connections[0]

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
            except AEAConnectionError:
                await self._stop()
                raise
            except Exception as e:
                self.logger.exception("Exception on connect:")
                await self._stop()
                raise AEAConnectionError(
                    f"Failed to connect the multiplexer: Error: {repr(e)}"
                ) from e

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
            except CancelledError:  # pragma: nocover
                self.logger.debug("Multiplexer.disconnect cancellation!")
                raise
            except Exception as e:
                self.logger.exception("Exception on disconnect:")
                raise AEAConnectionError(
                    f"Failed to disconnect the multiplexer: Error: {repr(e)}"
                ) from e

    async def _stop_receive_send_loops(self) -> None:
        """Stop receive and send loops."""
        self.logger.debug("Stopping receive loop...")

        if self._recv_loop_task:
            self._recv_loop_task.cancel()
            with suppress(Exception, asyncio.CancelledError):
                await self._recv_loop_task

        self._recv_loop_task = None
        self.logger.debug("Receive loop stopped.")

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
            connections_left = [
                str(c.connection_id) for c in self.connections if not c.is_disconnected
            ]
            raise AEAConnectionError(
                f"Failed to disconnect multiplexer, some connections are not disconnected within timeout: {', '.join(connections_left)}"
            )

    async def _stop(self) -> None:
        """
        Stop the multiplexer.

        Stops receive and send loops.
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
                await asyncio.wait_for(
                    self._connect_one(connection_id), timeout=self.CONNECT_TIMEOUT
                )
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
                await self._send(envelope)

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
                    connection = task_to_connection.pop(task)
                    envelope = task.result()
                    if envelope is not None:
                        self._update_routing_helper(envelope, connection)
                        self.in_queue.put_nowait(envelope)

                    # reinstantiate receiving task, but only if the connection is still up.
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
        """
        envelope_protocol_id = self._get_protocol_id_for_envelope(envelope)
        connection_id = self._get_connection_id_from_envelope(
            envelope, envelope_protocol_id
        )

        connection = (
            self._get_connection(connection_id) if connection_id is not None else None
        )

        if connection is None:
            # we don't raise on dropping envelope as this can be a configuration issue only!
            self.logger.warning(
                f"Dropping envelope, no connection available for sending: {envelope}"
            )
            return

        if not self._is_connection_supported_protocol(connection, envelope_protocol_id):
            return

        try:
            await asyncio.wait_for(connection.send(envelope), timeout=self.SEND_TIMEOUT)
        except Exception as e:  # pylint: disable=broad-except
            self._handle_exception(self._send, e)

    def _get_connection_id_from_envelope(
        self, envelope: Envelope, envelope_protocol_id: PublicId
    ) -> Optional[PublicId]:
        """
        Get the connection id from an envelope.

        Applies the following rules:
        - component to component messages are routed by their component id
        - agent to agent messages, are routed following four rules:
            * first, try to route by envelope context connection id
            * second, try to route by routing helper
            * third, try to route by default routing
            * forth, using default connection

        :param envelope: the Envelope
        :param envelope_protocol_id: the protocol id of the message contained in the envelope
        :return: public id if found
        """
        self.logger.debug(f"Routing envelope: {envelope}")
        # component to component messages are routed by their component id
        if envelope.is_component_to_component_message:
            connection_id = envelope.to_as_public_id
            self.logger.debug(
                "Using envelope `to` field as connection_id: {}".format(connection_id)
            )
            enforce(
                connection_id is not None,
                "Connection id cannot be None by envelope construction.",
            )
            return connection_id

        # agent to agent messages, are routed following four rules:
        # first, try to route by envelope context connection id
        if envelope.context is not None and envelope.context.connection_id is not None:
            connection_id = envelope.context.connection_id
            self.logger.debug(
                "Using envelope context connection_id: {}".format(connection_id)
            )
            return connection_id

        # second, try to route by routing helper
        if envelope.to in self._routing_helper:
            connection_id = self._routing_helper[envelope.to]
            self.logger.debug(
                "Using routing helper with connection_id: {}".format(connection_id)
            )
            return connection_id

        # third, try to route by default routing
        if envelope_protocol_id in self.default_routing:
            connection_id = self.default_routing[envelope_protocol_id]
            self.logger.debug("Using default routing: {}".format(connection_id))
            return connection_id

        # forth, using default connection
        connection_id = (
            self.default_connection.connection_id
            if self.default_connection is not None
            else None
        )
        self.logger.debug("Using default connection: {}".format(connection_id))
        return connection_id

    def _get_connection(self, connection_id: PublicId) -> Optional[Connection]:
        """Check if the connection id is registered."""
        conn_ = self._id_to_connection.get(connection_id, None)
        if conn_ is not None:
            return conn_
        for id_, conn_ in self._id_to_connection.items():
            if id_.same_prefix(connection_id):
                return conn_
        self.logger.error(f"No connection registered with id: {connection_id}")
        return None

    def _is_connection_supported_protocol(
        self, connection: Connection, protocol_id: PublicId
    ) -> bool:
        """Check protocol id is supported by the connection."""
        if protocol_id in connection.excluded_protocols:
            self.logger.warning(
                f"Connection {connection.connection_id} does not support protocol {protocol_id}. It is explicitly excluded."
            )
            return False

        if (
            connection.restricted_to_protocols
            and protocol_id not in connection.restricted_to_protocols
        ):
            self.logger.warning(
                f"Connection {connection.connection_id} does not support protocol {protocol_id}. The connection is restricted to protocols in {connection.restricted_to_protocols}."
            )
            return False

        return True

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
        """
        await self.out_queue.put(envelope)

    def put(self, envelope: Envelope) -> None:
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        """
        if self._threaded:
            self._loop.call_soon_threadsafe(self.out_queue.put_nowait, envelope)
        else:
            self.out_queue.put_nowait(envelope)

    def _setup(
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
        """
        self.default_routing = default_routing or {}

        # replace connections
        self._connections = []
        self._id_to_connection = {}

        for c in connections:
            self.add_connection(c, c.public_id == default_connection)

    def _update_routing_helper(
        self, envelope: Envelope, connection: Connection
    ) -> None:
        """
        Update the routing helper.

        Saves the source (connection) of an agent-to-agent envelope.

        :param envelope: the envelope to be updated
        :param connection: the connection
        """
        if envelope.is_component_to_component_message:
            return
        self._routing_helper[envelope.sender] = connection.public_id


class Multiplexer(AsyncMultiplexer):
    """Transit sync multiplexer for compatibility."""

    _thread_was_started: bool
    _is_connected: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the connection multiplexer.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        super().__init__(*args, **kwargs)
        self._sync_lock = threading.Lock()
        self._init()

    def _init(self) -> None:
        """Set initial variables."""
        self._thread_was_started = False
        self._is_connected = False

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop and all event loop related objects.

        :param loop: asyncio event loop.
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

            # reset thread runner and init variables
            self._init()
            self.set_loop(self._loop)

    def put(self, envelope: Envelope) -> None:  # type: ignore  # cause overrides coroutine
        """
        Schedule an envelope for sending it.

        Notice that the output queue is an asyncio.Queue which uses an event loop
        running on a different thread than the one used in this function.

        :param envelope: the envelope to be sent.
        """
        self._thread_runner.call(super()._put(envelope))  # .result(240)


class InBox:
    """A queue from where you can only consume envelopes."""

    def __init__(self, multiplexer: AsyncMultiplexer) -> None:
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

        self._multiplexer.logger.debug(f"Incoming {envelope}")
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

        self._multiplexer.logger.debug(f"Incoming envelope: {envelope}")
        return envelope

    async def async_wait(self) -> None:
        """Check for a envelope on the in queue."""
        self._multiplexer.logger.debug(
            "Checks for envelope presents in queue async way..."
        )
        await self._multiplexer.async_wait()


class OutBox:
    """A queue from where you can only enqueue envelopes."""

    def __init__(self, multiplexer: AsyncMultiplexer) -> None:
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
        """
        self._multiplexer.logger.debug(f"Put an envelope in the queue: {envelope}.")
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
        self,
        message: Message,
        context: Optional[EnvelopeContext] = None,
    ) -> None:
        """
        Put a message in the outbox.

        This constructs an envelope with the input arguments.

        :param message: the message
        :param context: the envelope context
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
            message=message,
            context=context,
        )
        self.put(envelope)
