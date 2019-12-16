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

"""Serialization module for the default protocol."""
import base64
import json
from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.default.message import DefaultMessage


class DefaultSerializer(Serializer):
    """Serialization for the 'default' protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'default' message into bytes."""
        msg = cast(DefaultMessage, msg)
        body = {}  # Dict[str, Any]
        body["type"] = msg.type.value

        if msg.type == DefaultMessage.Type.BYTES:
            body["content"] = base64.b64encode(msg.content).decode("utf-8")
        elif msg.type == DefaultMessage.Type.ERROR:
            body["error_code"] = msg.error_code.value
            body["error_msg"] = msg.error_msg
            body["error_data"] = msg.error_data
        else:
            raise ValueError("Type not recognized.")

        bytes_msg = json.dumps(body).encode("utf-8")
        return bytes_msg

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a 'default' message."""
        json_body = json.loads(obj.decode("utf-8"))
        body = {}

        msg_type = DefaultMessage.Type(json_body["type"])
        body["type"] = msg_type
        if msg_type == DefaultMessage.Type.BYTES:
            content = base64.b64decode(json_body["content"].encode("utf-8"))
            body["content"] = content  # type: ignore
        elif msg_type == DefaultMessage.Type.ERROR:
            body["error_code"] = json_body["error_code"]
            body["error_msg"] = json_body["error_msg"]
            body["error_data"] = json_body["error_data"]
        else:
            raise ValueError("Type not recognized.")

        return DefaultMessage(type=msg_type, body=body)
