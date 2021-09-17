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

"""Serialization module for cosm_trade protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.cosm_trade import cosm_trade_pb2
from packages.fetchai.protocols.cosm_trade.custom_types import SignedTransaction
from packages.fetchai.protocols.cosm_trade.message import CosmTradeMessage


class CosmTradeSerializer(Serializer):
    """Serialization for the 'cosm_trade' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'CosmTrade' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(CosmTradeMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        cosm_trade_msg = cosm_trade_pb2.CosmTradeMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == CosmTradeMessage.Performative.INFORM_PUBLIC_KEY:
            performative = cosm_trade_pb2.CosmTradeMessage.Inform_Public_Key_Performative()  # type: ignore
            public_key = msg.public_key
            performative.public_key = public_key
            cosm_trade_msg.inform_public_key.CopyFrom(performative)
        elif performative_id == CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION:
            performative = cosm_trade_pb2.CosmTradeMessage.Inform_Signed_Transaction_Performative()  # type: ignore
            signed_transaction = msg.signed_transaction
            SignedTransaction.encode(
                performative.signed_transaction, signed_transaction
            )
            if msg.is_set("fipa_dialogue_id"):
                performative.fipa_dialogue_id_is_set = True
                fipa_dialogue_id = msg.fipa_dialogue_id
                performative.fipa_dialogue_id.extend(fipa_dialogue_id)
            cosm_trade_msg.inform_signed_transaction.CopyFrom(performative)
        elif performative_id == CosmTradeMessage.Performative.ERROR:
            performative = cosm_trade_pb2.CosmTradeMessage.Error_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            if msg.is_set("message"):
                performative.message_is_set = True
                message = msg.message
                performative.message = message
            if msg.is_set("data"):
                performative.data_is_set = True
                data = msg.data
                performative.data = data
            cosm_trade_msg.error.CopyFrom(performative)
        elif performative_id == CosmTradeMessage.Performative.END:
            performative = cosm_trade_pb2.CosmTradeMessage.End_Performative()  # type: ignore
            cosm_trade_msg.end.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = cosm_trade_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'CosmTrade' message.

        :param obj: the bytes object.
        :return: the 'CosmTrade' message.
        """
        message_pb = ProtobufMessage()
        cosm_trade_pb = cosm_trade_pb2.CosmTradeMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        cosm_trade_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = cosm_trade_pb.WhichOneof("performative")
        performative_id = CosmTradeMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == CosmTradeMessage.Performative.INFORM_PUBLIC_KEY:
            public_key = cosm_trade_pb.inform_public_key.public_key
            performative_content["public_key"] = public_key
        elif performative_id == CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION:
            pb2_signed_transaction = (
                cosm_trade_pb.inform_signed_transaction.signed_transaction
            )
            signed_transaction = SignedTransaction.decode(pb2_signed_transaction)
            performative_content["signed_transaction"] = signed_transaction
            if cosm_trade_pb.inform_signed_transaction.fipa_dialogue_id_is_set:
                fipa_dialogue_id = (
                    cosm_trade_pb.inform_signed_transaction.fipa_dialogue_id
                )
                fipa_dialogue_id_tuple = tuple(fipa_dialogue_id)
                performative_content["fipa_dialogue_id"] = fipa_dialogue_id_tuple
        elif performative_id == CosmTradeMessage.Performative.ERROR:
            code = cosm_trade_pb.error.code
            performative_content["code"] = code
            if cosm_trade_pb.error.message_is_set:
                message = cosm_trade_pb.error.message
                performative_content["message"] = message
            if cosm_trade_pb.error.data_is_set:
                data = cosm_trade_pb.error.data
                performative_content["data"] = data
        elif performative_id == CosmTradeMessage.Performative.END:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return CosmTradeMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
