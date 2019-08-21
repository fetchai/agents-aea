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

"""Serialization for the FIPA protocol."""
import copy
import json
import pickle
from typing import Dict

import base58
from google.protobuf import json_format
from google.protobuf.json_format import MessageToJson
from oef import query_pb2, dap_interface_pb2
from oef.messages import OEFErrorOperation
from oef.query import Query, ConstraintExpr, And, Or, Not, Constraint
from oef.schema import Description, DataModel

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer
from aea.protocols.oef.message import OEFMessage

"""default 'to' field for OEF envelopes."""
DEFAULT_OEF = "oef"


class ConstraintWrapper:
    """Make the constraint object pickable."""

    def __init__(self, c: ConstraintExpr):
        """Wrap the constraint object."""
        self.c = c

    def to_json(self) -> Dict:
        """
        Convert to json.

        :return: the dictionary
        """
        result = {}
        if isinstance(self.c, And) or isinstance(self.c, Or):
            wraps = [ConstraintWrapper(subc).to_json() for subc in self.c.constraints]
            key = "and" if isinstance(self.c, And) else "or" if isinstance(self.c, Or) else ""
            result[key] = wraps
        elif isinstance(self.c, Not):
            wrap = ConstraintWrapper(self.c.constraint).to_json()
            result["not"] = wrap
        elif isinstance(self.c, Constraint):
            result["attribute_name"] = self.c.attribute_name
            result["constraint_type"] = base58.b58encode(pickle.dumps(self.c.constraint)).decode("utf-8")
        else:
            raise ValueError("ConstraintExpr not recognized.")

        return result

    @classmethod
    def from_json(cls, d: Dict) -> Constraint:
        """
        Convert from json.

        :param d: the dictionary.
        :return: the constraint
        """
        if "and" in d:
            return And([ConstraintWrapper.from_json(subc) for subc in d["and"]])
        elif "or" in d:
            return Or([ConstraintWrapper.from_json(subc) for subc in d["or"]])
        elif "not" in d:
            return Not(ConstraintWrapper.from_json(d["not"]))
        else:
            constraint_type = pickle.loads(base58.b58decode(d["constraint_type"]))
            return Constraint(d["attribute_name"], constraint_type)


class QueryWrapper:
    """Make the query object pickable."""

    def __init__(self, q: Query):
        """
        Initialize.

        :param q: the query
        """
        self.q = q

    def to_json(self) -> Dict:
        """
        Convert to json.

        :return: the dictionary
        """
        result = {}
        if self.q.model:
            result["data_model"] = base58.b58encode(self.q.model.to_pb().SerializeToString()).decode("utf-8")
        else:
            result["data_model"] = None
        result["constraints"] = [ConstraintWrapper(c).to_json() for c in self.q.constraints]
        return result

    @classmethod
    def from_json(self, d: Dict) -> Query:
        """
        Convert from json.

        :param d: the dictionary.
        :return: the query
        """
        if d["data_model"]:
            data_model_pb = dap_interface_pb2.ValueMessage.DataModel()
            data_model_pb.ParseFromString(base58.b58decode(d["data_model"]))
            data_model = DataModel.from_pb(data_model_pb)
        else:
            data_model = None

        constraints = [ConstraintWrapper.from_json(c) for c in d["constraints"]]
        return Query(constraints, data_model)


class OEFSerializer(Serializer):
    """Serialization for the OEF protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Decode the message.

        :param msg: the message object
        :return: the bytes
        """
        oef_type = OEFMessage.Type(msg.get("type"))
        new_body = copy.copy(msg.body)

        if oef_type in {OEFMessage.Type.REGISTER_SERVICE, OEFMessage.Type.UNREGISTER_SERVICE}:
            service_description = msg.body["service_description"]  # type: Description
            service_description_pb = service_description.to_pb()
            service_description_json = MessageToJson(service_description_pb)
            new_body["service_description"] = service_description_json
        elif oef_type in {OEFMessage.Type.REGISTER_AGENT}:
            agent_description = msg.body["agent_description"]  # type: Description
            agent_description_pb = agent_description.to_pb()
            agent_description_json = MessageToJson(agent_description_pb)
            new_body["agent_description"] = agent_description_json
        elif oef_type in {OEFMessage.Type.SEARCH_SERVICES, OEFMessage.Type.SEARCH_AGENTS}:
            query = msg.body["query"]  # type: Query
            new_body["query"] = QueryWrapper(query).to_json()
        elif oef_type in {OEFMessage.Type.SEARCH_RESULT}:
            # we need this cast because the "agents" field might contains
            # the Protobuf type "RepeatedScalarContainer", which is not JSON serializable.
            new_body["agents"] = list(msg.body["agents"])
        elif oef_type in {OEFMessage.Type.OEF_ERROR}:
            operation = msg.body["operation"]
            new_body["operation"] = str(operation)

        oef_message_bytes = json.dumps(new_body).encode("utf-8")
        return oef_message_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode the message.

        :param obj: the bytes object
        :return: the message
        """
        json_msg = json.loads(obj.decode("utf-8"))
        oef_type = OEFMessage.Type(json_msg["type"])
        new_body = copy.copy(json_msg)
        new_body["type"] = oef_type

        if oef_type in {OEFMessage.Type.REGISTER_SERVICE, OEFMessage.Type.UNREGISTER_SERVICE}:
            service_description_json = json_msg["service_description"]
            service_description_pb = json_format.Parse(service_description_json, query_pb2.Query.Instance())
            service_description = Description.from_pb(service_description_pb)
            new_body["service_description"] = service_description
        elif oef_type in {OEFMessage.Type.REGISTER_AGENT}:
            agent_description_json = json_msg["agent_description"]
            agent_description_pb = json_format.Parse(agent_description_json, query_pb2.Query.Instance())
            agent_description = Description.from_pb(agent_description_pb)
            new_body["agent_description"] = agent_description
        elif oef_type in {OEFMessage.Type.SEARCH_SERVICES, OEFMessage.Type.SEARCH_AGENTS}:
            query = QueryWrapper.from_json(json_msg["query"])
            new_body["query"] = query
        elif oef_type in {OEFMessage.Type.SEARCH_RESULT}:
            new_body["agents"] = list(json_msg["agents"])
        elif oef_type in {OEFMessage.Type.OEF_ERROR}:
            operation = json_msg["operation"]
            new_body["operation"] = OEFErrorOperation(operation)

        oef_message = Message(body=new_body)
        return oef_message
