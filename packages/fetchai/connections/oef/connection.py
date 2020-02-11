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
import pickle  # nosec
import time
from asyncio import AbstractEventLoop, CancelledError
from threading import Thread
from typing import List, Optional, Set, cast

import oef
from oef.agents import OEFAgent
from oef.core import AsyncioCore
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.query import (
    And as OEFAnd,
    Constraint as OEFConstraint,
    ConstraintExpr as OEFConstraintExpr,
    ConstraintType as OEFConstraintType,
    Eq,
    Gt,
    GtEq,
    In,
    Lt,
    LtEq,
    Not as OEFNot,
    NotEq,
    NotIn,
    Or as OEFOr,
    Query as OEFQuery,
    Range,
)
from oef.schema import (
    AttributeSchema as OEFAttribute,
    DataModel as OEFDataModel,
    Description as OEFDescription,
)

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.helpers.search.models import (
    And,
    Attribute,
    Constraint,
    ConstraintExpr,
    ConstraintType,
    ConstraintTypes,
    DataModel,
    Description,
    Not,
    Or,
    Query,
)
from aea.mail.base import Address, Envelope

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer

logger = logging.getLogger(__name__)

STUB_MESSSAGE_ID = 0
STUB_DIALOGUE_ID = 0


class OEFObjectTranslator:
    """Translate our OEF object to object of OEF SDK classes."""

    @classmethod
    def to_oef_description(cls, desc: Description) -> OEFDescription:
        """From our description to OEF description."""
        oef_data_model = (
            cls.to_oef_data_model(desc.data_model)
            if desc.data_model is not None
            else None
        )
        return OEFDescription(desc.values, oef_data_model)

    @classmethod
    def to_oef_data_model(cls, data_model: DataModel) -> OEFDataModel:
        """From our data model to OEF data model."""
        oef_attributes = [
            cls.to_oef_attribute(attribute) for attribute in data_model.attributes
        ]
        return OEFDataModel(data_model.name, oef_attributes, data_model.description)

    @classmethod
    def to_oef_attribute(cls, attribute: Attribute) -> OEFAttribute:
        """From our attribute to OEF attribute."""
        return OEFAttribute(
            attribute.name, attribute.type, attribute.is_required, attribute.description
        )

    @classmethod
    def to_oef_query(cls, query: Query) -> OEFQuery:
        """From our query to OEF query."""
        oef_data_model = (
            cls.to_oef_data_model(query.model) if query.model is not None else None
        )
        constraints = [cls.to_oef_constraint_expr(c) for c in query.constraints]
        return OEFQuery(constraints, oef_data_model)

    @classmethod
    def to_oef_constraint_expr(
        cls, constraint_expr: ConstraintExpr
    ) -> OEFConstraintExpr:
        """From our constraint expression to the OEF constraint expression."""
        if isinstance(constraint_expr, And):
            return OEFAnd(
                [cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints]
            )
        elif isinstance(constraint_expr, Or):
            return OEFOr(
                [cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints]
            )
        elif isinstance(constraint_expr, Not):
            return OEFNot(cls.to_oef_constraint_expr(constraint_expr.constraint))
        elif isinstance(constraint_expr, Constraint):
            oef_constraint_type = cls.to_oef_constraint_type(
                constraint_expr.constraint_type
            )
            return OEFConstraint(constraint_expr.attribute_name, oef_constraint_type)
        else:
            raise ValueError("Constraint expression not supported.")

    @classmethod
    def to_oef_constraint_type(
        cls, constraint_type: ConstraintType
    ) -> OEFConstraintType:
        """From our constraint type to OEF constraint type."""
        value = constraint_type.value
        if constraint_type.type == ConstraintTypes.EQUAL:
            return Eq(value)
        elif constraint_type.type == ConstraintTypes.NOT_EQUAL:
            return NotEq(value)
        elif constraint_type.type == ConstraintTypes.LESS_THAN:
            return Lt(value)
        elif constraint_type.type == ConstraintTypes.LESS_THAN_EQ:
            return LtEq(value)
        elif constraint_type.type == ConstraintTypes.GREATER_THAN:
            return Gt(value)
        elif constraint_type.type == ConstraintTypes.GREATER_THAN_EQ:
            return GtEq(value)
        elif constraint_type.type == ConstraintTypes.WITHIN:
            return Range(value)
        elif constraint_type.type == ConstraintTypes.IN:
            return In(value)
        elif constraint_type.type == ConstraintTypes.NOT_IN:
            return NotIn(value)
        else:
            raise ValueError("Constraint type not recognized.")

    @classmethod
    def from_oef_description(cls, oef_desc: OEFDescription) -> Description:
        """From an OEF description to our description."""
        data_model = (
            cls.from_oef_data_model(oef_desc.data_model)
            if oef_desc.data_model is not None
            else None
        )
        return Description(oef_desc.values, data_model=data_model)

    @classmethod
    def from_oef_data_model(cls, oef_data_model: OEFDataModel) -> DataModel:
        """From an OEF data model to our data model."""
        attributes = [
            cls.from_oef_attribute(oef_attribute)
            for oef_attribute in oef_data_model.attribute_schemas
        ]
        return DataModel(oef_data_model.name, attributes, oef_data_model.description)

    @classmethod
    def from_oef_attribute(cls, oef_attribute: OEFAttribute) -> Attribute:
        """From an OEF attribute to our attribute."""
        return Attribute(
            oef_attribute.name,
            oef_attribute.type,
            oef_attribute.required,
            oef_attribute.description,
        )

    @classmethod
    def from_oef_query(cls, oef_query: OEFQuery) -> Query:
        """From our query to OrOEF query."""
        data_model = (
            cls.from_oef_data_model(oef_query.model)
            if oef_query.model is not None
            else None
        )
        constraints = [cls.from_oef_constraint_expr(c) for c in oef_query.constraints]
        return Query(constraints, data_model)

    @classmethod
    def from_oef_constraint_expr(
        cls, oef_constraint_expr: OEFConstraintExpr
    ) -> ConstraintExpr:
        """From our query to OEF query."""
        if isinstance(oef_constraint_expr, OEFAnd):
            return And(
                [
                    cls.from_oef_constraint_expr(c)
                    for c in oef_constraint_expr.constraints
                ]
            )
        elif isinstance(oef_constraint_expr, OEFOr):
            return Or(
                [
                    cls.from_oef_constraint_expr(c)
                    for c in oef_constraint_expr.constraints
                ]
            )
        elif isinstance(oef_constraint_expr, OEFNot):
            return Not(cls.from_oef_constraint_expr(oef_constraint_expr.constraint))
        elif isinstance(oef_constraint_expr, OEFConstraint):
            constraint_type = cls.from_oef_constraint_type(
                oef_constraint_expr.constraint
            )
            return Constraint(oef_constraint_expr.attribute_name, constraint_type)
        else:
            raise ValueError("OEF Constraint not supported.")

    @classmethod
    def from_oef_constraint_type(
        cls, constraint_type: OEFConstraintType
    ) -> ConstraintType:
        """From OEF constraint type to our constraint type."""
        if isinstance(constraint_type, Eq):
            return ConstraintType(ConstraintTypes.EQUAL, constraint_type.value)
        elif isinstance(constraint_type, NotEq):
            return ConstraintType(ConstraintTypes.NOT_EQUAL, constraint_type.value)
        elif isinstance(constraint_type, Lt):
            return ConstraintType(ConstraintTypes.LESS_THAN, constraint_type.value)
        elif isinstance(constraint_type, LtEq):
            return ConstraintType(ConstraintTypes.LESS_THAN_EQ, constraint_type.value)
        elif isinstance(constraint_type, Gt):
            return ConstraintType(ConstraintTypes.GREATER_THAN, constraint_type.value)
        elif isinstance(constraint_type, GtEq):
            return ConstraintType(
                ConstraintTypes.GREATER_THAN_EQ, constraint_type.value
            )
        elif isinstance(constraint_type, Range):
            return ConstraintType(ConstraintTypes.WITHIN, constraint_type.values)
        elif isinstance(constraint_type, In):
            return ConstraintType(ConstraintTypes.IN, constraint_type.values)
        elif isinstance(constraint_type, NotIn):
            return ConstraintType(ConstraintTypes.NOT_IN, constraint_type.values)
        else:
            raise ValueError("Constraint type not recognized.")


