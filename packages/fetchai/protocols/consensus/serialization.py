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

"""Serialization module for consensus protocol."""

from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.consensus import consensus_pb2
from packages.fetchai.protocols.consensus.message import ConsensusMessage


class ConsensusSerializer(Serializer):
    """Serialization for the 'consensus' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Consensus' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(ConsensusMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        consensus_msg = consensus_pb2.ConsensusMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == ConsensusMessage.Performative.OBSERVATION:
            performative = consensus_pb2.ConsensusMessage.Observation_Performative()  # type: ignore
            value = msg.value
            performative.value = value
            time = msg.time
            performative.time = time
            source = msg.source
            performative.source = source
            signature = msg.signature
            performative.signature = signature
            consensus_msg.observation.CopyFrom(performative)
        elif performative_id == ConsensusMessage.Performative.AGGREGATION:
            performative = consensus_pb2.ConsensusMessage.Aggregation_Performative()  # type: ignore
            value = msg.value
            performative.value = value
            time = msg.time
            performative.time = time
            contributors = msg.contributors
            performative.contributors.extend(contributors)
            signature = msg.signature
            performative.signature = signature
            consensus_msg.aggregation.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = consensus_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Consensus' message.

        :param obj: the bytes object.
        :return: the 'Consensus' message.
        """
        message_pb = ProtobufMessage()
        consensus_pb = consensus_pb2.ConsensusMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        consensus_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = consensus_pb.WhichOneof("performative")
        performative_id = ConsensusMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == ConsensusMessage.Performative.OBSERVATION:
            value = consensus_pb.observation.value
            performative_content["value"] = value
            time = consensus_pb.observation.time
            performative_content["time"] = time
            source = consensus_pb.observation.source
            performative_content["source"] = source
            signature = consensus_pb.observation.signature
            performative_content["signature"] = signature
        elif performative_id == ConsensusMessage.Performative.AGGREGATION:
            value = consensus_pb.aggregation.value
            performative_content["value"] = value
            time = consensus_pb.aggregation.time
            performative_content["time"] = time
            contributors = consensus_pb.aggregation.contributors
            contributors_tuple = tuple(contributors)
            performative_content["contributors"] = contributors_tuple
            signature = consensus_pb.aggregation.signature
            performative_content["signature"] = signature
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return ConsensusMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
