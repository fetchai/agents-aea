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

"""Serialization module for acn protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.acn import acn_pb2
from packages.fetchai.protocols.acn.custom_types import AgentRecord, StatusBody
from packages.fetchai.protocols.acn.message import AcnMessage


class AcnSerializer(Serializer):
    """Serialization for the 'acn' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Acn' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(AcnMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        acn_msg = acn_pb2.AcnMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == AcnMessage.Performative.REGISTER:
            performative = acn_pb2.AcnMessage.Register_Performative()  # type: ignore
            record = msg.record
            AgentRecord.encode(performative.record, record)
            acn_msg.register.CopyFrom(performative)
        elif performative_id == AcnMessage.Performative.LOOKUP_REQUEST:
            performative = acn_pb2.AcnMessage.Lookup_Request_Performative()  # type: ignore
            agent_address = msg.agent_address
            performative.agent_address = agent_address
            acn_msg.lookup_request.CopyFrom(performative)
        elif performative_id == AcnMessage.Performative.LOOKUP_RESPONSE:
            performative = acn_pb2.AcnMessage.Lookup_Response_Performative()  # type: ignore
            record = msg.record
            AgentRecord.encode(performative.record, record)
            acn_msg.lookup_response.CopyFrom(performative)
        elif performative_id == AcnMessage.Performative.AEA_ENVELOPE:
            performative = acn_pb2.AcnMessage.Aea_Envelope_Performative()  # type: ignore
            envelope = msg.envelope
            performative.envelope = envelope
            record = msg.record
            AgentRecord.encode(performative.record, record)
            acn_msg.aea_envelope.CopyFrom(performative)
        elif performative_id == AcnMessage.Performative.STATUS:
            performative = acn_pb2.AcnMessage.Status_Performative()  # type: ignore
            body = msg.body
            StatusBody.encode(performative.body, body)
            acn_msg.status.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = acn_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Acn' message.

        :param obj: the bytes object.
        :return: the 'Acn' message.
        """
        message_pb = ProtobufMessage()
        acn_pb = acn_pb2.AcnMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        acn_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = acn_pb.WhichOneof("performative")
        performative_id = AcnMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == AcnMessage.Performative.REGISTER:
            pb2_record = acn_pb.register.record
            record = AgentRecord.decode(pb2_record)
            performative_content["record"] = record
        elif performative_id == AcnMessage.Performative.LOOKUP_REQUEST:
            agent_address = acn_pb.lookup_request.agent_address
            performative_content["agent_address"] = agent_address
        elif performative_id == AcnMessage.Performative.LOOKUP_RESPONSE:
            pb2_record = acn_pb.lookup_response.record
            record = AgentRecord.decode(pb2_record)
            performative_content["record"] = record
        elif performative_id == AcnMessage.Performative.AEA_ENVELOPE:
            envelope = acn_pb.aea_envelope.envelope
            performative_content["envelope"] = envelope
            pb2_record = acn_pb.aea_envelope.record
            record = AgentRecord.decode(pb2_record)
            performative_content["record"] = record
        elif performative_id == AcnMessage.Performative.STATUS:
            pb2_body = acn_pb.status.body
            body = StatusBody.decode(pb2_body)
            performative_content["body"] = body
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return AcnMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
