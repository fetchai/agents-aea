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

"""Serialization module for fipa protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.fipa import fipa_pb2
from packages.fetchai.protocols.fipa.custom_types import Description
from packages.fetchai.protocols.fipa.custom_types import Query
from packages.fetchai.protocols.fipa.message import FipaMessage


class FipaSerializer(Serializer):
    """Serialization for the 'fipa' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Fipa' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(FipaMessage, msg)
        fipa_msg = fipa_pb2.FipaMessage()
        fipa_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        fipa_msg.dialogue_starter_reference = dialogue_reference[0]
        fipa_msg.dialogue_responder_reference = dialogue_reference[1]
        fipa_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == FipaMessage.Performative.CFP:
            performative = fipa_pb2.FipaMessage.Cfp_Performative()  # type: ignore
            query = msg.query
            Query.encode(performative.query, query)
            fipa_msg.cfp.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.PROPOSE:
            performative = fipa_pb2.FipaMessage.Propose_Performative()  # type: ignore
            proposal = msg.proposal
            Description.encode(performative.proposal, proposal)
            fipa_msg.propose.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.ACCEPT_W_INFORM:
            performative = fipa_pb2.FipaMessage.Accept_W_Inform_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            fipa_msg.accept_w_inform.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            performative = fipa_pb2.FipaMessage.Match_Accept_W_Inform_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            fipa_msg.match_accept_w_inform.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.INFORM:
            performative = fipa_pb2.FipaMessage.Inform_Performative()  # type: ignore
            info = msg.info
            performative.info.update(info)
            fipa_msg.inform.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.ACCEPT:
            performative = fipa_pb2.FipaMessage.Accept_Performative()  # type: ignore
            fipa_msg.accept.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.DECLINE:
            performative = fipa_pb2.FipaMessage.Decline_Performative()  # type: ignore
            fipa_msg.decline.CopyFrom(performative)
        elif performative_id == FipaMessage.Performative.MATCH_ACCEPT:
            performative = fipa_pb2.FipaMessage.Match_Accept_Performative()  # type: ignore
            fipa_msg.match_accept.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        fipa_bytes = fipa_msg.SerializeToString()
        return fipa_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Fipa' message.

        :param obj: the bytes object.
        :return: the 'Fipa' message.
        """
        fipa_pb = fipa_pb2.FipaMessage()
        fipa_pb.ParseFromString(obj)
        message_id = fipa_pb.message_id
        dialogue_reference = (
            fipa_pb.dialogue_starter_reference,
            fipa_pb.dialogue_responder_reference,
        )
        target = fipa_pb.target

        performative = fipa_pb.WhichOneof("performative")
        performative_id = FipaMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == FipaMessage.Performative.CFP:
            pb2_query = fipa_pb.cfp.query
            query = Query.decode(pb2_query)
            performative_content["query"] = query
        elif performative_id == FipaMessage.Performative.PROPOSE:
            pb2_proposal = fipa_pb.propose.proposal
            proposal = Description.decode(pb2_proposal)
            performative_content["proposal"] = proposal
        elif performative_id == FipaMessage.Performative.ACCEPT_W_INFORM:
            info = fipa_pb.accept_w_inform.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            info = fipa_pb.match_accept_w_inform.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == FipaMessage.Performative.INFORM:
            info = fipa_pb.inform.info
            info_dict = dict(info)
            performative_content["info"] = info_dict
        elif performative_id == FipaMessage.Performative.ACCEPT:
            pass
        elif performative_id == FipaMessage.Performative.DECLINE:
            pass
        elif performative_id == FipaMessage.Performative.MATCH_ACCEPT:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return FipaMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
