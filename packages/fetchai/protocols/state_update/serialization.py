# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

"""Serialization module for state_update protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.state_update import state_update_pb2
from packages.fetchai.protocols.state_update.message import StateUpdateMessage


class StateUpdateSerializer(Serializer):
    """Serialization for the 'state_update' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'StateUpdate' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(StateUpdateMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        state_update_msg = state_update_pb2.StateUpdateMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == StateUpdateMessage.Performative.INITIALIZE:
            performative = state_update_pb2.StateUpdateMessage.Initialize_Performative()  # type: ignore
            exchange_params_by_currency_id = msg.exchange_params_by_currency_id
            performative.exchange_params_by_currency_id.update(
                exchange_params_by_currency_id
            )
            utility_params_by_good_id = msg.utility_params_by_good_id
            performative.utility_params_by_good_id.update(utility_params_by_good_id)
            amount_by_currency_id = msg.amount_by_currency_id
            performative.amount_by_currency_id.update(amount_by_currency_id)
            quantities_by_good_id = msg.quantities_by_good_id
            performative.quantities_by_good_id.update(quantities_by_good_id)
            state_update_msg.initialize.CopyFrom(performative)
        elif performative_id == StateUpdateMessage.Performative.APPLY:
            performative = state_update_pb2.StateUpdateMessage.Apply_Performative()  # type: ignore
            amount_by_currency_id = msg.amount_by_currency_id
            performative.amount_by_currency_id.update(amount_by_currency_id)
            quantities_by_good_id = msg.quantities_by_good_id
            performative.quantities_by_good_id.update(quantities_by_good_id)
            state_update_msg.apply.CopyFrom(performative)
        elif performative_id == StateUpdateMessage.Performative.END:
            performative = state_update_pb2.StateUpdateMessage.End_Performative()  # type: ignore
            state_update_msg.end.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = state_update_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'StateUpdate' message.

        :param obj: the bytes object.
        :return: the 'StateUpdate' message.
        """
        message_pb = ProtobufMessage()
        state_update_pb = state_update_pb2.StateUpdateMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        state_update_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = state_update_pb.WhichOneof("performative")
        performative_id = StateUpdateMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == StateUpdateMessage.Performative.INITIALIZE:
            exchange_params_by_currency_id = (
                state_update_pb.initialize.exchange_params_by_currency_id
            )
            exchange_params_by_currency_id_dict = dict(exchange_params_by_currency_id)
            performative_content[
                "exchange_params_by_currency_id"
            ] = exchange_params_by_currency_id_dict
            utility_params_by_good_id = (
                state_update_pb.initialize.utility_params_by_good_id
            )
            utility_params_by_good_id_dict = dict(utility_params_by_good_id)
            performative_content[
                "utility_params_by_good_id"
            ] = utility_params_by_good_id_dict
            amount_by_currency_id = state_update_pb.initialize.amount_by_currency_id
            amount_by_currency_id_dict = dict(amount_by_currency_id)
            performative_content["amount_by_currency_id"] = amount_by_currency_id_dict
            quantities_by_good_id = state_update_pb.initialize.quantities_by_good_id
            quantities_by_good_id_dict = dict(quantities_by_good_id)
            performative_content["quantities_by_good_id"] = quantities_by_good_id_dict
        elif performative_id == StateUpdateMessage.Performative.APPLY:
            amount_by_currency_id = state_update_pb.apply.amount_by_currency_id
            amount_by_currency_id_dict = dict(amount_by_currency_id)
            performative_content["amount_by_currency_id"] = amount_by_currency_id_dict
            quantities_by_good_id = state_update_pb.apply.quantities_by_good_id
            quantities_by_good_id_dict = dict(quantities_by_good_id)
            performative_content["quantities_by_good_id"] = quantities_by_good_id_dict
        elif performative_id == StateUpdateMessage.Performative.END:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return StateUpdateMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
