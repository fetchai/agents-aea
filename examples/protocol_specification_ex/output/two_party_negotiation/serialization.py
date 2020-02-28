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

from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.two_party_negotiation import (
    TwoPartyNegotiation_pb2,
)
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
        two_party_negotiation_msg = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage()
        two_party_negotiation_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        two_party_negotiation_msg.dialogue_starter_reference = dialogue_reference[0]
        two_party_negotiation_msg.dialogue_responder_reference = dialogue_reference[1]
        two_party_negotiation_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == TwoPartyNegotiationMessage.Performative.CFP:
            performative = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage.Cfp()  # type: ignore
            query = msg.query
            performative.query = query
            two_party_negotiation_msg.cfp.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.PROPOSE:
            performative = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage.Propose()  # type: ignore
            number = msg.number
            performative.number = number
            price = msg.price
            performative.price = price
            description = msg.description
            performative.description = description
            flag = msg.flag
            performative.flag = flag
            query = msg.query
            performative.query = query
            if msg.is_set("proposal"):
                proposal = msg.proposal
                performative.proposal.update(proposal)
            rounds = msg.rounds
            performative.rounds.extend(rounds)
            items = msg.items
            performative.items.extend(items)
            if msg.is_set("conditions_type_str"):
                conditions_type_str = msg.conditions_type_str
                performative.conditions_type_str = conditions_type_str
            if msg.is_set("conditions_type_dict_of_str_int"):
                conditions_type_dict_of_str_int = msg.conditions_type_dict_of_str_int
                performative.conditions_type_dict_of_str_int.update(conditions_type_dict_of_str_int)
            if msg.is_set("conditions_type_set_of_DataModel"):
                conditions_type_set_of_DataModel = msg.conditions_type_set_of_DataModel
                performative.conditions_type_set_of_DataModel.extend(conditions_type_set_of_DataModel)
            if msg.is_set("conditions_type_dict_of_str_float"):
                conditions_type_dict_of_str_float = msg.conditions_type_dict_of_str_float
                performative.conditions_type_dict_of_str_float.update(conditions_type_dict_of_str_float)
            two_party_negotiation_msg.propose.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.ACCEPT:
            performative = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage.Accept()  # type: ignore
            two_party_negotiation_msg.accept.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.DECLINE:
            performative = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage.Decline()  # type: ignore
            two_party_negotiation_msg.decline.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.MATCH_ACCEPT:
            performative = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage.Match_Accept()  # type: ignore
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
        two_party_negotiation_pb = TwoPartyNegotiation_pb2.TwoPartyNegotiationMessage()
        two_party_negotiation_pb.ParseFromString(obj)
        message_id = two_party_negotiation_pb.message_id
        dialogue_reference = (
            two_party_negotiation_pb.dialogue_starter_reference,
            two_party_negotiation_pb.dialogue_responder_reference,
        )
        target = two_party_negotiation_pb.target

        performative = two_party_negotiation_pb.WhichOneof("performative")
        performative_id = TwoPartyNegotiationMessage.Performative(str(performative))
        performative_content = dict()
        if performative_id == TwoPartyNegotiationMessage.Performative.CFP:
            query = two_party_negotiation_pb.cfp.query
            performative_content["query"] = query
        elif performative_id == TwoPartyNegotiationMessage.Performative.PROPOSE:
            number = two_party_negotiation_pb.propose.number
            performative_content["number"] = number
            price = two_party_negotiation_pb.propose.price
            performative_content["price"] = price
            description = two_party_negotiation_pb.propose.description
            performative_content["description"] = description
            flag = two_party_negotiation_pb.propose.flag
            performative_content["flag"] = flag
            query = two_party_negotiation_pb.propose.query
            performative_content["query"] = query
            if two_party_negotiation_pb.propose.HasField("proposal"):
                proposal = two_party_negotiation_pb.propose.proposal
                performative_content["proposal"] = proposal
            rounds = two_party_negotiation_pb.propose.rounds
            performative_content["rounds"] = rounds
            items = two_party_negotiation_pb.propose.items
            performative_content["items"] = items
            if two_party_negotiation_pb.propose.HasField("conditions_type_str"):
                conditions = two_party_negotiation_pb.propose.conditions_type_str
                performative_content["conditions"] = conditions
            if two_party_negotiation_pb.propose.HasField("conditions_type_dict_of_str_int"):
                conditions = two_party_negotiation_pb.propose.conditions
                performative_content["conditions"] = conditions
            if two_party_negotiation_pb.propose.HasField("conditions_type_set_of_DataModel"):
                conditions = two_party_negotiation_pb.propose.conditions
                performative_content["conditions"] = conditions
            if two_party_negotiation_pb.propose.HasField("conditions_type_dict_of_str_float"):
                conditions = two_party_negotiation_pb.propose.conditions
                performative_content["conditions"] = conditions
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
