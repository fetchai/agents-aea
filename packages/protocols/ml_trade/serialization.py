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
import base64
import json
import pickle
import sys
from typing import TYPE_CHECKING

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.oef.models import Query

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.ml_trade.message import MLTradeMessage
else:
    from ml_trade_protocol.message import MLTradeMessage


class MLTradeSerializer(Serializer):
    """Serialization for the ML Trade protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'ml_trade' message into bytes."""
        body = {}  # Dict[str, Any]

        msg_type = MLTradeMessage.Performative(msg.get("performative"))
        body["performative"] = str(msg_type.value)

        if msg_type == MLTradeMessage.Performative.CFT:
            query = msg.body["query"]  # type: Query
            query_bytes = base64.b64encode(pickle.dumps(query)).decode("utf-8")
            body["query"] = query_bytes
        elif msg_type == MLTradeMessage.Performative.TERMS:
            terms = msg.body["terms"]
            terms_bytes = base64.b64encode(pickle.dumps(terms)).decode("utf-8")
            body["terms"] = terms_bytes
        elif msg_type == MLTradeMessage.Performative.ACCEPT:
            raise NotImplementedError
        else:
            raise ValueError("Type not recognized.")

        bytes_msg = json.dumps(body).encode("utf-8")
        return bytes_msg

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a 'ml_trade' message."""
        json_body = json.loads(obj.decode("utf-8"))
        body = {}

        msg_type = MLTradeMessage.Performative(json_body["performative"])
        body["performative"] = msg_type
        if msg_type == MLTradeMessage.Performative.CFT:
            query_bytes = base64.b64decode(json_body["query"])
            query = pickle.loads(query_bytes)
            body["query"] = query
        elif msg_type == MLTradeMessage.Performative.TERMS:
            terms_bytes = base64.b64decode(json_body["terms"])
            terms = pickle.loads(terms_bytes)
            body["terms"] = terms
        elif msg_type == MLTradeMessage.Performative.ACCEPT:
            raise NotImplementedError
        else:
            raise ValueError("Type not recognized.")

        return MLTradeMessage(performative=msg_type, body=body)
