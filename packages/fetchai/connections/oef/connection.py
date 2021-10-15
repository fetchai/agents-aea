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
"""Extension to the OEF Python SDK."""

import asyncio
import logging
from asyncio import AbstractEventLoop, CancelledError
from concurrent.futures.thread import ThreadPoolExecutor
from itertools import cycle
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, cast

import oef
from oef.agents import OEFAgent
from oef.core import AsyncioCore
from oef.messages import CFP_TYPES, PROPOSE_TYPES

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.oef.object_translator import OEFObjectTranslator
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


_default_logger = logging.getLogger("aea.packages.fetchai.connections.oef")

TARGET = 0
MESSAGE_ID = 1
RESPONSE_TARGET = MESSAGE_ID
RESPONSE_MESSAGE_ID = MESSAGE_ID + 1
STUB_MESSAGE_ID = 0
STUB_DIALOGUE_ID = 0
DEFAULT_OEF = "oef"
PUBLIC_ID = PublicId.from_str("fetchai/oef:0.21.0")

OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(BaseOefSearchDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self) -> None:
        """Initialize dialogues."""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The oef connection maintains the dialogue on behalf of the node
            return OefSearchDialogue.Role.OEF_NODE

        BaseOefSearchDialogues.__init__(
            self,
            self_address=str(OEFConnection.connection_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=OefSearchDialogue,
        )


class OEFChannel(OEFAgent):
    """The OEFChannel connects the OEF Agent with the connection."""

    THREAD_POOL_SIZE = 3
    CONNECT_RETRY_DELAY = 5.0
    CONNECT_TIMEOUT = 2
    CONNECT_ATTEMPTS_LIMIT = 0

    def __init__(
        self,
        address: Address,
        oef_addr: str,
        oef_port: int,
        logger: Logger = _default_logger,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        :param logger: the logger.
        """
        super().__init__(
            address,
            oef_addr=oef_addr,
            oef_port=oef_port,
            core=AsyncioCore(logger=logger),
            logger=lambda *x: None,
            logger_debug=lambda *x: None,
        )
        self.address = address
        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._loop = None  # type: Optional[AbstractEventLoop]

        self.oef_search_dialogues = OefSearchDialogues()
        self.oef_msg_id = 0
        self.oef_msg_id_to_dialogue = {}  # type: Dict[int, OefSearchDialogue]

        self._threaded_pool = ThreadPoolExecutor(self.THREAD_POOL_SIZE)

        self.aea_logger = logger

    async def _run_in_executor(self, fn: Callable, *args: Any) -> None:
        if not self._loop:  # pragma: nocover
            raise ValueError("Channel not connected!")
        return await self._loop.run_in_executor(self._threaded_pool, fn, *args)

    @property
    def in_queue(self) -> asyncio.Queue:
        """Get input messages queue."""
        if not self._in_queue:  # pragma: nocover
            raise ValueError("Channel not connected!")
        return self._in_queue

    @property
    def loop(self) -> AbstractEventLoop:
        """Get event loop."""
        if not self._loop:  # pragma: nocover
            raise ValueError("Channel not connected!")
        return self._loop

    def on_message(  # pylint: disable=unused-argument
        self, msg_id: int, dialogue_id: int, origin: Address, content: bytes
    ) -> None:
        """
        On message event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param content: the bytes content.
        """
        # We are not using the 'msg_id', 'dialogue_id' and 'origin' parameters because 'content' contains a
        # serialized instance of 'Envelope', hence it already contains this information.
        self._check_loop_and_queue()
        envelope = Envelope.decode(content)
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    def on_cfp(
        self,
        msg_id: int,
        dialogue_id: int,
        origin: Address,
        target: int,
        query: CFP_TYPES,
    ) -> None:
        """
        On cfp event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param target: the message target.
        :param query: the query.
        """
        self._check_loop_and_queue()
        self.aea_logger.warning(
            "Dropping incompatible on_cfp: msg_id={}, dialogue_id={}, origin={}, target={}, query={}".format(
                msg_id, dialogue_id, origin, target, query
            )
        )

    def on_propose(  # pylint: disable=unused-argument
        self,
        msg_id: int,
        dialogue_id: int,
        origin: Address,
        target: int,
        proposals: PROPOSE_TYPES,
    ) -> None:
        """
        On propose event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param target: the message target.
        :param proposals: the proposals.
        """
        self._check_loop_and_queue()
        self.aea_logger.warning(
            "Dropping incompatible on_propose: msg_id={}, dialogue_id={}, origin={}, target={}".format(
                msg_id, dialogue_id, origin, target
            )
        )

    def on_accept(
        self, msg_id: int, dialogue_id: int, origin: Address, target: int
    ) -> None:
        """
        On accept event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param target: the message target.
        """
        self._check_loop_and_queue()
        self.aea_logger.warning(
            "Dropping incompatible on_accept: msg_id={}, dialogue_id={}, origin={}, target={}".format(
                msg_id, dialogue_id, origin, target
            )
        )

    def on_decline(
        self, msg_id: int, dialogue_id: int, origin: Address, target: int
    ) -> None:
        """
        On decline event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param target: the message target.
        """
        self._check_loop_and_queue()
        self.aea_logger.warning(
            "Dropping incompatible on_decline: msg_id={}, dialogue_id={}, origin={}, target={}".format(
                msg_id, dialogue_id, origin, target
            )
        )

    def on_search_result(self, search_id: int, agents: List[Address]) -> None:
        """
        On accept event handler.

        :param search_id: the search id.
        :param agents: the list of agents.
        """
        self._check_loop_and_queue()
        oef_search_dialogue = self.oef_msg_id_to_dialogue.pop(search_id, None)
        if oef_search_dialogue is None:
            self.aea_logger.warning(
                "Could not find dialogue for search_id={}".format(search_id)
            )  # pragma: nocover
            return  # pragma: nocover
        last_msg = oef_search_dialogue.last_incoming_message
        if last_msg is None:
            self.aea_logger.warning("Could not find last message.")  # pragma: nocover
            return  # pragma: nocover
        msg = oef_search_dialogue.reply(
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            target_message=last_msg,
            agents=tuple(agents),
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    def on_oef_error(
        self, answer_id: int, operation: oef.messages.OEFErrorOperation
    ) -> None:
        """
        On oef error event handler.

        :param answer_id: the answer id.
        :param operation: the error operation.
        """
        self._check_loop_and_queue()
        try:
            operation = OefSearchMessage.OefErrorOperation(operation)
        except ValueError:
            operation = OefSearchMessage.OefErrorOperation.OTHER
        oef_search_dialogue = self.oef_msg_id_to_dialogue.pop(answer_id, None)
        if oef_search_dialogue is None:
            self.aea_logger.warning(
                "Could not find dialogue for answer_id={}".format(answer_id)
            )  # pragma: nocover
            return  # pragma: nocover
        last_msg = oef_search_dialogue.last_incoming_message
        if last_msg is None:
            self.aea_logger.warning("Could not find last message.")  # pragma: nocover
            return  # pragma: nocover
        msg = oef_search_dialogue.reply(
            performative=OefSearchMessage.Performative.OEF_ERROR,
            target_message=last_msg,
            oef_error_operation=operation,
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    def on_dialogue_error(  # pylint: disable=unused-argument
        self, answer_id: int, dialogue_id: int, origin: Address
    ) -> None:
        """
        On dialogue error event handler.

        :param answer_id: the answer id.
        :param dialogue_id: the dialogue id.
        :param origin: the message sender.
        """
        self._check_loop_and_queue()
        msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=(str(answer_id), ""),
            target=TARGET,
            message_id=MESSAGE_ID,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Destination not available",
            error_data={},
        )
        envelope = Envelope(to=self.address, sender=DEFAULT_OEF, message=msg,)
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        """
        if (
            envelope.protocol_specification_id
            == OefSearchMessage.protocol_specification_id
        ):
            self.send_oef_message(envelope)
        else:
            self.send_default_message(envelope)

    def send_default_message(self, envelope: Envelope) -> None:
        """Send a 'default' message."""
        self.send_message(
            STUB_MESSAGE_ID, STUB_DIALOGUE_ID, envelope.to, envelope.encode()
        )

    def send_oef_message(self, envelope: Envelope) -> None:
        """
        Send oef message handler.

        :param envelope: the message.
        """
        enforce(
            isinstance(envelope.message, OefSearchMessage),
            "Message not of type OefSearchMessage",
        )
        oef_message = cast(OefSearchMessage, envelope.message)
        oef_search_dialogue = cast(
            OefSearchDialogue, self.oef_search_dialogues.update(oef_message)
        )
        if oef_search_dialogue is None:
            self.aea_logger.warning(
                "Could not create dialogue for message={}".format(oef_message)
            )  # pragma: nocover
            return  # pragma: nocover
        self.oef_msg_id += 1
        self.oef_msg_id_to_dialogue[self.oef_msg_id] = oef_search_dialogue
        if oef_message.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
            service_description = oef_message.service_description
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            self.register_service(self.oef_msg_id, oef_service_description)
        elif (
            oef_message.performative == OefSearchMessage.Performative.UNREGISTER_SERVICE
        ):
            service_description = oef_message.service_description
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            self.unregister_service(self.oef_msg_id, oef_service_description)
        elif oef_message.performative == OefSearchMessage.Performative.SEARCH_SERVICES:
            query = oef_message.query
            oef_query = OEFObjectTranslator.to_oef_query(query)
            self.search_services(self.oef_msg_id, oef_query)
        else:
            raise ValueError("OEF request not recognized.")  # pragma: nocover

    def handle_failure(  # pylint: disable=no-self-use,unused-argument
        self, exception: Exception, conn: Any
    ) -> None:
        """Handle failure."""
        self.aea_logger.exception(exception)  # pragma: nocover

    async def _set_loop_and_queue(self) -> None:
        self._loop = asyncio.get_event_loop()
        self._in_queue = asyncio.Queue()

    async def _unset_loop_and_queue(self) -> None:
        self._loop = None
        self._in_queue = None

    def _check_loop_and_queue(self) -> None:
        enforce(self.in_queue is not None, "In queue is not set!")
        enforce(self.loop is not None, "Loop is not set!")

    async def connect(  # pylint: disable=invalid-overridden-method,arguments-differ
        self,
    ) -> None:
        """Connect channel."""
        await self._set_loop_and_queue()
        self.core.__init__(loop=self._loop, logger=_default_logger)

        if self.CONNECT_ATTEMPTS_LIMIT != 0:  # pragma: nocover
            gen = range(self.CONNECT_ATTEMPTS_LIMIT)
        else:
            gen = cycle(range(1))  # type: ignore

        try:
            for _ in gen:
                is_connected = await self._run_in_executor(
                    self._oef_agent_connect, self.CONNECT_TIMEOUT
                )
                if is_connected:
                    return
                self.aea_logger.warning(
                    "Cannot connect to OEFChannel. Retrying in 5 seconds..."
                )
                await asyncio.sleep(self.CONNECT_RETRY_DELAY)

            raise ValueError("Connect attempts limit!")  # pragma: nocover
        except Exception:  # pragma: nocover
            await self._unset_loop_and_queue()
            raise

    def _oef_agent_connect(self, timeout: float = 2) -> bool:
        """
        Connect OEF agent.

        :param timeout: timeout to wait on connection
        :return: bool, connected or not
        """
        return super().connect(timeout)

    async def disconnect(self) -> None:  # pylint: disable=invalid-overridden-method
        """Disconnect channel."""
        if self._in_queue is None and self._loop is None:  # pragma: nocover
            return  # not connected so nothing to do

        await self.in_queue.put(None)
        await self._run_in_executor(super().disconnect)
        await self._unset_loop_and_queue()

    async def get(self) -> Optional[Envelope]:
        """Get incoming envelope."""
        return await self.in_queue.get()


class OEFConnection(Connection):
    """The OEFConnection connects the to the mailbox."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize.

        :param kwargs: the keyword arguments (check the parent constructor)
        """
        super().__init__(**kwargs)
        addr = cast(str, self.configuration.config.get("addr"))
        port = cast(int, self.configuration.config.get("port"))
        if addr is None or port is None:
            raise ValueError("addr and port must be set!")  # pragma: nocover
        self.oef_addr = addr
        self.oef_port = port
        self.channel = OEFChannel(self.address, self.oef_addr, self.oef_port, logger=self.logger)  # type: ignore
        self._connection_check_task = None  # type: Optional[asyncio.Future]

    async def connect(self) -> None:
        """
        Connect to the channel.

        :raises Exception if the connection to the OEF fails.
        """
        if self.is_connected:
            return

        with self._connect_context():
            self.channel.aea_logger = self.logger
            await self.channel.connect()
            self._connection_check_task = self.loop.create_task(
                self._connection_check()
            )

    async def _connection_check(self) -> None:
        """
        Check for connection to the channel.

        Try to reconnect if connection is dropped.
        """
        while self.is_connected:
            await asyncio.sleep(2.0)
            if not self.channel.get_state() == "connected":  # pragma: no cover
                self.state = ConnectionStates.connecting
                self.logger.warning(
                    "Lost connection to OEFChannel. Retrying to connect soon ..."
                )
                await self.channel.connect()
                self.state = ConnectionStates.connected
                self.logger.warning(
                    "Successfully re-established connection to OEFChannel."
                )

    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        if self.is_disconnected:
            return
        self.state = ConnectionStates.disconnecting
        if self._connection_check_task is not None:
            self._connection_check_task.cancel()
            self._connection_check_task = None
        await self.channel.disconnect()

        self.state = ConnectionStates.disconnected

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :param args: the positional arguments
        :param kwargs: the keyword arguments
        :return: the envelope received, or None.
        """
        try:
            envelope = await self.channel.get()
            if envelope is None:  # pragma: no cover
                self.logger.debug("Received None.")
                return None
            self.logger.debug("Received envelope: {}".format(envelope))
            return envelope
        except CancelledError:
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        if self.is_connected:
            self.channel.send(envelope)
