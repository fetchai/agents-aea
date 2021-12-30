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

"""Serialization module for default protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.default import default_pb2
from packages.fetchai.protocols.default.custom_types import ErrorCode
from packages.fetchai.protocols.default.message import DefaultMessage


class DefaultSerializer(Serializer):
    """Serialization for the 'default' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Default' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(DefaultMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        default_msg = default_pb2.DefaultMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == DefaultMessage.Performative.BYTES:
            performative = default_pb2.DefaultMessage.Bytes_Performative()  # type: ignore
            content = msg.content
            performative.content = content
            default_msg.bytes.CopyFrom(performative)
        elif performative_id == DefaultMessage.Performative.ERROR:
            performative = default_pb2.DefaultMessage.Error_Performative()  # type: ignore
            error_code = msg.error_code
            ErrorCode.encode(performative.error_code, error_code)
            error_msg = msg.error_msg
            performative.error_msg = error_msg
            error_data = msg.error_data
            performative.error_data.update(error_data)
            default_msg.error.CopyFrom(performative)
        elif performative_id == DefaultMessage.Performative.END:
            performative = default_pb2.DefaultMessage.End_Performative()  # type: ignore
            default_msg.end.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = default_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Default' message.

        :param obj: the bytes object.
        :return: the 'Default' message.
        """
        message_pb = ProtobufMessage()
        default_pb = default_pb2.DefaultMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        default_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = default_pb.WhichOneof("performative")
        performative_id = DefaultMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == DefaultMessage.Performative.BYTES:
            content = default_pb.bytes.content
            performative_content["content"] = content
        elif performative_id == DefaultMessage.Performative.ERROR:
            pb2_error_code = default_pb.error.error_code
            error_code = ErrorCode.decode(pb2_error_code)
            performative_content["error_code"] = error_code
            error_msg = default_pb.error.error_msg
            performative_content["error_msg"] = error_msg
            error_data = default_pb.error.error_data
            error_data_dict = dict(error_data)
            performative_content["error_data"] = error_data_dict
        elif performative_id == DefaultMessage.Performative.END:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return DefaultMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
