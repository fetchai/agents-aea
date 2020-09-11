# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 AAAI_paper_authors
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

"""Serialization module for negotiation protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.AAAI_paper_authors.protocols.negotiation import negotiation_pb2
from packages.AAAI_paper_authors.protocols.negotiation.custom_types import Resources
from packages.AAAI_paper_authors.protocols.negotiation.message import NegotiationMessage


class NegotiationSerializer(Serializer):
    """Serialization for the 'negotiation' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Negotiation' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(NegotiationMessage, msg)
        negotiation_msg = negotiation_pb2.NegotiationMessage()
        negotiation_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        negotiation_msg.dialogue_starter_reference = dialogue_reference[0]
        negotiation_msg.dialogue_responder_reference = dialogue_reference[1]
        negotiation_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == NegotiationMessage.Performative.CFP:
            performative = negotiation_pb2.NegotiationMessage.Cfp_Performative()  # type: ignore
            e = msg.e
            Resources.encode(performative.e, e)
            negotiation_msg.cfp.CopyFrom(performative)
        elif performative_id == NegotiationMessage.Performative.PROPOSE:
            performative = negotiation_pb2.NegotiationMessage.Propose_Performative()  # type: ignore
            e = msg.e
            Resources.encode(performative.e, e)
            p = msg.p
            performative.p = p
            negotiation_msg.propose.CopyFrom(performative)
        elif performative_id == NegotiationMessage.Performative.ACCEPT:
            performative = negotiation_pb2.NegotiationMessage.Accept_Performative()  # type: ignore
            negotiation_msg.accept.CopyFrom(performative)
        elif performative_id == NegotiationMessage.Performative.DECLINE:
            performative = negotiation_pb2.NegotiationMessage.Decline_Performative()  # type: ignore
            negotiation_msg.decline.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        negotiation_bytes = negotiation_msg.SerializeToString()
        return negotiation_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Negotiation' message.

        :param obj: the bytes object.
        :return: the 'Negotiation' message.
        """
        negotiation_pb = negotiation_pb2.NegotiationMessage()
        negotiation_pb.ParseFromString(obj)
        message_id = negotiation_pb.message_id
        dialogue_reference = (
            negotiation_pb.dialogue_starter_reference,
            negotiation_pb.dialogue_responder_reference,
        )
        target = negotiation_pb.target

        performative = negotiation_pb.WhichOneof("performative")
        performative_id = NegotiationMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == NegotiationMessage.Performative.CFP:
            pb2_e = negotiation_pb.cfp.e
            e = Resources.decode(pb2_e)
            performative_content["e"] = e
        elif performative_id == NegotiationMessage.Performative.PROPOSE:
            pb2_e = negotiation_pb.propose.e
            e = Resources.decode(pb2_e)
            performative_content["e"] = e
            p = negotiation_pb.propose.p
            performative_content["p"] = p
        elif performative_id == NegotiationMessage.Performative.ACCEPT:
            pass
        elif performative_id == NegotiationMessage.Performative.DECLINE:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return NegotiationMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
