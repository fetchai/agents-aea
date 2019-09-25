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
import logging
import queue
import threading
from collections import defaultdict
from queue import Queue
from threading import Thread
from typing import Dict, List, Optional, cast

from aea.mail.base import Envelope, Channel, Connection
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, Query
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.configurations.base import ConnectionConfig

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class LocalNode:
    """A light-weight local implementation of a OEF Node."""

    def __init__(self):
        """Initialize a local (i.e. non-networked) implementation of an OEF Node."""
        self.agents = dict()  # type: Dict[str, Description]
        self.services = defaultdict(lambda: [])  # type: Dict[str, List[Description]]
        self._lock = threading.Lock()

        self._queues = {}  # type: Dict[str, Queue]

    def connect(self, public_key: str) -> Optional[Queue]:
        """
        Connect a public key to the node.

        :param public_key: the public key of the agent.
        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if public_key in self._queues:
            return None

        q = Queue()  # type: Queue
        self._queues[public_key] = q
        return q

    def send(self, envelope: Envelope) -> None:
        """
        Process the incoming messages.

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
        if envelope.protocol_id == "oef":
            self.handle_oef_message(envelope)
        else:
            self.handle_agent_message(envelope)

    def handle_oef_message(self, envelope: Envelope) -> None:
        """
        Handle oef messages.

        :param envelope: the envelope
        :return: None
        """
        oef_message = OEFSerializer().decode(envelope.message)
        sender = envelope.sender
        request_id = cast(int, oef_message.get("id"))
        oef_type = OEFMessage.Type(oef_message.get("type"))
        if oef_type == OEFMessage.Type.REGISTER_SERVICE:
            self.register_service(sender, cast(Description, oef_message.get("service_description")))
        elif oef_type == OEFMessage.Type.UNREGISTER_SERVICE:
            self.unregister_service(sender, request_id, cast(Description, oef_message.get("service_description")))
        elif oef_type == OEFMessage.Type.SEARCH_AGENTS:
            self.search_agents(sender, request_id, cast(Query, oef_message.get("query")))
        elif oef_type == OEFMessage.Type.SEARCH_SERVICES:
            self.search_services(sender, request_id, cast(Query, oef_message.get("query")))
        else:
            # request not recognized
            pass

    def handle_agent_message(self, envelope: Envelope) -> None:
        """
        Forward an envelope to the right agent.

        :param envelope: the envelope
        :return: None
        """
        destination = envelope.to

        if destination not in self._queues:
            msg = OEFMessage(oef_type=OEFMessage.Type.DIALOGUE_ERROR, id=STUB_DIALOGUE_ID, dialogue_id=STUB_DIALOGUE_ID, origin=destination)
            msg_bytes = OEFSerializer().encode(msg)
            error_envelope = Envelope(to=destination, sender=envelope.sender, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
            self._send(error_envelope)
            return
        else:
            self._send(envelope)

    def register_service(self, public_key: str, service_description: Description):
        """
        Register a service agent in the service directory of the node.

        :param public_key: the public key of the service agent to be registered.
        :param service_description: the description of the service agent to be registered.
        :return: None
        """
        with self._lock:
            self.services[public_key].append(service_description)

    def register_service_wide(self, public_key: str, service_description: Description):
        """Register service wide."""
        raise NotImplementedError

    def unregister_service(self, public_key: str, msg_id: int, service_description: Description) -> None:
        """
        Unregister a service agent.

        :param public_key: the public key of the service agent to be unregistered.
        :param msg_id: the message id of the request.
        :param service_description: the description of the service agent to be unregistered.
        :return: None
        """
        with self._lock:
            if public_key not in self.services:
                msg = OEFMessage(oef_type=OEFMessage.Type.OEF_ERROR, id=msg_id, operation=OEFMessage.OEFErrorOperation.UNREGISTER_SERVICE)
                msg_bytes = OEFSerializer().encode(msg)
                envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
                self._send(envelope)
            else:
                self.services[public_key].remove(service_description)
                if len(self.services[public_key]) == 0:
                    self.services.pop(public_key)

    def search_agents(self, public_key: str, search_id: int, query: Query) -> None:
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
            for agent_public_key, description in self.agents.items():
                if query.model == description.data_model:
                    result.append(agent_public_key)

        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_RESULT, id=search_id, agents=sorted(set(result)))
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self._send(envelope)

    def search_services(self, public_key: str, search_id: int, query: Query) -> None:
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
        self._send(envelope)

    def _send(self, envelope: Envelope):
        """Send a message."""
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
            self.services.pop(public_key, None)
            self.agents.pop(public_key, None)


class LocalNodeChannel(Channel):
    """Channel implementation for the local node."""

    def __init__(self, public_key: str, local_node: LocalNode):
        """
        Initialize a OEF proxy for a local OEF Node (that is, :class:`~oef.proxy.OEFLocalProxy.LocalNode`.

        :param public_key: the public key used in the protocols.
        :param local_node: the Local OEF Node object. This reference must be the same across the agents of interest.
        """
        self.public_key = public_key
        self.local_node = local_node

    def connect(self) -> Optional[Queue]:
        """
        Set up the connection.

        :return: A queue or None.
        """
        return self.local_node.connect(self.public_key)

    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """
        return self.local_node.disconnect(self.public_key)

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        return self.local_node.send(envelope)


class OEFLocalConnection(Connection):
    """
    Proxy to the functionality of the OEF.

    It allows the interaction between agents, but not the search functionality.
    It is useful for local testing.
    """

    def __init__(self, public_key: str, local_node: LocalNode):
        """
        Initialize a OEF proxy for a local OEF Node (that is, :class:`~oef.proxy.OEFLocalProxy.LocalNode`.

        :param public_key: the public key used in the protocols.
        :param local_node: the Local OEF Node object. This reference must be the same across the agents of interest.
        """
        super().__init__()
        self.public_key = public_key
        self.channel = LocalNodeChannel(public_key, local_node)

        self._connection = None  # type: Optional[Queue]

        self._stopped = True
        self.in_thread = None
        self.out_thread = None

    def _fetch(self) -> None:
        """
        Fetch the messages from the outqueue and send them.

        :return: None
        """
        while not self._stopped:
            try:
                msg = self.out_queue.get(block=True, timeout=2.0)
                self.send(msg)
            except queue.Empty:
                pass

    def _receive_loop(self):
        """Receive messages."""
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

    def connect(self):
        """Connect to the local OEF Node."""
        if self._stopped:
            self._stopped = False
            self._connection = self.channel.connect()
            self.in_thread = Thread(target=self._receive_loop)
            self.out_thread = Thread(target=self._fetch)
            self.in_thread.start()
            self.out_thread.start()

    def disconnect(self):
        """Disconnect from the local OEF Node."""
        if not self._stopped:
            self._stopped = True
            self.in_thread.join()
            self.out_thread.join()
            self.in_thread = None
            self.out_thread = None
            self.channel.disconnect()
            self.stop()

    def send(self, envelope: Envelope):
        """Send a message."""
        if not self.is_established:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self.channel.send(envelope)

    def stop(self):
        """Tear down the connection."""
        self._connection = None

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the Local OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        local_node = LocalNode()
        return OEFLocalConnection(public_key, local_node)
