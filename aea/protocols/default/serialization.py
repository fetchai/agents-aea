# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.default import default_pb2
from aea.protocols.default.custom_types import ErrorCode
from aea.protocols.default.message import DefaultMessage


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
        default_msg = default_pb2.DefaultMessage()
        default_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        default_msg.dialogue_starter_reference = dialogue_reference[0]
        default_msg.dialogue_responder_reference = dialogue_reference[1]
        default_msg.target = msg.target

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
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        default_bytes = default_msg.SerializeToString()
        return default_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Default' message.

        :param obj: the bytes object.
        :return: the 'Default' message.
        """
        default_pb = default_pb2.DefaultMessage()
        default_pb.ParseFromString(obj)
        message_id = default_pb.message_id
        dialogue_reference = (
            default_pb.dialogue_starter_reference,
            default_pb.dialogue_responder_reference,
        )
        target = default_pb.target

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
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return DefaultMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
