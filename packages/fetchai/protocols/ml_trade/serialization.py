# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 fetchai
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

"""Serialization module for ml_trade protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.ml_trade import ml_trade_pb2
from packages.fetchai.protocols.ml_trade.custom_types import Description, Query
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage


class MlTradeSerializer(Serializer):
    """Serialization for the 'ml_trade' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'MlTrade' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(MlTradeMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        ml_trade_msg = ml_trade_pb2.MlTradeMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == MlTradeMessage.Performative.CFP:
            performative = ml_trade_pb2.MlTradeMessage.Cfp_Performative()  # type: ignore
            query = msg.query
            Query.encode(performative.query, query)
            ml_trade_msg.cfp.CopyFrom(performative)
        elif performative_id == MlTradeMessage.Performative.TERMS:
            performative = ml_trade_pb2.MlTradeMessage.Terms_Performative()  # type: ignore
            terms = msg.terms
            Description.encode(performative.terms, terms)
            ml_trade_msg.terms.CopyFrom(performative)
        elif performative_id == MlTradeMessage.Performative.ACCEPT:
            performative = ml_trade_pb2.MlTradeMessage.Accept_Performative()  # type: ignore
            terms = msg.terms
            Description.encode(performative.terms, terms)
            tx_digest = msg.tx_digest
            performative.tx_digest = tx_digest
            ml_trade_msg.accept.CopyFrom(performative)
        elif performative_id == MlTradeMessage.Performative.DATA:
            performative = ml_trade_pb2.MlTradeMessage.Data_Performative()  # type: ignore
            terms = msg.terms
            Description.encode(performative.terms, terms)
            payload = msg.payload
            performative.payload = payload
            ml_trade_msg.data.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = ml_trade_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'MlTrade' message.

        :param obj: the bytes object.
        :return: the 'MlTrade' message.
        """
        message_pb = ProtobufMessage()
        ml_trade_pb = ml_trade_pb2.MlTradeMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        ml_trade_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = ml_trade_pb.WhichOneof("performative")
        performative_id = MlTradeMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == MlTradeMessage.Performative.CFP:
            pb2_query = ml_trade_pb.cfp.query
            query = Query.decode(pb2_query)
            performative_content["query"] = query
        elif performative_id == MlTradeMessage.Performative.TERMS:
            pb2_terms = ml_trade_pb.terms.terms
            terms = Description.decode(pb2_terms)
            performative_content["terms"] = terms
        elif performative_id == MlTradeMessage.Performative.ACCEPT:
            pb2_terms = ml_trade_pb.accept.terms
            terms = Description.decode(pb2_terms)
            performative_content["terms"] = terms
            tx_digest = ml_trade_pb.accept.tx_digest
            performative_content["tx_digest"] = tx_digest
        elif performative_id == MlTradeMessage.Performative.DATA:
            pb2_terms = ml_trade_pb.data.terms
            terms = Description.decode(pb2_terms)
            performative_content["terms"] = terms
            payload = ml_trade_pb.data.payload
            performative_content["payload"] = payload
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return MlTradeMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
