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

"""Serialization module for register protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.register import register_pb2
from packages.fetchai.protocols.register.message import RegisterMessage


class RegisterSerializer(Serializer):
    """Serialization for the 'register' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Register' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(RegisterMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        register_msg = register_pb2.RegisterMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == RegisterMessage.Performative.REGISTER:
            performative = register_pb2.RegisterMessage.Register_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            register_msg.register.CopyFrom(performative)
        elif performative_id == RegisterMessage.Performative.SUCCESS:
            performative = register_pb2.RegisterMessage.Success_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            register_msg.success.CopyFrom(performative)
        elif performative_id == RegisterMessage.Performative.ERROR:
            performative = register_pb2.RegisterMessage.Error_Performative()  # type: ignore
            error_code = msg.error_code
            performative.error_code = error_code
            error_msg = msg.error_msg
            performative.error_msg = error_msg
            info = msg.info
            performative.info.update(info)
            register_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = register_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Register' message.

        :param obj: the bytes object.
        :return: the 'Register' message.
        """
        message_pb = ProtobufMessage()
        register_pb = register_pb2.RegisterMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        register_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = register_pb.WhichOneof("performative")
        performative_id = RegisterMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == RegisterMessage.Performative.REGISTER:
            info = register_pb.register.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == RegisterMessage.Performative.SUCCESS:
            info = register_pb.success.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == RegisterMessage.Performative.ERROR:
            error_code = register_pb.error.error_code
            performative_content["error_code"] = error_code
            error_msg = register_pb.error.error_msg
            performative_content["error_msg"] = error_msg
            info = register_pb.error.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return RegisterMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
