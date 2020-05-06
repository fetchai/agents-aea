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

"""Serialization module for two_party_negotiation protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.two_party_negotiation import two_party_negotiation_pb2
from packages.fetchai.protocols.two_party_negotiation.custom_types import Description
from packages.fetchai.protocols.two_party_negotiation.custom_types import Query
from packages.fetchai.protocols.two_party_negotiation.message import (
    TwoPartyNegotiationMessage,
)


class TwoPartyNegotiationSerializer(Serializer):
    """Serialization for the 'two_party_negotiation' protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Encode a 'TwoPartyNegotiation' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(TwoPartyNegotiationMessage, msg)
        two_party_negotiation_msg = (
            two_party_negotiation_pb2.TwoPartyNegotiationMessage()
        )
        two_party_negotiation_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        two_party_negotiation_msg.dialogue_starter_reference = dialogue_reference[0]
        two_party_negotiation_msg.dialogue_responder_reference = dialogue_reference[1]
        two_party_negotiation_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == TwoPartyNegotiationMessage.Performative.CFP:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Cfp_Performative()  # type: ignore
            query = msg.query
            Query.encode(performative.query, query)
            two_party_negotiation_msg.cfp.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.PROPOSE:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Propose_Performative()  # type: ignore
            proposal = msg.proposal
            Description.encode(performative.proposal, proposal)
            two_party_negotiation_msg.propose.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.ACCEPT:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Accept_Performative()  # type: ignore
            two_party_negotiation_msg.accept.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.DECLINE:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Decline_Performative()  # type: ignore
            two_party_negotiation_msg.decline.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.MATCH_ACCEPT:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Match_Accept_Performative()  # type: ignore
            two_party_negotiation_msg.match_accept.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        two_party_negotiation_bytes = two_party_negotiation_msg.SerializeToString()
        return two_party_negotiation_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode bytes into a 'TwoPartyNegotiation' message.

        :param obj: the bytes object.
        :return: the 'TwoPartyNegotiation' message.
        """
        two_party_negotiation_pb = (
            two_party_negotiation_pb2.TwoPartyNegotiationMessage()
        )
        two_party_negotiation_pb.ParseFromString(obj)
        message_id = two_party_negotiation_pb.message_id
        dialogue_reference = (
            two_party_negotiation_pb.dialogue_starter_reference,
            two_party_negotiation_pb.dialogue_responder_reference,
        )
        target = two_party_negotiation_pb.target

        performative = two_party_negotiation_pb.WhichOneof("performative")
        performative_id = TwoPartyNegotiationMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == TwoPartyNegotiationMessage.Performative.CFP:
            pb2_query = two_party_negotiation_pb.cfp.query
            query = Query.decode(pb2_query)
            performative_content["query"] = query
        elif performative_id == TwoPartyNegotiationMessage.Performative.PROPOSE:
            pb2_proposal = two_party_negotiation_pb.propose.proposal
            proposal = Description.decode(pb2_proposal)
            performative_content["proposal"] = proposal
        elif performative_id == TwoPartyNegotiationMessage.Performative.ACCEPT:
            pass
        elif performative_id == TwoPartyNegotiationMessage.Performative.DECLINE:
            pass
        elif performative_id == TwoPartyNegotiationMessage.Performative.MATCH_ACCEPT:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return TwoPartyNegotiationMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
