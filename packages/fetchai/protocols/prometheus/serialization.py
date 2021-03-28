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

"""Serialization module for prometheus protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.prometheus import prometheus_pb2
from packages.fetchai.protocols.prometheus.message import PrometheusMessage


class PrometheusSerializer(Serializer):
    """Serialization for the 'prometheus' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Prometheus' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(PrometheusMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        prometheus_msg = prometheus_pb2.PrometheusMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == PrometheusMessage.Performative.ADD_METRIC:
            performative = prometheus_pb2.PrometheusMessage.Add_Metric_Performative()  # type: ignore
            type = msg.type
            performative.type = type
            title = msg.title
            performative.title = title
            description = msg.description
            performative.description = description
            labels = msg.labels
            performative.labels.update(labels)
            prometheus_msg.add_metric.CopyFrom(performative)
        elif performative_id == PrometheusMessage.Performative.UPDATE_METRIC:
            performative = prometheus_pb2.PrometheusMessage.Update_Metric_Performative()  # type: ignore
            title = msg.title
            performative.title = title
            callable = msg.callable
            performative.callable = callable
            value = msg.value
            performative.value = value
            labels = msg.labels
            performative.labels.update(labels)
            prometheus_msg.update_metric.CopyFrom(performative)
        elif performative_id == PrometheusMessage.Performative.RESPONSE:
            performative = prometheus_pb2.PrometheusMessage.Response_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            if msg.is_set("message"):
                performative.message_is_set = True
                message = msg.message
                performative.message = message
            prometheus_msg.response.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = prometheus_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Prometheus' message.

        :param obj: the bytes object.
        :return: the 'Prometheus' message.
        """
        message_pb = ProtobufMessage()
        prometheus_pb = prometheus_pb2.PrometheusMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        prometheus_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = prometheus_pb.WhichOneof("performative")
        performative_id = PrometheusMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == PrometheusMessage.Performative.ADD_METRIC:
            type = prometheus_pb.add_metric.type
            performative_content["type"] = type
            title = prometheus_pb.add_metric.title
            performative_content["title"] = title
            description = prometheus_pb.add_metric.description
            performative_content["description"] = description
            labels = prometheus_pb.add_metric.labels
            labels_dict = dict(labels)
            performative_content["labels"] = labels_dict
        elif performative_id == PrometheusMessage.Performative.UPDATE_METRIC:
            title = prometheus_pb.update_metric.title
            performative_content["title"] = title
            callable = prometheus_pb.update_metric.callable
            performative_content["callable"] = callable
            value = prometheus_pb.update_metric.value
            performative_content["value"] = value
            labels = prometheus_pb.update_metric.labels
            labels_dict = dict(labels)
            performative_content["labels"] = labels_dict
        elif performative_id == PrometheusMessage.Performative.RESPONSE:
            code = prometheus_pb.response.code
            performative_content["code"] = code
            if prometheus_pb.response.message_is_set:
                message = prometheus_pb.response.message
                performative_content["message"] = message
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return PrometheusMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
