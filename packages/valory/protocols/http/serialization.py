# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 valory
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

"""Serialization module for http protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.valory.protocols.http import http_pb2
from packages.valory.protocols.http.message import HttpMessage


class HttpSerializer(Serializer):
    """Serialization for the 'http' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Http' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(HttpMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        http_msg = http_pb2.HttpMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == HttpMessage.Performative.REQUEST:
            performative = http_pb2.HttpMessage.Request_Performative()  # type: ignore
            method = msg.method
            performative.method = method
            url = msg.url
            performative.url = url
            version = msg.version
            performative.version = version
            headers = msg.headers
            performative.headers = headers
            body = msg.body
            performative.body = body
            http_msg.request.CopyFrom(performative)
        elif performative_id == HttpMessage.Performative.RESPONSE:
            performative = http_pb2.HttpMessage.Response_Performative()  # type: ignore
            version = msg.version
            performative.version = version
            status_code = msg.status_code
            performative.status_code = status_code
            status_text = msg.status_text
            performative.status_text = status_text
            headers = msg.headers
            performative.headers = headers
            body = msg.body
            performative.body = body
            http_msg.response.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = http_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Http' message.

        :param obj: the bytes object.
        :return: the 'Http' message.
        """
        message_pb = ProtobufMessage()
        http_pb = http_pb2.HttpMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        http_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = http_pb.WhichOneof("performative")
        performative_id = HttpMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == HttpMessage.Performative.REQUEST:
            method = http_pb.request.method
            performative_content["method"] = method
            url = http_pb.request.url
            performative_content["url"] = url
            version = http_pb.request.version
            performative_content["version"] = version
            headers = http_pb.request.headers
            performative_content["headers"] = headers
            body = http_pb.request.body
            performative_content["body"] = body
        elif performative_id == HttpMessage.Performative.RESPONSE:
            version = http_pb.response.version
            performative_content["version"] = version
            status_code = http_pb.response.status_code
            performative_content["status_code"] = status_code
            status_text = http_pb.response.status_text
            performative_content["status_text"] = status_text
            headers = http_pb.response.headers
            performative_content["headers"] = headers
            body = http_pb.response.body
            performative_content["body"] = body
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return HttpMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
