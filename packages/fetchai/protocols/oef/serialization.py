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
import pickle  # nosec
from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.oef.message import OEFMessage

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
        msg = cast(OEFMessage, msg)
        new_body = copy.copy(msg.body)
        new_body["type"] = msg.type.value
        new_body["id"] = msg.id

        if msg.type in {
            OEFMessage.Type.REGISTER_SERVICE,
            OEFMessage.Type.UNREGISTER_SERVICE,
        }:
            service_description = msg.service_description
            service_description_bytes = base64.b64encode(
                pickle.dumps(service_description)  # nosec
            ).decode("utf-8")
            new_body["service_description"] = service_description_bytes
        elif msg.type in {
            OEFMessage.Type.SEARCH_SERVICES
        }:
            query = msg.query
            query_bytes = base64.b64encode(pickle.dumps(query)).decode("utf-8")  # nosec
            new_body["query"] = query_bytes
        elif msg.type in {OEFMessage.Type.SEARCH_RESULT}:
            # we need this cast because the "agents" field might contains
            # the Protobuf type "RepeatedScalarContainer", which is not JSON serializable.
            new_body["agents"] = msg.agents
        elif msg.type in {OEFMessage.Type.OEF_ERROR}:
            new_body["operation"] = msg.operation.value

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
        oef_id = json_msg["id"]
        new_body = copy.copy(json_msg)

        if oef_type in {
            OEFMessage.Type.REGISTER_SERVICE,
            OEFMessage.Type.UNREGISTER_SERVICE,
        }:
            service_description_bytes = base64.b64decode(
                json_msg["service_description"]
            )
            service_description = pickle.loads(service_description_bytes)  # nosec
            new_body["service_description"] = service_description
        elif oef_type in {
            OEFMessage.Type.SEARCH_SERVICES,
        }:
            query_bytes = base64.b64decode(json_msg["query"])
            query = pickle.loads(query_bytes)  # nosec
            new_body["query"] = query
        elif oef_type in {OEFMessage.Type.SEARCH_RESULT}:
            new_body["agents"] = list(json_msg["agents"])
        elif oef_type in {OEFMessage.Type.OEF_ERROR}:
            operation = json_msg["operation"]
            new_body["operation"] = OEFMessage.OEFErrorOperation(int(operation))

        oef_message = OEFMessage(type=oef_type, id=oef_id, body=new_body)
        return oef_message
