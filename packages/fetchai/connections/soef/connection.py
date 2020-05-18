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

"""Extension to the Simple OEF and OEF Python SDK."""

import asyncio
import logging
import pickle  # nosec
from asyncio import AbstractEventLoop, CancelledError
from typing import Dict, List, Optional, Set, Tuple, cast

from defusedxml import ElementTree as ET

import oef
from oef.agents import OEFAgent
from oef.core import AsyncioCore
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.query import (
    And as OEFAnd,
    Constraint as OEFConstraint,
    ConstraintExpr as OEFConstraintExpr,
    ConstraintType as OEFConstraintType,
    Distance,
    Eq,
    Gt,
    GtEq,
    In,
    Location as OEFLocation,
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

import requests

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
    Location,
    Not,
    Or,
    Query,
)
from aea.mail.base import Address, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer

logger = logging.getLogger("aea.packages.fetchai.connections.oef")

TARGET = 0
MESSAGE_ID = 1
RESPONSE_TARGET = MESSAGE_ID
RESPONSE_MESSAGE_ID = MESSAGE_ID + 1
STUB_MESSAGE_ID = 0
STUB_DIALOGUE_ID = 0
DEFAULT_OEF = "default_oef"
PUBLIC_ID = PublicId.from_str("fetchai/oef:0.2.0")


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

        new_values = {}
        location_keys = set()
        loggers_by_key = {}
        for key, value in desc.values.items():
            if isinstance(value, Location):
                oef_location = OEFLocation(value.latitude, value.longitude)
                location_keys.add(key)
                new_values[key] = oef_location
            else:
                new_values[key] = value

        # this is a workaround to make OEFLocation objects deep-copyable.
        # Indeed, there is a problem in deep-copying such objects
        # because of the logger object they have attached.
        # Steps:
        # 1) we remove the loggers attached to each Location obj,
        # 2) then we instantiate the description (it runs deepcopy on the values),
        # 3) and then we reattach the loggers.
        for key in location_keys:
            loggers_by_key[key] = new_values[key].log
            # in this way we remove the logger
            new_values[key].log = None

        description = OEFDescription(new_values, oef_data_model)

        for key in location_keys:
            new_values[key].log = loggers_by_key[key]

        return description

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

        # in case the attribute type is Location, replace with the `oef` class.
        attribute_type = OEFLocation if attribute.type == Location else attribute.type
        return OEFAttribute(
            attribute.name, attribute_type, attribute.is_required, attribute.description
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
    def to_oef_location(cls, location: Location) -> OEFLocation:
        """From our location to OEF location."""
        return OEFLocation(location.latitude, location.longitude)  # type: ignore

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
        elif constraint_type.type == ConstraintTypes.DISTANCE:
            location = cls.to_oef_location(location=value[0])
            return Distance(center=location, distance=value[1])
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

        new_values = {}
        for key, value in oef_desc.values.items():
            if isinstance(value, OEFLocation):
                new_values[key] = Location(value.latitude, value.longitude)
            else:
                new_values[key] = value

        return Description(new_values, data_model=data_model)

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
        oef_attribute_type = (
            Location if oef_attribute.type == OEFLocation else oef_attribute.type
        )
        return Attribute(
            oef_attribute.name,
            oef_attribute_type,
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
    def from_oef_location(cls, oef_location: OEFLocation) -> Location:
        """From oef location to our location."""
        return Location(oef_location.latitude, oef_location.longitude)

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
        elif isinstance(constraint_type, Distance):
            location = cls.from_oef_location(constraint_type.center)
            return ConstraintType(
                ConstraintTypes.DISTANCE, (location, constraint_type.distance)
            )
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
        self.oef_msg_id = 0
        self.oef_msg_it_to_dialogue_reference = {}  # type: Dict[int, Tuple[str, str]]

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
        msg = FipaMessage(
            message_id=msg_id,
            dialogue_reference=(str(dialogue_id), ""),
            target=target,
            performative=FipaMessage.Performative.CFP,
            query=query if query != b"" else None,
        )
        msg_bytes = FipaSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=origin,
            protocol_id=FipaMessage.protocol_id,
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
        dialogue_reference = self.oef_msg_it_to_dialogue_reference[search_id]
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            dialogue_reference=dialogue_reference,
            target=RESPONSE_TARGET,
            message_id=RESPONSE_MESSAGE_ID,
            agents=tuple(agents),
        )
        msg_bytes = OefSearchSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=OefSearchMessage.protocol_id,
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
            operation = OefSearchMessage.OefErrorOperation(operation)
        except ValueError:
            operation = OefSearchMessage.OefErrorOperation.OTHER
        dialogue_reference = self.oef_msg_it_to_dialogue_reference[answer_id]
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.OEF_ERROR,
            dialogue_reference=dialogue_reference,
            target=RESPONSE_TARGET,
            message_id=RESPONSE_MESSAGE_ID,
            oef_error_operation=operation,
        )
        msg_bytes = OefSearchSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=OefSearchMessage.protocol_id,
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
        msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=(str(answer_id), ""),
            target=TARGET,
            message_id=MESSAGE_ID,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Destination not available",
            error_data={},  # TODO: add helper info
        )
        msg_bytes = DefaultSerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=DEFAULT_OEF,
            protocol_id=DefaultMessage.protocol_id,
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
        if envelope.protocol_id == PublicId.from_str("fetchai/oef_search:0.1.0"):
            self.send_oef_message(envelope)
        else:
            self.send_default_message(envelope)

    def send_default_message(self, envelope: Envelope):
        """Send a 'default' message."""
        self.send_message(
            STUB_MESSAGE_ID, STUB_DIALOGUE_ID, envelope.to, envelope.encode()
        )

    def send_oef_message(self, envelope: Envelope) -> None:
        """
        Send oef message handler.

        :param envelope: the message.
        :return: None
        """
        oef_message = OefSearchSerializer().decode(envelope.message)
        oef_message = cast(OefSearchMessage, oef_message)
        self.oef_msg_id += 1
        self.oef_msg_it_to_dialogue_reference[self.oef_msg_id] = (
            oef_message.dialogue_reference[0],
            str(self.oef_msg_id),
        )
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
            raise ValueError("OEF request not recognized.")


API_KEY = "TwiCIriSl0mLahw17pyqoA"


class SOEFChannel:
    """The OEFChannel connects the OEF Agent with the connection."""

    def __init__(
        self,
        address: Address,
        soef_addr: str,
        soef_port: int,
        excluded_protocols: Optional[Set[str]] = None,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        """
        self.address = address
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self.base_url = "http://{}:{}".format(soef_addr, soef_port)
        self.excluded_protocols = excluded_protocols
        self.oef_msg_id = 0
        self.oef_msg_it_to_dialogue_reference = {}  # type: Dict[int, Tuple[str, str]]
        self.service_name_to_page_address = {}  # type: Dict[str, str]
        self.in_queue = None  # type: Optional[asyncio.Queue]

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        :return: None
        """
        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the soef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")
        if envelope.protocol_id == PublicId.from_str("fetchai/oef_search:0.1.0"):
            self.send_soef_message(envelope)
        else:
            raise ValueError("Cannot send message.")

    def send_soef_message(self, envelope: Envelope) -> None:
        """
        Send soef message handler.

        :param envelope: the message.
        :return: None
        """
        oef_message = OefSearchSerializer().decode(envelope.message)
        oef_message = cast(OefSearchMessage, oef_message)
        self.oef_msg_id += 1
        self.oef_msg_it_to_dialogue_reference[self.oef_msg_id] = (
            oef_message.dialogue_reference[0],
            str(self.oef_msg_id),
        )
        if oef_message.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
            service_description = oef_message.service_description
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            service_name = oef_service_description.values["service_name"]
            service_location = oef_service_description.values["location"]
            self.register_service(self.oef_msg_id, service_name, service_location)
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
            raise ValueError("OEF request not recognized.")

    def register_service(
        self, msg_id: int, service_name: str, service_location: OEFLocation
    ):
        """
        Register a service on the SOEF.

        :param service_name: the name of the service
        :param service_location: the location of the service
        """
        unique_page_address = self._register_service(service_name)
        if unique_page_address is not None:
            self._set_location(service_location, unique_page_address)

    def _register_service(self, service_name: str) -> Optional[str]:
        """
        Register a service.

        :param service_name: the service name
        :return: the unique page address
        """
        logger.debug("Applying to SOEF lobby with address={}".format(self.address))
        url = self.base_url + "/register"
        params = {
            "api_key": API_KEY,
            "chain_identifier": "fetchai",
            "address": self.address,
            "declared_name": service_name,
        }
        try:
            response = requests.get(url=url, params=params)
            logger.debug("Response: {}".format(response.text))
            root = ET.fromstring(response.text)
            logger.debug("Root tag: {}".format(root.tag))
            unique_page_address = ""
            unique_token = ""  # nosec
            for child in root:
                logger.debug(
                    "Child tag={}, child attrib={}, child text={}".format(
                        child.tag, child.attrib, child.text
                    )
                )
                if "page_address" == child.tag and child.text is not None:
                    unique_page_address = child.text
                if "token" == child.tag and child.text is not None:
                    unique_token = child.text
            if len(unique_page_address) > 0 and len(unique_token) > 0:
                logger.debug("Registering service {}".format(service_name))
                url = self.base_url + "/" + unique_page_address
                params = {"token": unique_token, "command": "acknowledge"}
                response = requests.get(url=url, params=params)
                if response.text == "<response><success>1</success></response>":
                    logger.debug("Service registration SUCCESS")
                    self.service_name_to_page_address[
                        service_name
                    ] = unique_page_address
                    return unique_page_address
                else:
                    raise ValueError(
                        "Service registration error - acknowledge not accepted"
                    )
            else:
                raise ValueError(
                    "Service registration error - page address or token not received"
                )
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))
            return None

    def _set_location(
        self, service_location: OEFLocation, unique_page_address: str
    ) -> None:
        """
        Set the location.

        :param service_location: the service location
        :param unique_page_address: the page address where the service is registered
        """
        try:
            latitude = service_location.latitude
            longitude = service_location.longitude

            logger.debug(
                "Registering position lat={}, long={}".format(latitude, longitude)
            )
            url = self.base_url + "/" + unique_page_address
            params = {
                "longitude": longitude,
                "latitude": latitude,
                "command": "set_position",
            }
            response = requests.get(url=url, params=params)
            if response.text == "<response><success>1</success></response>":
                logger.debug("Location registration SUCCESS")
            else:
                raise ValueError("Location registration error.")
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))

    def unregister_service(self, msg_id: int, oef_service_description):
        raise NotImplementedError

    def search_services(self, msg_id: int, oef_query: OEFQuery) -> None:
        """
        Search services on the SOEF.

        :param msg_id: the message id
        :param oef_query: the oef query
        """
        constraint_distance = [
            c for c in oef_query.constraints if type(c.constraint) == Distance
        ][0]
        constraint_name = [
            c for c in oef_query.constraints if type(c.constraint) == Eq
        ][0]
        radius = constraint_distance.constraint.distance
        service_name = constraint_name.constraint.value
        service_location = constraint_distance.constraint.center
        if service_name not in self.service_name_to_page_address:
            unique_page_address = self.register_service(
                msg_id, service_name, service_location
            )
        else:
            unique_page_address = self.service_name_to_page_address.get(service_name)
        if unique_page_address is not None:
            self._search_range(unique_page_address, radius, service_name)

    def _search_range(
        self, unique_page_address: str, radius: float, service_name: str
    ) -> None:
        """
        Search services on the SOEF.
        """
        assert self.in_queue is not None, "Inqueue not set!"
        try:
            logger.debug(
                "Searching in radius={} of service={}".format(radius, service_name)
            )
            url = self.base_url + "/" + unique_page_address
            params = {
                "range_in_km": str(radius),
                "command": "find_around_me",
            }
            response = requests.get(url=url, params=params)
            root = ET.fromstring(response.text)
            agents = {}  # type: Dict[str, Dict[str, str]]
            agents_l = []  # type: List[str]
            for child in root:
                for child_ in child:
                    data = {}
                    for child__ in child_:
                        if child__.text is not None:
                            data[child__.tag] = child__.text
                        for child___ in child__:
                            if child___.text is not None:
                                data[child___.tag] = child___.text
                    if data["chain_identifier"] not in agents:
                        agents[data["chain_identifier"]] = {}
                    agents[data["chain_identifier"]][data["address"]] = data[
                        "range_in_km"
                    ]
                    agents_l.append(data["address"])
            if root.tag == "response":
                logger.debug("Search SUCCESS")
                message = OefSearchMessage(
                    performative=OefSearchMessage.Performative.SEARCH_RESULT,
                    agents=tuple(agents_l),
                )
                envelope = Envelope(
                    to=self.address,
                    sender="simple_oef",
                    protocol_id=OefSearchMessage.protocol_id,
                    message=OefSearchSerializer().encode(message),
                )
                self.in_queue.put_nowait(envelope)
            else:
                raise ValueError("Location registration error.")
        except Exception as e:
            logger.error("Exception when interacting with SOEF: {}".format(e))

        # command=find_around_me&range_in_km=20


class MultiChannel:
    """The MultiChannel connects the OEF Channel and the SOEF Channel with the connection."""

    def __init__(
        self,
        address: Address,
        oef_addr: str,
        oef_port: int,
        soef_addr: str,
        soef_port: int,
        core: AsyncioCore,
        excluded_protocols: Optional[Set[str]] = None,
    ):
        """
        Initialize.

        :param address: the address of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        """
        self.oef_channel = OEFChannel(address, oef_addr, oef_port, core=core)  # type: ignore
        self.loop = self.oef_channel.loop
        self.soef_channel = SOEFChannel(address, soef_addr, soef_port)

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        :return: None
        """
        if self.is_using_oef(envelope):
            self.oef_channel.send(envelope)
        else:
            self.soef_channel.send(envelope)

    def connect(self) -> bool:
        """
        Connect to the channel.

        :return: bool
        """
        return self.oef_channel.connect()

    def disconnect(self) -> None:
        """
        Disconnect to the channel.

        :return: None
        """
        self.oef_channel.disconnect()

    def get_state(self) -> str:
        """
        Get the connection state.

        :return: str indicating state
        """
        return self.oef_channel.get_state()

    @staticmethod
    def is_using_oef(envelope: Envelope) -> bool:
        """
        Whether or not the envelope is using the oef.

        :param envelope: the envelope
        :return: bool
        """
        is_using_oef = True
        if envelope.protocol_id != PublicId.from_str("fetchai/oef_search:0.1.0"):
            return is_using_oef
        oef_message = OefSearchSerializer().decode(envelope.message)
        oef_message = cast(OefSearchMessage, oef_message)
        if oef_message.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
            service_description = oef_message.service_description
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            if len(oef_service_description.values) == 2:
                is_using_oef = not (
                    isinstance(
                        oef_service_description.values.get("service_name", None), str
                    )
                    and isinstance(
                        oef_service_description.values.get("location", None),
                        OEFLocation,
                    )
                )
        elif (
            oef_message.performative == OefSearchMessage.Performative.UNREGISTER_SERVICE
        ):
            service_description = oef_message.service_description
            oef_service_description = OEFObjectTranslator.to_oef_description(
                service_description
            )
            if len(oef_service_description.values) == 2:
                is_using_oef = not (
                    isinstance(
                        oef_service_description.values.get("service_name", None), str
                    )
                    and isinstance(
                        oef_service_description.values.get("location", None),
                        OEFLocation,
                    )
                )
        elif oef_message.performative == OefSearchMessage.Performative.SEARCH_SERVICES:
            query = oef_message.query
            oef_query = OEFObjectTranslator.to_oef_query(query)
            if len(oef_query.constraints) == 2:
                constraint_one = oef_query.constraints[0]
                constraint_two = oef_query.constraints[1]
                is_using_oef = not (
                    set([constraint_one.attribute_name, constraint_two.attribute_name])
                    == set(["location", "service_name"])
                    and set(
                        [
                            type(constraint_one.constraint),
                            type(constraint_two.constraint),
                        ]
                    )
                    == set([Distance, Eq])
                )
        return is_using_oef


class SOEFConnection(Connection):
    """The SOEFConnection connects the Simple OEF to the mailbox."""

    def __init__(
        self,
        oef_addr: str,
        oef_port: int = 10000,
        soef_addr: str = "127.0.0.1",
        soef_port: int = 10001,
        **kwargs
    ):
        """
        Initialize.

        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        :param soef_addr: the SOEF IP address.
        :param soef_port: the SOEF port.
        :param kwargs: the keyword arguments (check the parent constructor)
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PUBLIC_ID
        super().__init__(**kwargs)
        self.oef_addr = oef_addr
        self.oef_port = oef_port
        self.soef_addr = soef_addr
        self.soef_port = soef_port
        self._core = AsyncioCore(logger=logger)  # type: AsyncioCore
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.channel = MultiChannel(self.address, self.oef_addr, self.oef_port, self.soef_addr, self.soef_port, core=self._core)  # type: ignore
        self._connection_check_task = None  # type: Optional[asyncio.Future]

    async def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises Exception if the connection to the OEF fails.
        """
        if self.connection_status.is_connected:
            return
        try:
            self.connection_status.is_connecting = True
            self._core.run_threaded()
            loop = asyncio.get_event_loop()
            self.in_queue = asyncio.Queue()
            await self._try_connect()
            self.connection_status.is_connecting = False
            self.connection_status.is_connected = True
            self.channel.loop = loop
            self.channel.oef_channel.in_queue = self.in_queue
            self.channel.soef_channel.in_queue = self.in_queue
            self._connection_check_task = asyncio.ensure_future(
                self._connection_check(), loop=self._loop
            )
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

    async def _connection_check(self) -> None:
        """
        Check for connection to the channel.

        Try to reconnect if connection is dropped.

        :return: None
        """
        while self.connection_status.is_connected:
            await asyncio.sleep(2.0)
            if not self.channel.get_state() == "connected":  # pragma: no cover
                self.connection_status.is_connected = False
                self.connection_status.is_connecting = True
                logger.warning(
                    "Lost connection to OEFChannel. Retrying to connect soon ..."
                )
                await self._try_connect()
                self.connection_status.is_connected = True
                logger.warning("Successfully re-established connection to OEFChannel.")

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert (
            self.connection_status.is_connected or self.connection_status.is_connecting
        ), "Call connect before disconnect."
        assert self.in_queue is not None
        self.connection_status.is_connected = False
        self.connection_status.is_connecting = False
        if self._connection_check_task is not None:
            self._connection_check_task.cancel()
            self._connection_check_task = None
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
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the OEF connection from the connection configuration.
        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        oef_addr = cast(str, configuration.config.get("oef_addr"))
        oef_port = cast(int, configuration.config.get("oef_port"))
        soef_addr = cast(str, configuration.config.get("soef_addr"))
        soef_port = cast(int, configuration.config.get("soef_port"))
        return SOEFConnection(
            oef_addr,
            oef_port,
            soef_addr,
            soef_port,
            address=address,
            configuration=configuration,
        )
