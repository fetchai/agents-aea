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
import datetime
import logging
import pickle
from queue import Empty, Queue
from threading import Thread
from typing import List, Dict, Optional, cast

import oef
from oef.agents import OEFAgent
from oef.core import AsyncioCore
from oef.messages import CFP_TYPES, PROPOSE_TYPES
from oef.query import (
    Query as OEFQuery,
    ConstraintExpr as OEFConstraintExpr,
    And as OEFAnd,
    Or as OEFOr,
    Not as OEFNot,
    Constraint as OEFConstraint,
    ConstraintType as OEFConstraintType, Eq, NotEq, Lt, LtEq, Gt, GtEq, Range, In, NotIn)
from oef.schema import Description as OEFDescription, DataModel as OEFDataModel, AttributeSchema as OEFAttribute

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Channel, Connection
from aea.mail.base import MailBox, Envelope
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, Attribute, DataModel, Query, ConstraintExpr, And, Or, Not, Constraint, \
    ConstraintType, ConstraintTypes
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF

logger = logging.getLogger(__name__)


STUB_MESSSAGE_ID = 0
STUB_DIALOGUE_ID = 0


class OEFObjectTranslator:
    """Translate our OEF object to object of OEF SDK classes."""

    @classmethod
    def to_oef_description(cls, desc: Description) -> OEFDescription:
        """From our description to OEF description."""
        oef_data_model = cls.to_oef_data_model(desc.data_model) if desc.data_model is not None else None
        return OEFDescription(desc.values, oef_data_model)

    @classmethod
    def to_oef_data_model(cls, data_model: DataModel) -> OEFDataModel:
        """From our data model to OEF data model."""
        oef_attributes = [cls.to_oef_attribute(attribute) for attribute in data_model.attributes]
        return OEFDataModel(data_model.name, oef_attributes, data_model.description)

    @classmethod
    def to_oef_attribute(cls, attribute: Attribute) -> OEFAttribute:
        """From our attribute to OEF attribute."""
        return OEFAttribute(attribute.name, attribute.type, attribute.is_required, attribute.description)

    @classmethod
    def to_oef_query(cls, query: Query) -> OEFQuery:
        """From our query to OEF query."""
        oef_data_model = cls.to_oef_data_model(query.model) if query.model is not None else None
        constraints = [cls.to_oef_constraint_expr(c) for c in query.constraints]
        return OEFQuery(constraints, oef_data_model)

    @classmethod
    def to_oef_constraint_expr(cls, constraint_expr: ConstraintExpr) -> OEFConstraintExpr:
        """From our constraint expression to the OEF constraint expression."""
        if isinstance(constraint_expr, And):
            return OEFAnd([cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints])
        elif isinstance(constraint_expr, Or):
            return OEFOr([cls.to_oef_constraint_expr(c) for c in constraint_expr.constraints])
        elif isinstance(constraint_expr, Not):
            return OEFNot(cls.to_oef_constraint_expr(constraint_expr.constraint))
        elif isinstance(constraint_expr, Constraint):
            oef_constraint_type = cls.to_oef_constraint_type(constraint_expr.constraint_type)
            return OEFConstraint(constraint_expr.attribute_name, oef_constraint_type)
        else:
            raise ValueError("Constraint expression not supported.")

    @classmethod
    def to_oef_constraint_type(cls, constraint_type: ConstraintType) -> OEFConstraintType:
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
        data_model = cls.from_oef_data_model(oef_desc.data_model) if oef_desc.data_model is not None else None
        return Description(oef_desc.values, data_model=data_model)

    @classmethod
    def from_oef_data_model(cls, oef_data_model: OEFDataModel) -> DataModel:
        """From an OEF data model to our data model."""
        attributes = [cls.from_oef_attribute(oef_attribute) for oef_attribute in oef_data_model.attribute_schemas]
        return DataModel(oef_data_model.name, attributes, oef_data_model.description)

    @classmethod
    def from_oef_attribute(cls, oef_attribute: OEFAttribute) -> Attribute:
        """From an OEF attribute to our attribute."""
        return Attribute(oef_attribute.name, oef_attribute.type, oef_attribute.required, oef_attribute.description)

    @classmethod
    def from_oef_query(cls, oef_query: OEFQuery) -> Query:
        """From our query to OrOEF query."""
        data_model = cls.from_oef_data_model(oef_query.model) if oef_query.model is not None else None
        constraints = [cls.from_oef_constraint_expr(c) for c in oef_query.constraints]
        return Query(constraints, data_model)

    @classmethod
    def from_oef_constraint_expr(cls, oef_constraint_expr: OEFConstraintExpr) -> ConstraintExpr:
        """From our query to OEF query."""
        if isinstance(oef_constraint_expr, OEFAnd):
            return And([cls.from_oef_constraint_expr(c) for c in oef_constraint_expr.constraints])
        elif isinstance(oef_constraint_expr, OEFOr):
            return Or([cls.from_oef_constraint_expr(c) for c in oef_constraint_expr.constraints])
        elif isinstance(oef_constraint_expr, OEFNot):
            return Not(cls.from_oef_constraint_expr(oef_constraint_expr.constraint))
        elif isinstance(oef_constraint_expr, OEFConstraint):
            constraint_type = cls.from_oef_constraint_type(oef_constraint_expr.constraint)
            return Constraint(oef_constraint_expr.attribute_name, constraint_type)
        else:
            raise ValueError("OEF Constraint not supported.")

    @classmethod
    def from_oef_constraint_type(cls, constraint_type: OEFConstraintType) -> ConstraintType:
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
            return ConstraintType(ConstraintTypes.GREATER_THAN_EQ, constraint_type.value)
        elif isinstance(constraint_type, Range):
            return ConstraintType(ConstraintTypes.WITHIN, constraint_type.values)
        elif isinstance(constraint_type, In):
            return ConstraintType(ConstraintTypes.IN, constraint_type.values)
        elif isinstance(constraint_type, NotIn):
            return ConstraintType(ConstraintTypes.NOT_IN, constraint_type.values)
        else:
            raise ValueError("Constraint type not recognized.")


