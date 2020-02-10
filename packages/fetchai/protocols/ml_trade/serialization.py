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
from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.ml_trade.message import MLTradeMessage


class MLTradeSerializer(Serializer):
    """Serialization for the ML Trade protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'ml_trade' message into bytes."""
        body = {}  # Dict[str, Any]
        msg = cast(MLTradeMessage, msg)
        body["performative"] = msg.performative.value

        if msg.performative == MLTradeMessage.Performative.CFT:
            query = msg.query
            query_bytes = base64.b64encode(pickle.dumps(query)).decode("utf-8")
            body["query"] = query_bytes
        elif msg.performative == MLTradeMessage.Performative.TERMS:
            terms = msg.terms
            terms_bytes = base64.b64encode(pickle.dumps(terms)).decode("utf-8")
            body["terms"] = terms_bytes
        elif msg.performative == MLTradeMessage.Performative.ACCEPT:
            # encoding terms
            terms = msg.terms
            terms_bytes = base64.b64encode(pickle.dumps(terms)).decode("utf-8")
            body["terms"] = terms_bytes
            # encoding tx_digest
            body["tx_digest"] = msg.tx_digest
        elif msg.performative == MLTradeMessage.Performative.DATA:
            # encoding terms
            terms = msg.terms
            terms_bytes = base64.b64encode(pickle.dumps(terms)).decode("utf-8")
            body["terms"] = terms_bytes
            # encoding data
            data = msg.data
            data_bytes = base64.b64encode(pickle.dumps(data)).decode("utf-8")
            body["data"] = data_bytes
        else:  # pragma: no cover
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
            terms_bytes = base64.b64decode(json_body["terms"])
            terms = pickle.loads(terms_bytes)
            body["terms"] = terms
            body["tx_digest"] = json_body["tx_digest"]
        elif msg_type == MLTradeMessage.Performative.DATA:
            # encoding terms
            terms_bytes = base64.b64decode(json_body["terms"])
            terms = pickle.loads(terms_bytes)
            body["terms"] = terms
            # encoding data
            data_bytes = base64.b64decode(json_body["data"])
            data = pickle.loads(data_bytes)
            body["data"] = data
        else:  # pragma: no cover
            raise ValueError("Type not recognized.")

        return MLTradeMessage(performative=msg_type, body=body)
