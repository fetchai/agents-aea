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
import base64
import copy
import json
import pickle

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, Query

"""default 'to' field for OEF envelopes."""
DEFAULT_OEF = "oef"


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
        new_body["type"] = oef_type.value

        if oef_type in {OEFMessage.Type.REGISTER_SERVICE, OEFMessage.Type.UNREGISTER_SERVICE}:
            service_description = msg.body["service_description"]  # type: Description
            service_description_bytes = base64.b64encode(pickle.dumps(service_description)).decode("utf-8")
            new_body["service_description"] = service_description_bytes
        elif oef_type in {OEFMessage.Type.REGISTER_AGENT, OEFMessage.Type.UNREGISTER_AGENT}:
            agent_description = msg.body["agent_description"]  # type: Description
            agent_description_bytes = base64.b64encode(pickle.dumps(agent_description)).decode("utf-8")
            new_body["agent_description"] = agent_description_bytes
        elif oef_type in {OEFMessage.Type.SEARCH_SERVICES, OEFMessage.Type.SEARCH_AGENTS}:
            query = msg.body["query"]  # type: Query
            query_bytes = base64.b64encode(pickle.dumps(query)).decode("utf-8")
            new_body["query"] = query_bytes
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
            service_description_bytes = base64.b64decode(json_msg["service_description"])
            service_description = pickle.loads(service_description_bytes)
            new_body["service_description"] = service_description
        elif oef_type in {OEFMessage.Type.REGISTER_AGENT, OEFMessage.Type.UNREGISTER_AGENT}:
            agent_description_bytes = base64.b64decode(json_msg["agent_description"])
            agent_description = pickle.loads(agent_description_bytes)
            new_body["agent_description"] = agent_description
        elif oef_type in {OEFMessage.Type.SEARCH_SERVICES, OEFMessage.Type.SEARCH_AGENTS}:
            query_bytes = base64.b64decode(json_msg["query"])
            query = pickle.loads(query_bytes)
            new_body["query"] = query
        elif oef_type in {OEFMessage.Type.SEARCH_RESULT}:
            new_body["agents"] = list(json_msg["agents"])
        elif oef_type in {OEFMessage.Type.OEF_ERROR}:
            operation = json_msg["operation"]
            new_body["operation"] = OEFMessage.OEFErrorOperation(int(operation))

        oef_message = OEFMessage(oef_type=oef_type, body=new_body)
        return oef_message
