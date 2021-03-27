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

"""Serialization module for yoti protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.yoti import yoti_pb2
from packages.fetchai.protocols.yoti.message import YotiMessage


class YotiSerializer(Serializer):
    """Serialization for the 'yoti' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Yoti' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(YotiMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        yoti_msg = yoti_pb2.YotiMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == YotiMessage.Performative.GET_PROFILE:
            performative = yoti_pb2.YotiMessage.Get_Profile_Performative()  # type: ignore
            token = msg.token
            performative.token = token
            dotted_path = msg.dotted_path
            performative.dotted_path = dotted_path
            args = msg.args
            performative.args.extend(args)
            yoti_msg.get_profile.CopyFrom(performative)
        elif performative_id == YotiMessage.Performative.PROFILE:
            performative = yoti_pb2.YotiMessage.Profile_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            yoti_msg.profile.CopyFrom(performative)
        elif performative_id == YotiMessage.Performative.ERROR:
            performative = yoti_pb2.YotiMessage.Error_Performative()  # type: ignore
            error_code = msg.error_code
            performative.error_code = error_code
            error_msg = msg.error_msg
            performative.error_msg = error_msg
            yoti_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = yoti_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Yoti' message.

        :param obj: the bytes object.
        :return: the 'Yoti' message.
        """
        message_pb = ProtobufMessage()
        yoti_pb = yoti_pb2.YotiMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        yoti_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = yoti_pb.WhichOneof("performative")
        performative_id = YotiMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == YotiMessage.Performative.GET_PROFILE:
            token = yoti_pb.get_profile.token
            performative_content["token"] = token
            dotted_path = yoti_pb.get_profile.dotted_path
            performative_content["dotted_path"] = dotted_path
            args = yoti_pb.get_profile.args
            args_tuple = tuple(args)
            performative_content["args"] = args_tuple
        elif performative_id == YotiMessage.Performative.PROFILE:
            info = yoti_pb.profile.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == YotiMessage.Performative.ERROR:
            error_code = yoti_pb.error.error_code
            performative_content["error_code"] = error_code
            error_msg = yoti_pb.error.error_msg
            performative_content["error_msg"] = error_msg
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return YotiMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