class OEFChannel(OEFAgent):
    """The OEFChannel connects the OEF Agent with the connection."""

    def __init__(
        self,
        address: Address,
        oef_addr: str,
        oef_port: int,
        core: AsyncioCore,
        excluded_protocols: Optional[Set[str]] = None,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        """
        super().__init__(
            address,
            oef_addr=oef_addr,
            oef_port=oef_port,
            core=core,
            logger=lambda *x: None,
            logger_debug=lambda *x: None,
        )
        self.address = address
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[AbstractEventLoop]
        self.excluded_protocols = excluded_protocols

    def on_message(
        self, msg_id: int, dialogue_id: int, origin: Address, content: bytes
    ) -> None:
        """
        On message event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param content: the bytes content.
        :return: None
        """
        # We are not using the 'msg_id', 'dialogue_id' and 'origin' parameters because 'content' contains a
        # serialized instance of 'Envelope', hence it already contains this information.
        assert self.in_queue is not None
        assert self.loop is not None
        envelope = Envelope.decode(content)
        asyncio.run_coroutine_threadsafe(
            self.in_queue.put(envelope), self.loop
        ).result()

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
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        logger.warning(
            "Accepting on_cfp from deprecated API: msg_id={}, dialogue_id={}, origin={}, target={}. Continuing dialogue via envelopes!".format(
                msg_id, dialogue_id, origin, target
            )
        )
        try:
            query = pickle.loads(query)  # nosec
        except Exception as e:
            logger.debug(
                "When trying to unpickle the query the following exception occured: {}".format(
                    e
                )
            )
        msg = FIPAMessage(
            message_id=msg_id,
            dialogue_reference=(str(dialogue_id), ""),
            target=target,
            performative=FIPAMessage.Performative.CFP,
            query=query if query != b"" else None,
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=origin,
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )
        asyncio.run_coroutine_threadsafe(
            self.in_queue.put(envelope), self.loop
        ).result()

    def on_propose(
        self,
        msg_id: int,
        dialogue_id: int,
        origin: Address,
        target: int,
        b_proposals: PROPOSE_TYPES,
    ) -> None:
        """
        On propose event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the address of the sender.
        :param target: the message target.
        :param b_proposals: the proposals.
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        logger.warning(
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
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        logger.warning(
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
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        logger.warning(
            "Dropping incompatible on_decline: msg_id={}, dialogue_id={}, origin={}, target={}".format(
                msg_id, dialogue_id, origin, target
            )
        )

    def on_search_result(self, search_id: int, agents: List[Address]) -> None:
        """
        On accept event handler.

        :param search_id: the search id.
        :param agents: the list of agents.
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        msg = OEFMessage(
            type=OEFMessage.Type.SEARCH_RESULT, id=search_id, agents=agents
        )
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=OEFMessage.protocol_id,
            message=msg_bytes,
        )
        asyncio.run_coroutine_threadsafe(
            self.in_queue.put(envelope), self.loop
        ).result()

    def on_oef_error(
        self, answer_id: int, operation: oef.messages.OEFErrorOperation
    ) -> None:
        """
        On oef error event handler.

        :param answer_id: the answer id.
        :param operation: the error operation.
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        try:
            operation = OEFMessage.OEFErrorOperation(operation)
        except ValueError:
            operation = OEFMessage.OEFErrorOperation.OTHER

        msg = OEFMessage(
            type=OEFMessage.Type.OEF_ERROR, id=answer_id, operation=operation
        )
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=OEFMessage.protocol_id,
            message=msg_bytes,
        )
        asyncio.run_coroutine_threadsafe(
            self.in_queue.put(envelope), self.loop
        ).result()

    def on_dialogue_error(
        self, answer_id: int, dialogue_id: int, origin: Address
    ) -> None:
        """
        On dialogue error event handler.

        :param answer_id: the answer id.
        :param dialogue_id: the dialogue id.
        :param origin: the message sender.
        :return: None
        """
        assert self.in_queue is not None
        assert self.loop is not None
        msg = OEFMessage(
            type=OEFMessage.Type.DIALOGUE_ERROR,
            id=answer_id,
            dialogue_id=dialogue_id,
            origin=origin,
        )
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=OEFMessage.protocol_id,
            message=msg_bytes,
        )
        asyncio.run_coroutine_threadsafe(
            self.in_queue.put(envelope), self.loop
        ).result()

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        :return: None
        """
        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the oef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")
        if envelope.protocol_id == PublicId.from_str("fetchai/oef:0.1.0"):
            self.send_oef_message(envelope)
        else:
            self.send_default_message(envelope)

    def send_default_message(self, envelope: Envelope):
        """Send a 'default' message."""
        self.send_message(
            STUB_MESSSAGE_ID, STUB_DIALOGUE_ID, envelope.to, envelope.encode()
        )

    def send_oef_message(self, envelope: Envelope) -> None:
        """
        Send oef message handler.

        :param envelope: the message.
        :return: None
        """
        oef_message = OEFSerializer().decode(envelope.message)
        oef_message = cast(OEFMessage, oef_message)
        oef_type = oef_message.type
        oef_msg_id = oef_message.id
        if oef_type == OEFMessage.Type.REGISTER_SERVICE:
            service_description = oef_message.service_description
            service_id = oef_message.service_id
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            self.register_service(oef_msg_id, oef_service_description, service_id)
        elif oef_type == OEFMessage.Type.UNREGISTER_SERVICE:
            service_description = oef_message.service_description
            service_id = oef_message.service_id
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            self.unregister_service(oef_msg_id, oef_service_description, service_id)
        elif oef_type == OEFMessage.Type.SEARCH_AGENTS:
            query = oef_message.query
            oef_query = OEFObjectTranslator.to_oef_query(query)
            self.search_agents(oef_msg_id, oef_query)
        elif oef_type == OEFMessage.Type.SEARCH_SERVICES:
            query = oef_message.query
            oef_query = OEFObjectTranslator.to_oef_query(query)
            self.search_services(oef_msg_id, oef_query)
        else:
            raise ValueError("OEF request not recognized.")


class OEFConnection(Connection):
    """The OEFConnection connects the to the mailbox."""

    def __init__(
        self, address: Address, oef_addr: str, oef_port: int = 10000, *args, **kwargs
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        :param connection_id: the identifier of the connection object.
        :param restricted_to_protocols: the only supported protocols for this connection.
        :param excluded_protocols: the excluded protocols for this connection.
        """
        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "oef", "0.1.0")
        super().__init__(*args, **kwargs)
        self._core = AsyncioCore(logger=logger)  # type: AsyncioCore
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.channel = OEFChannel(
            address, oef_addr, oef_port, core=self._core,
        )  # type: ignore

        self._connection_check_thread = None  # type: Optional[Thread]

    async def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises Exception if the connection to the OEF fails.
        """
        if self.connection_status.is_connected:
            return
        try:
            self._core.run_threaded()
            loop = asyncio.get_event_loop()
            self.in_queue = asyncio.Queue()
            await self._try_connect()
            self.connection_status.is_connected = True
            self.channel.loop = loop
            self.channel.in_queue = self.in_queue
            self._connection_check_thread = Thread(target=self._connection_check)
            self._connection_check_thread.start()
        except (CancelledError, Exception) as e:  # pragma: no cover
            self._core.stop()
            self.connection_status.is_connected = False
            raise e

    async def _try_connect(self) -> None:
        """
        Try connect to the channel.

        :return: None
        :raises Exception if the connection to the OEF fails.
        """
        while not self.connection_status.is_connected:
            if not self.channel.connect():
                logger.warning("Cannot connect to OEFChannel. Retrying in 5 seconds...")
                await asyncio.sleep(5.0)
            else:
                break

    def _connection_check(self) -> None:
        """
        Check for connection to the channel.

        Try to reconnect if connection is dropped.

        :return: None
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.connection_status.is_connected:
            time.sleep(2.0)
            if not self.channel.get_state() == "connected":  # pragma: no cover
                self.connection_status.is_connected = False
                logger.warning(
                    "Lost connection to OEFChannel. Retrying to connect soon ..."
                )
                loop.run_until_complete(self._try_connect())
                self.connection_status.is_connected = True
                logger.warning("Successfully re-established connection to OEFChannel.")

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert (
            self._connection_check_thread is not None
        ), "Call connect before disconnect."
        assert self.in_queue is not None
        self.connection_status.is_connected = False
        self._connection_check_thread.join()
        self._connection_check_thread = None
        self.channel.disconnect()
        await self.in_queue.put(None)
        self._core.stop()

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            assert self.in_queue is not None
            envelope = await self.in_queue.get()
            if envelope is None:
                logger.debug("Received None.")
                return None
            logger.debug("Received envelope: {}".format(envelope))
            return envelope
        except CancelledError:
            logger.debug("Receive cancelled.")
            return None
        except Exception as e:
            logger.exception(e)
            return None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        if self.connection_status.is_connected:
            self.channel.send(envelope)

    @classmethod
    def from_config(
        cls, address: Address, connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the OEF connection from the connection configuration.

        :param address: the address of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        oef_addr = cast(str, connection_configuration.config.get("addr"))
        oef_port = cast(int, connection_configuration.config.get("port"))
        restricted_to_protocols_names = {
            p.name for p in connection_configuration.restricted_to_protocols
        }
        excluded_protocols_names = {
            p.name for p in connection_configuration.excluded_protocols
        }
        return OEFConnection(
            address,
            oef_addr,
            oef_port,
            connection_id=connection_configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )
