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

"""Serialization for the TAC protocol."""
import copy
import json

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer
from aea.protocols.tac.message import TACMessage


class TACSerializer(Serializer):
    """Serialization for the TAC protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Decode the message.

        :param msg: the message object
        :return: the bytes
        """
        tac_type = TACMessage.Type(msg.get("type"))
        new_body = copy.copy(msg.body)

        if tac_type in {}:
            pass  # TODO

        tac_message_bytes = json.dumps(new_body).encode("utf-8")
        return tac_message_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode the message.

        :param obj: the bytes object
        :return: the message
        """
        json_msg = json.loads(obj.decode("utf-8"))
        tac_type = TACMessage.Type(json_msg["type"])
        new_body = copy.copy(json_msg)
        new_body["type"] = tac_type

        if tac_type in {}:
            pass  # TODO

        tac_message = Message(body=new_body)
        return tac_message
