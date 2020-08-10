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
import copy
import logging
from asyncio import AbstractEventLoop, Queue
from collections import defaultdict
from threading import Thread
from typing import Dict, List, Optional, Tuple, cast

from aea.configurations.base import ProtocolId, PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.helpers.search.models import Description
from aea.mail.base import AEAConnectionError, Address, Envelope
from aea.protocols.default.message import DefaultMessage

from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

_default_logger = logging.getLogger("aea.packages.fetchai.connections.local")

TARGET = 0
MESSAGE_ID = 1
RESPONSE_TARGET = MESSAGE_ID
RESPONSE_MESSAGE_ID = MESSAGE_ID + 1
STUB_DIALOGUE_ID = 0
PUBLIC_ID = PublicId.from_str("fetchai/local:0.5.0")


class LocalNode:
    """A light-weight local implementation of a OEF Node."""

    def __init__(
        self, loop: AbstractEventLoop = None, logger: logging.Logger = _default_logger
    ):
        """
        Initialize a local (i.e. non-networked) implementation of an OEF Node.

        :param loop: the event loop. If None, a new event loop is instantiated.
        """
        self.services = defaultdict(lambda: [])  # type: Dict[str, List[Description]]
        self._lock = asyncio.Lock()
        self._loop = loop if loop is not None else asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop, daemon=True)

        self._in_queue = asyncio.Queue(loop=self._loop)  # type: asyncio.Queue
        self._out_queues = {}  # type: Dict[str, asyncio.Queue]

        self._receiving_loop_task = None  # type: Optional[asyncio.Task]
        self.address: Optional[Address] = None
        self._dialogues: Optional[OefSearchDialogues] = None
        self.logger = logger

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
        self.logger.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        self.logger.debug("Asyncio loop has been stopped.")

    async def connect(
        self, address: Address, writer: asyncio.Queue
    ) -> Optional[asyncio.Queue]:
        """
        Connect an address to the node.

        :param address: the address of the agent.
        :param writer: the queue where the client is listening.
        :return: an asynchronous queue, that constitutes the communication channel.
        """
        if address in self._out_queues.keys():
            return None

        assert self._in_queue is not None
        q = self._in_queue  # type: asyncio.Queue
        self._out_queues[address] = writer

        self.address = address
        self._dialogues = OefSearchDialogues(
            agent_address=str(OEFLocalConnection.connection_id)
        )
        return q

    def start(self):
        """Start the node."""
        if not self._loop.is_running() and not self._thread.is_alive():
            self._thread.start()
        self._receiving_loop_task = asyncio.run_coroutine_threadsafe(
            self.receiving_loop(), loop=self._loop
        )
        self.logger.debug("Local node has been started.")

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
                self.logger.debug("Receiving loop terminated.")
                return
            self.logger.debug("Handling envelope: {}".format(envelope))
            await self._handle_envelope(envelope)

    async def _handle_envelope(self, envelope: Envelope) -> None:
        """Handle an envelope.

        :param envelope: the envelope
        :return: None
        """
        if envelope.protocol_id == ProtocolId.from_str("fetchai/oef_search:0.4.0"):
            await self._handle_oef_message(envelope)
        else:
            await self._handle_agent_message(envelope)

    async def _handle_oef_message(self, envelope: Envelope) -> None:
        """Handle oef messages.

        :param envelope: the envelope
        :return: None
        """
        assert isinstance(
            envelope.message, OefSearchMessage
        ), "Message not of type OefSearchMessage"
        oef_message, dialogue = self._get_message_and_dialogue(envelope)

        if dialogue is None:
            self.logger.warning(
                "Could not create dialogue for message={}".format(oef_message)
            )
            return

        if oef_message.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
            await self._register_service(
                envelope.sender, oef_message.service_description
            )
        elif (
            oef_message.performative == OefSearchMessage.Performative.UNREGISTER_SERVICE
        ):
            await self._unregister_service(oef_message, dialogue)
        elif oef_message.performative == OefSearchMessage.Performative.SEARCH_SERVICES:
            await self._search_services(oef_message, dialogue)
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
            msg = DefaultMessage(
                performative=DefaultMessage.Performative.ERROR,
                dialogue_reference=("", ""),
                target=TARGET,
                message_id=MESSAGE_ID,
                error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
                error_msg="Destination not available",
                error_data={},  # TODO: reference incoming message.
            )
            error_envelope = Envelope(
                to=envelope.sender,
                sender=str(OEFLocalConnection.connection_id),
                protocol_id=DefaultMessage.protocol_id,
                message=msg,
            )
            await self._send(error_envelope)
            return
        else:
            await self._send(envelope)

    async def _register_service(
        self, address: Address, service_description: Description
    ):
        """
        Register a service agent in the service directory of the node.

        :param address: the address of the service agent to be registered.
        :param service_description: the description of the service agent to be registered.
        :return: None
        """
        async with self._lock:
            self.services[address].append(service_description)

    async def _unregister_service(
        self, oef_search_msg: OefSearchMessage, dialogue: OefSearchDialogue,
    ) -> None:
        """
        Unregister a service agent.

        :param oef_search_msg: the incoming message.
        :param dialogue: the dialogue.
        :return: None
        """
        service_description = oef_search_msg.service_description
        address = oef_search_msg.sender
        async with self._lock:
            if address not in self.services:
                msg = OefSearchMessage(
                    performative=OefSearchMessage.Performative.OEF_ERROR,
                    target=oef_search_msg.message_id,
                    message_id=oef_search_msg.message_id + 1,
                    oef_error_operation=OefSearchMessage.OefErrorOperation.UNREGISTER_SERVICE,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                )
                msg.counterparty = oef_search_msg.sender
                assert dialogue.update(msg)
                envelope = Envelope(
                    to=msg.counterparty,
                    sender=msg.sender,
                    protocol_id=msg.protocol_id,
                    message=msg,
                )
                await self._send(envelope)
            else:
                self.services[address].remove(service_description)
                if len(self.services[address]) == 0:
                    self.services.pop(address)

    async def _search_services(
        self, oef_search_msg: OefSearchMessage, dialogue: OefSearchDialogue,
    ) -> None:
        """
        Search the agents in the local Service Directory, and send back the result.

        This is actually a dummy search, it will return all the registered agents with the specified data model.
        If the data model is not specified, it will return all the agents.

        :param oef_search_msg: the message.
        :param dialogue: the dialogue.
        :return: None
        """
        async with self._lock:
            query = oef_search_msg.query
            result = []  # type: List[str]
            if query.model is None:
                result = list(set(self.services.keys()))
            else:
                for agent_address, descriptions in self.services.items():
                    for description in descriptions:
                        if description.data_model == query.model:
                            result.append(agent_address)

            msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                target=oef_search_msg.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                message_id=oef_search_msg.message_id + 1,
                agents=tuple(sorted(set(result))),
            )
            msg.counterparty = oef_search_msg.sender
            assert dialogue.update(msg)

            envelope = Envelope(
                to=msg.counterparty,
                sender=msg.sender,
                protocol_id=msg.protocol_id,
                message=msg,
            )
            await self._send(envelope)

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[OefSearchMessage, Optional[OefSearchDialogue]]:
        """
        Get a message copy and dialogue related to this message.

        :param envelope: incoming envelope

        :return: Tuple[MEssage, Optional[Dialogue]]
        """
        assert self._dialogues is not None, "Call connect before!"
        message_orig = cast(OefSearchMessage, envelope.message)
        message = copy.copy(
            message_orig
        )  # TODO: fix; need to copy atm to avoid overwriting "is_incoming"
        message.is_incoming = True  # TODO: fix; should be done by framework
        message.counterparty = (
            message_orig.sender
        )  # TODO: fix; should be done by framework
        dialogue = cast(OefSearchDialogue, self._dialogues.update(message))
        return message, dialogue

    async def _send(self, envelope: Envelope):
        """Send a message."""
        destination = envelope.to
        destination_queue = self._out_queues[destination]
        destination_queue._loop.call_soon_threadsafe(destination_queue.put_nowait, envelope)  # type: ignore  # pylint: disable=protected-access
        self.logger.debug("Send envelope {}".format(envelope))

    async def disconnect(self, address: Address) -> None:
        """
        Disconnect.

        :param address: the address of the agent
        :return: None
        """
        async with self._lock:
            self._out_queues.pop(address, None)
            self.services.pop(address, None)