class MailStats(object):
    """The MailStats class tracks statistics on messages processed by MailBox."""

    def __init__(self) -> None:
        """
        Instantiate mail stats.

        :return: None
        """
        self._search_count = 0
        self._search_start_time = {}  # type: Dict[int, datetime.datetime]
        self._search_timedelta = {}  # type: Dict[int, float]
        self._search_result_counts = {}  # type: Dict[int, int]

    @property
    def search_count(self) -> int:
        """Get the search count."""
        return self._search_count

    def search_start(self, search_id: int) -> None:
        """
        Add a search id and start time.

        :param search_id: the search id

        :return: None
        """
        assert search_id not in self._search_start_time
        self._search_count += 1
        self._search_start_time[search_id] = datetime.datetime.now()

    def search_end(self, search_id: int, nb_search_results: int) -> None:
        """
        Add end time for a search id.

        :param search_id: the search id
        :param nb_search_results: the number of agents returned in the search result

        :return: None
        """
        assert search_id in self._search_start_time
        assert search_id not in self._search_timedelta
        self._search_timedelta[search_id] = (datetime.datetime.now() - self._search_start_time[search_id]).total_seconds() * 1000
        self._search_result_counts[search_id] = nb_search_results


class OEFChannel(OEFAgent, Channel):
    """The OEFChannel connects the OEF Agent with the connection."""

    def __init__(self, public_key: str, oef_addr: str, oef_port: int, core: AsyncioCore, in_queue: Queue):
        """
        Initialize.

        :param public_key: the public key of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        :param in_queue: the in queue.
        """
        super().__init__(public_key, oef_addr=oef_addr, oef_port=oef_port, core=core,
                         logger=lambda *x: None, logger_debug=lambda *x: None)
        self.in_queue = in_queue
        self.mail_stats = MailStats()

    def on_message(self, msg_id: int, dialogue_id: int, origin: str, content: bytes) -> None:
        """
        On message event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the public key of the sender.
        :param content: the bytes content.
        :return: None
        """
        # We are not using the 'origin' parameter because 'content' contains a serialized instance of 'Envelope',
        # hence it already contains the address of the sender.
        envelope = Envelope.decode(content)
        self.in_queue.put(envelope)

    def on_cfp(self, msg_id: int, dialogue_id: int, origin: str, target: int, query: CFP_TYPES) -> None:
        """
        On cfp event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the public key of the sender.
        :param target: the message target.
        :param query: the query.
        :return: None
        """
        try:
            query = pickle.loads(query)
        except Exception:
            pass
        msg = FIPAMessage(message_id=msg_id,
                          dialogue_id=dialogue_id,
                          target=target,
                          performative=FIPAMessage.Performative.CFP,
                          query=query if query != b"" else None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=origin, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_propose(self, msg_id: int, dialogue_id: int, origin: str, target: int, b_proposals: PROPOSE_TYPES) -> None:
        """
        On propose event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the public key of the sender.
        :param target: the message target.
        :param b_proposals: the proposals.
        :return: None
        """
        if type(b_proposals) == bytes:
            proposals = pickle.loads(b_proposals)  # type: List[Description]
        else:
            raise ValueError("No support for non-bytes proposals.")

        msg = FIPAMessage(message_id=msg_id,
                          dialogue_id=dialogue_id,
                          target=target,
                          performative=FIPAMessage.Performative.PROPOSE,
                          proposal=proposals)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=origin, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_accept(self, msg_id: int, dialogue_id: int, origin: str, target: int) -> None:
        """
        On accept event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the public key of the sender.
        :param target: the message target.
        :return: None
        """
        performative = FIPAMessage.Performative.MATCH_ACCEPT if msg_id == 4 and target == 3 else FIPAMessage.Performative.ACCEPT
        msg = FIPAMessage(message_id=msg_id,
                          dialogue_id=dialogue_id,
                          target=target,
                          performative=performative)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=origin, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_decline(self, msg_id: int, dialogue_id: int, origin: str, target: int) -> None:
        """
        On decline event handler.

        :param msg_id: the message id.
        :param dialogue_id: the dialogue id.
        :param origin: the public key of the sender.
        :param target: the message target.
        :return: None
        """
        msg = FIPAMessage(message_id=msg_id,
                          dialogue_id=dialogue_id,
                          target=target,
                          performative=FIPAMessage.Performative.DECLINE)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=origin, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_search_result(self, search_id: int, agents: List[str]) -> None:
        """
        On accept event handler.

        :param search_id: the search id.
        :param agents: the list of agents.
        :return: None
        """
        self.mail_stats.search_end(search_id, len(agents))
        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_RESULT, id=search_id, agents=agents)
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_oef_error(self, answer_id: int, operation: oef.messages.OEFErrorOperation) -> None:
        """
        On oef error event handler.

        :param answer_id: the answer id.
        :param operation: the error operation.
        :return: None
        """
        try:
            operation = OEFMessage.OEFErrorOperation(operation)
        except ValueError:
            operation = OEFMessage.OEFErrorOperation.OTHER

        msg = OEFMessage(oef_type=OEFMessage.Type.OEF_ERROR, id=answer_id, operation=operation)
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def on_dialogue_error(self, answer_id: int, dialogue_id: int, origin: str) -> None:
        """
        On dialogue error event handler.

        :param answer_id: the answer id.
        :param dialogue_id: the dialogue id.
        :param origin: the message sender.
        :return: None
        """
        msg = OEFMessage(oef_type=OEFMessage.Type.DIALOGUE_ERROR,
                         id=answer_id,
                         dialogue_id=dialogue_id,
                         origin=origin)
        msg_bytes = OEFSerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=DEFAULT_OEF, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        self.in_queue.put(envelope)

    def send(self, envelope: Envelope) -> None:
        """
        Send message handler.

        :param envelope: the message.
        :return: None
        """
        if envelope.protocol_id == "default":
            self.send_default_message(envelope)
        elif envelope.protocol_id == "fipa":
            self.send_fipa_message(envelope)
        elif envelope.protocol_id == "oef":
            self.send_oef_message(envelope)
        elif envelope.protocol_id == "tac":
            self.send_default_message(envelope)
        else:
            logger.error("This envelope cannot be sent: protocol_id={}".format(envelope.protocol_id))
            raise ValueError("Cannot send message.")

    def send_default_message(self, envelope: Envelope):
        """Send a 'default' message."""
        self.send_message(STUB_MESSSAGE_ID, STUB_DIALOGUE_ID, envelope.to, envelope.encode())

    def send_fipa_message(self, envelope: Envelope) -> None:
        """
        Send fipa message handler.

        :param envelope: the message.
        :return: None
        """
        fipa_message = FIPASerializer().decode(envelope.message)
        id = fipa_message.get("message_id")
        dialogue_id = fipa_message.get("dialogue_id")
        destination = envelope.to
        target = fipa_message.get("target")
        performative = FIPAMessage.Performative(fipa_message.get("performative"))
        if performative == FIPAMessage.Performative.CFP:
            query = fipa_message.get("query")
            query = b"" if query is None else query
            if type(query) == Query:
                query = pickle.dumps(query)
            self.send_cfp(id, dialogue_id, destination, target, query)
        elif performative == FIPAMessage.Performative.PROPOSE:
            proposal = cast(List[Description], fipa_message.get("proposal"))
            proposal_b = pickle.dumps(proposal)  # type: bytes
            self.send_propose(id, dialogue_id, destination, target, proposal_b)
        elif performative == FIPAMessage.Performative.ACCEPT:
            self.send_accept(id, dialogue_id, destination, target)
        elif performative == FIPAMessage.Performative.MATCH_ACCEPT:
            self.send_accept(id, dialogue_id, destination, target)
        elif performative == FIPAMessage.Performative.DECLINE:
            self.send_decline(id, dialogue_id, destination, target)
        elif performative == FIPAMessage.Performative.MATCH_ACCEPT_W_ADDRESS or \
                performative == FIPAMessage.Performative.ACCEPT_W_ADDRESS or \
                performative == FIPAMessage.Performative.INFORM:
            self.send_default_message(envelope)
        else:
            raise ValueError("OEF FIPA message not recognized.")  # pragma: no cover

    def send_oef_message(self, envelope: Envelope) -> None:
        """
        Send oef message handler.

        :param envelope: the message.
        :return: None
        """
        oef_message = OEFSerializer().decode(envelope.message)
        oef_type = OEFMessage.Type(oef_message.get("type"))
        oef_msg_id = cast(int, oef_message.get("id"))
        if oef_type == OEFMessage.Type.REGISTER_SERVICE:
            service_description = cast(Description, oef_message.get("service_description"))
            service_id = cast(int, oef_message.get("service_id"))
            oef_service_description = OEFObjectTranslator.to_oef_description(service_description)
            self.register_service(oef_msg_id, oef_service_description, service_id)
        elif oef_type == OEFMessage.Type.UNREGISTER_SERVICE:
            service_description = cast(Description, oef_message.get("service_description"))
            service_id = cast(int, oef_message.get("service_id"))
            oef_service_description = OEFObjectTranslator.to_oef_description(service_description)
            self.unregister_service(oef_msg_id, oef_service_description, service_id)
        elif oef_type == OEFMessage.Type.SEARCH_AGENTS:
            query = cast(Query, oef_message.get("query"))
            oef_query = OEFObjectTranslator.to_oef_query(query)
            self.search_agents(oef_msg_id, oef_query)
        elif oef_type == OEFMessage.Type.SEARCH_SERVICES:
            query = cast(Query, oef_message.get("query"))
            oef_query = OEFObjectTranslator.to_oef_query(query)
            self.mail_stats.search_start(oef_msg_id)
            self.search_services(oef_msg_id, oef_query)
        else:
            raise ValueError("OEF request not recognized.")


