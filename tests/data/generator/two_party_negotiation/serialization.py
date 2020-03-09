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

from tests.data.generator.two_party_negotiation import two_party_negotiation_pb2
from tests.data.generator.two_party_negotiation.message import (
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
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Cfp()  # type: ignore
            query = msg.query
            performative.query = query
            two_party_negotiation_msg.cfp.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.PROPOSE:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Propose()  # type: ignore
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
                performative.proposal_is_set = True
                proposal = msg.proposal
                performative.proposal.update(proposal)
            rounds = msg.rounds
            performative.rounds.extend(rounds)
            items = msg.items
            performative.items.extend(items)
            if msg.is_set("conditions_type_str"):
                performative.conditions_type_str_is_set = True
                conditions_type_str = msg.conditions_type_str
                performative.conditions_type_str = conditions_type_str
            if msg.is_set("conditions_type_dict_of_str_int"):
                performative.conditions_type_dict_of_str_int_is_set = True
                conditions_type_dict_of_str_int = msg.conditions_type_dict_of_str_int
                performative.conditions_type_dict_of_str_int.update(
                    conditions_type_dict_of_str_int
                )
            if msg.is_set("conditions_type_set_of_str"):
                performative.conditions_type_set_of_str_is_set = True
                conditions_type_set_of_str = msg.conditions_type_set_of_str
                performative.conditions_type_set_of_str.extend(
                    conditions_type_set_of_str
                )
            if msg.is_set("conditions_type_dict_of_str_float"):
                performative.conditions_type_dict_of_str_float_is_set = True
                conditions_type_dict_of_str_float = (
                    msg.conditions_type_dict_of_str_float
                )
                performative.conditions_type_dict_of_str_float.update(
                    conditions_type_dict_of_str_float
                )
            two_party_negotiation_msg.propose.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.REQUEST:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Request()  # type: ignore
            method = msg.method
            performative.method = method
            url = msg.url
            performative.url = url
            version = msg.version
            performative.version = version
            headers = msg.headers
            performative.headers = headers
            if msg.is_set("bodyy"):
                performative.bodyy_is_set = True
                bodyy = msg.bodyy
                performative.bodyy = bodyy
            two_party_negotiation_msg.request.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.ACCEPT:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Accept()  # type: ignore
            two_party_negotiation_msg.accept.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.INFORM:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Inform()  # type: ignore
            inform_number = msg.inform_number
            performative.inform_number.extend(inform_number)
            two_party_negotiation_msg.inform.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.INFORM_REPLY:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Inform_Reply()  # type: ignore
            reply_message = msg.reply_message
            performative.reply_message.update(reply_message)
            two_party_negotiation_msg.inform_reply.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.DECLINE:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Decline()  # type: ignore
            two_party_negotiation_msg.decline.CopyFrom(performative)
        elif performative_id == TwoPartyNegotiationMessage.Performative.MATCH_ACCEPT:
            performative = two_party_negotiation_pb2.TwoPartyNegotiationMessage.Match_Accept()  # type: ignore
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
            if two_party_negotiation_pb.propose.proposal_is_set:
                proposal = two_party_negotiation_pb.propose.proposal
                proposal_dict = dict(proposal)
                performative_content["proposal"] = proposal_dict
            rounds = two_party_negotiation_pb.propose.rounds
            rounds_frozenset = frozenset(rounds)
            performative_content["rounds"] = rounds_frozenset
            items = two_party_negotiation_pb.propose.items
            items_tuple = tuple(items)
            performative_content["items"] = items_tuple
            if two_party_negotiation_pb.propose.conditions_type_str_is_set:
                conditions = two_party_negotiation_pb.propose.conditions_type_str
                performative_content["conditions"] = conditions
            if two_party_negotiation_pb.propose.conditions_type_dict_of_str_int_is_set:
                conditions = two_party_negotiation_pb.propose.conditions
                conditions_dict = dict(conditions)
                performative_content["conditions"] = conditions_dict
            if two_party_negotiation_pb.propose.conditions_type_set_of_str_is_set:
                conditions = two_party_negotiation_pb.propose.conditions
                conditions_frozenset = frozenset(conditions)
                performative_content["conditions"] = conditions_frozenset
            if (
                two_party_negotiation_pb.propose.conditions_type_dict_of_str_float_is_set
            ):
                conditions = two_party_negotiation_pb.propose.conditions
                conditions_dict = dict(conditions)
                performative_content["conditions"] = conditions_dict
        elif performative_id == TwoPartyNegotiationMessage.Performative.REQUEST:
            method = two_party_negotiation_pb.request.method
            performative_content["method"] = method
            url = two_party_negotiation_pb.request.url
            performative_content["url"] = url
            version = two_party_negotiation_pb.request.version
            performative_content["version"] = version
            headers = two_party_negotiation_pb.request.headers
            performative_content["headers"] = headers
            if two_party_negotiation_pb.request.bodyy_is_set:
                bodyy = two_party_negotiation_pb.request.bodyy
                performative_content["bodyy"] = bodyy
        elif performative_id == TwoPartyNegotiationMessage.Performative.ACCEPT:
            pass
        elif performative_id == TwoPartyNegotiationMessage.Performative.INFORM:
            inform_number = two_party_negotiation_pb.inform.inform_number
            inform_number_tuple = tuple(inform_number)
            performative_content["inform_number"] = inform_number_tuple
        elif performative_id == TwoPartyNegotiationMessage.Performative.INFORM_REPLY:
            reply_message = two_party_negotiation_pb.inform_reply.reply_message
            reply_message_dict = dict(reply_message)
            performative_content["reply_message"] = reply_message_dict
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
