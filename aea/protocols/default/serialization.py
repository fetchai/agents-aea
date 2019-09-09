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
import json
from typing import cast

import base58

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer
from aea.protocols.default.message import DefaultMessage


class DefaultSerializer(Serializer):
    """Serialization for the 'default' protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'default' message into bytes."""
        body = {}  # Dict[str, Any]

        msg_type = DefaultMessage.Type(msg.get("type"))
        body["type"] = str(msg_type.value)

        if msg_type == DefaultMessage.Type.BYTES:
            body["content"] = base58.b58encode(msg.get("content")).decode("utf-8")
        elif msg_type == DefaultMessage.Type.ERROR:
            body["error_code"] = cast(str, msg.get("error_code"))
            body["error_msg"] = cast(str, msg.get("error_msg"))
            body["error_data"] = cast(str, msg.get("error_data"))
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
            content = base58.b58decode(json_body["content"].encode("utf-8"))
            body["content"] = content
        elif msg_type == DefaultMessage.Type.ERROR:
            body["error_code"] = json_body["error_code"]
            body["error_msg"] = json_body["error_msg"]
            body["error_data"] = json_body["error_data"]
        else:
            raise ValueError("Type not recognized.")

        return Message(body=body)