class OEFConnection(Connection):
    """The OEFConnection connects the to the mailbox."""

    def __init__(self, public_key: str, oef_addr: str, oef_port: int = 10000):
        """
        Initialize.

        :param public_key: the public key of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        """
        super().__init__()
        core = AsyncioCore(logger=logger)
        self._core = core  # type: AsyncioCore
        self.channel = OEFChannel(public_key, oef_addr, oef_port, core=core, in_queue=self.in_queue)

        self._stopped = True
        self._connected = False
        self.out_thread = None  # type: Optional[Thread]

    @property
    def is_established(self) -> bool:
        """Get the connection status."""
        return self._connected

    def _fetch(self) -> None:
        """
        Fetch the messages from the outqueue and send them.

        :return: None
        """
        while self._connected:
            try:
                msg = self.out_queue.get(block=True, timeout=1.0)
                self.send(msg)
            except Empty:
                pass

    def connect(self) -> None:
        """
        Connect to the channel.

        :return: None
        :raises ConnectionError if the connection to the OEF fails.
        """
        if self._stopped and not self._connected:
            self._stopped = False
            self._core.run_threaded()
            try:
                if not self.channel.connect():
                    raise ConnectionError("Cannot connect to OEFChannel.")
                self._connected = True
                self.out_thread = Thread(target=self._fetch)
                self.out_thread.start()
            except ConnectionError as e:
                self._core.stop()
                raise e

    def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert self.out_thread is not None, "Call connect before disconnect."
        if not self._stopped and self._connected:
            self._connected = False
            self.out_thread.join()
            self.out_thread = None
            self.channel.disconnect()
            self._core.stop()
            self._stopped = True

    def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        if self._connected:
            self.channel.send(envelope)

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        oef_addr = cast(str, connection_configuration.config.get("addr"))
        oef_port = cast(int, connection_configuration.config.get("port"))
        return OEFConnection(public_key, oef_addr, oef_port)


class OEFMailBox(MailBox):
    """The OEF mail box."""

    def __init__(self, public_key: str, oef_addr: str, oef_port: int = 10000):
        """
        Initialize.

        :param public_key: the public key of the agent.
        :param oef_addr: the OEF IP address.
        :param oef_port: the OEF port.
        """
        connection = OEFConnection(public_key, oef_addr, oef_port)
        super().__init__(connection)

    @property
    def mail_stats(self) -> MailStats:
        """Get the mail stats object."""
        return self._connection.channel.mail_stats  # type: ignore