class OEFLocalConnection(Connection):
    """
    Proxy to the functionality of the OEF.

    It allows the interaction between agents, but not the search functionality.
    It is useful for local testing.
    """

    connection_id = PUBLIC_ID

    def __init__(self, local_node: Optional[LocalNode] = None, **kwargs):
        """
        Load the connection configuration.

        Initialize a OEF proxy for a local OEF Node

        :param local_node: the Local OEF Node object. This reference must be the same across the agents of interest. (Note, AEA loader will not accept this argument.)
        """
        super().__init__(**kwargs)
        self._local_node = local_node
        self._reader = None  # type: Optional[Queue]
        self._writer = None  # type: Optional[Queue]

    async def connect(self) -> None:
        """Connect to the local OEF Node."""
        assert self._local_node is not None, "No local node set!"
        if self.is_connected:
            return
        self._state.set(ConnectionStates.connecting)
        self._reader = Queue()
        self._writer = await self._local_node.connect(self.address, self._reader)
        self._state.set(ConnectionStates.connected)

    async def disconnect(self) -> None:
        """Disconnect from the local OEF Node."""
        assert self._local_node is not None, "No local node set!"
        if self.is_disconnected:
            return
        self._state.set(ConnectionStates.disconnecting)
        assert self._reader is not None
        await self._local_node.disconnect(self.address)
        await self._reader.put(None)
        self._reader, self._writer = None, None
        self._state.set(ConnectionStates.disconnected)

    async def send(self, envelope: Envelope):
        """Send a message."""
        if not self.is_connected:
            raise AEAConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )
        self._writer._loop.call_soon_threadsafe(self._writer.put_nowait, envelope)  # type: ignore  # pylint: disable=protected-access

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        if not self.is_connected:
            raise AEAConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )
        try:
            assert self._reader is not None
            envelope = await self._reader.get()
            if envelope is None:
                self.logger.debug("Receiving task terminated.")
                return None
            self.logger.debug("Received envelope {}".format(envelope))
            return envelope
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            return None
