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

"""Extension to the Local Node."""
import asyncio
import logging
from asyncio import Queue, AbstractEventLoop
from collections import defaultdict
from threading import Thread
from typing import Dict, List, Optional, cast, Set

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope, AEAConnectionError
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, Query
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class LocalNode:
    """A light-weight local implementation of a OEF Node."""

    def __init__(self, loop: AbstractEventLoop = None):
        """
        Initialize a local (i.e. non-networked) implementation of an OEF Node.

        :param loop: the event loop. If None, a new event loop is instantiated.
        """
        self.agents = defaultdict(lambda: [])  # type: Dict[str, List[Description]]
        self.services = defaultdict(lambda: [])  # type: Dict[str, List[Description]]
        self._lock = asyncio.Lock()
        self._loop = loop if loop is not None else asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop)

        self._in_queue = asyncio.Queue(loop=self._loop)  # type: asyncio.Queue
        self._out_queues = {}  # type: Dict[str, asyncio.Queue]

        self._receiving_loop_task = None  # type: Optional[asyncio.Task]

    def __enter__(self):
        """Start the local node."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the local node."""
        self.stop()

    def _run_loop(self):
        """
        Run the asyncio loop.

        This method is supposed to be run only in the Multiplexer thread.
        """
        logger.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        logger.debug("Asyncio loop has been stopped.")

    async def connect(self, public_key: str, writer: asyncio.Queue) -> Optional[asyncio.Queue]:
        """
        Connect a public key to the node.

        :param public_key: the public key of the agent.
        :param writer: the queue where the client is listening.
        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if public_key in self._out_queues.keys():
            return None

        assert self._in_queue is not None
        q = self._in_queue  # type: asyncio.Queue
        self._out_queues[public_key] = writer

        return q

    def start(self):
        """Start the node."""
        if not self._loop.is_running() and not self._thread.is_alive():
            self._thread.start()
        self._receiving_loop_task = asyncio.run_coroutine_threadsafe(self.receiving_loop(), loop=self._loop)
        logger.debug("Local node has been started.")

    def stop(self):
        """Stop the node."""
        asyncio.run_coroutine_threadsafe(self._in_queue.put(None), self._loop).result()
        self._receiving_loop_task.result()

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive():
            self._thread.join()

    async def receiving_loop(self):
        """Process incoming messages."""
        while True:
            envelope = await self._in_queue.get()
            if envelope is None:
                logger.debug("Receiving loop terminated.")
                return
            logger.debug("Handling envelope: {}".format(envelope))
            await self._handle_envelope(envelope)

    async def _handle_envelope(self, envelope: Envelope) -> None:
        """Handle an envelope.

        :param envelope: the envelope
        :return: None
        """
        if envelope.protocol_id == "oef":
            await self._handle_oef_message(envelope)
        else:
            await self._handle_agent_message(envelope)

    async def _handle_oef_message(self, envelope: Envelope) -> None:
        """Handle oef messages.

        :param envelope: the envelope
        :return: None
        """
        oef_message = OEFSerializer().decode(envelope.message)
        sender = envelope.sender
        request_id = cast(int, oef_message.get("id"))
        oef_type = OEFMessage.Type(oef_message.get("type"))
        if oef_type == OEFMessage.Type.REGISTER_SERVICE:
            await self._register_service(sender, cast(Description, oef_message.get("service_description")))
        elif oef_type == OEFMessage.Type.REGISTER_AGENT:
            await self._register_agent(sender, cast(Description, oef_message.get("agent_description")))
        elif oef_type == OEFMessage.Type.UNREGISTER_SERVICE:
            await self._unregister_service(sender, request_id, cast(Description, oef_message.get("service_description")))
        elif oef_type == OEFMessage.Type.UNREGISTER_AGENT:
            await self._unregister_agent(sender, request_id, cast(Description, oef_message.get("agent_description")))
        elif oef_type == OEFMessage.Type.SEARCH_AGENTS:
            await self._search_agents(sender, request_id, cast(Query, oef_message.get("query")))
        elif oef_type == OEFMessage.Type.SEARCH_SERVICES:
            await self._search_services(sender, request_id, cast(Query, oef_message.get("query")))
        else:
            # request not recognized
            pass

    async def _handle_agent_message(self, envelope: Envelope) -> None:
        """
        Forward an envelope to the right agent.

        :param envelope: the envelope
        :return: None
        """
        destination = envelope.to

        if destination not in self._out_queues.keys():
            msg = OEFMessage(oef_type=OEFMessage.Type.DIALOGUE_ERROR, id=STUB_DIALOGUE_ID, dialogue_id=STUB_DIALOGUE_ID, origin=destination)
            msg_bytes = OEFSerializer().encode(msg)
            error_envelope = Envelope(to=envelope.sender, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
            await self._send(error_envelope)
            return
        else:
            await self._send(envelope)

    async def _register_service(self, public_key: str, service_description: Description):
        """
        Register a service agent in the service directory of the node.

        :param public_key: the public key of the service agent to be registered.
        :param service_description: the description of the service agent to be registered.
        :return: None
        """
        async with self._lock:
            self.services[public_key].append(service_description)

    async def _register_agent(self, public_key: str, agent_description: Description):
        """
        Register a service agent in the service directory of the node.

        :param public_key: the public key of the service agent to be registered.
        :param agent_description: the description of the service agent to be registered.
        :return: None
        """
        async with self._lock:
            self.agents[public_key].append(agent_description)

    async def _register_service_wide(self, public_key: str, service_description: Description):
        """Register service wide."""
        raise NotImplementedError  # pragma: no cover

    async def _unregister_service(self, public_key: str, msg_id: int, service_description: Description) -> None:
        """
        Unregister a service agent.

        :param public_key: the public key of the service agent to be unregistered.
        :param msg_id: the message id of the request.
        :param service_description: the description of the service agent to be unregistered.
        :return: None
        """
        async with self._lock:
            if public_key not in self.services:
                msg = OEFMessage(oef_type=OEFMessage.Type.OEF_ERROR, id=msg_id, operation=OEFMessage.OEFErrorOperation.UNREGISTER_SERVICE)
                msg_bytes = OEFSerializer().encode(msg)
                envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
                await self._send(envelope)
            else:
                self.services[public_key].remove(service_description)
                if len(self.services[public_key]) == 0:
                    self.services.pop(public_key)

    async def _unregister_agent(self, public_key: str, msg_id: int, agent_description: Description) -> None:
        """
        Unregister an agent.

        :param agent_description:
        :param public_key: the public key of the service agent to be unregistered.
        :param msg_id: the message id of the request.
        :return: None
        """
        async with self._lock:
            if public_key not in self.agents:
                msg = OEFMessage(oef_type=OEFMessage.Type.OEF_ERROR, id=msg_id, operation=OEFMessage.OEFErrorOperation.UNREGISTER_AGENT)
                msg_bytes = OEFSerializer().encode(msg)
                envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
                await self._send(envelope)
            else:
                self.agents[public_key].remove(agent_description)
                if len(self.agents[public_key]) == 0:
                    self.agents.pop(public_key)

    async def _search_agents(self, public_key: str, search_id: int, query: Query) -> None:
        """
        Search the agents in the local Agent Directory, and send back the result.

        This is actually a dummy search, it will return all the registered agents with the specified data model.
        If the data model is not specified, it will return all the agents.

        :param public_key: the source of the search request.
        :param search_id: the search identifier associated with the search request.
        :param query: the query that constitutes the search.
        :return: None
        """
        result = []  # type: List[str]
        if query.model is None:
            result = list(set(self.services.keys()))
        else:
            for agent_public_key, descriptions in self.agents.items():
                for description in descriptions:
                    if query.model == description.data_model:
                        result.append(agent_public_key)

        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_RESULT, id=search_id, agents=sorted(set(result)))
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        await self._send(envelope)

    async def _search_services(self, public_key: str, search_id: int, query: Query) -> None:
        """
        Search the agents in the local Service Directory, and send back the result.

        This is actually a dummy search, it will return all the registered agents with the specified data model.
        If the data model is not specified, it will return all the agents.

        :param public_key: the source of the search request.
        :param search_id: the search identifier associated with the search request.
        :param query: the query that constitutes the search.
        :return: None
        """
        result = []  # type: List[str]
        if query.model is None:
            result = list(set(self.services.keys()))
        else:
            for agent_public_key, descriptions in self.services.items():
                for description in descriptions:
                    if description.data_model == query.model:
                        result.append(agent_public_key)

        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_RESULT, id=search_id, agents=sorted(set(result)))
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        await self._send(envelope)

    async def _send(self, envelope: Envelope):
        """Send a message."""
        destination = envelope.to
        destination_queue = self._out_queues[destination]
        destination_queue._loop.call_soon_threadsafe(destination_queue.put_nowait, envelope)  # type: ignore
        logger.debug("Send envelope {}".format(envelope))

    async def disconnect(self, public_key: str) -> None:
        """
        Disconnect.

        :param public_key: the public key
        :return: None
        """
        async with self._lock:
            self._out_queues.pop(public_key, None)
            self.services.pop(public_key, None)
            self.agents.pop(public_key, None)


class OEFLocalConnection(Connection):
    """
    Proxy to the functionality of the OEF.

    It allows the interaction between agents, but not the search functionality.
    It is useful for local testing.
    """

    def __init__(self, public_key: str, local_node: LocalNode, connection_id: str = "local",
                 restricted_to_protocols: Optional[Set[str]] = None):
        """
        Initialize a OEF proxy for a local OEF Node (that is, :class:`~oef.proxy.OEFLocalProxy.LocalNode`.

        :param public_key: the public key used in the protocols.
        :param local_node: the Local OEF Node object. This reference must be the same across the agents of interest.
        """
        super().__init__(connection_id=connection_id, restricted_to_protocols=restricted_to_protocols)
        self._public_key = public_key
        self._local_node = local_node

        self._reader = None  # type: Optional[Queue]
        self._writer = None  # type: Optional[Queue]

    @property
    def public_key(self) -> str:
        """Get the public key."""
        return self._public_key

    async def connect(self) -> None:
        """Connect to the local OEF Node."""
        if not self.connection_status.is_connected:
            self._reader = Queue()
            self._writer = await self._local_node.connect(self._public_key, self._reader)
            self.connection_status.is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from the local OEF Node."""
        if self.connection_status.is_connected:
            assert self._reader is not None
            await self._local_node.disconnect(self.public_key)
            await self._reader.put(None)
            self._reader, self._writer = None, None
            self.connection_status.is_connected = False

    async def send(self, envelope: Envelope):
        """Send a message."""
        if not self.connection_status.is_connected:
            raise AEAConnectionError("Connection not established yet. Please use 'connect()'.")
        self._writer._loop.call_soon_threadsafe(self._writer.put_nowait, envelope)  # type: ignore

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        if not self.connection_status.is_connected:
            raise AEAConnectionError("Connection not established yet. Please use 'connect()'.")
        try:
            assert self._reader is not None
            envelope = await self._reader.get()
            if envelope is None:
                logger.debug("Receiving task terminated.")
                return None
            logger.debug("Received envelope {}".format(envelope))
            return envelope
        except Exception:
            return None

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the Local OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        local_node = LocalNode()
        return OEFLocalConnection(public_key, local_node,
                                  connection_id=connection_configuration.config.get("name"),
                                  restricted_to_protocols=set(connection_configuration.restricted_to_protocols))
