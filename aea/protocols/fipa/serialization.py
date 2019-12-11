# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""Serialization for the FIPA protocol."""
import json
import pickle
from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.fipa import fipa_pb2
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.oef.models import Description, Query


class FIPASerializer(Serializer):
    """Serialization for the FIPA protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a FIPA message into bytes."""
        msg = cast(FIPAMessage, msg)
        fipa_msg = fipa_pb2.FIPAMessage()
        fipa_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        fipa_msg.dialogue_starter_reference = dialogue_reference[0]
        fipa_msg.dialogue_responder_reference = dialogue_reference[1]
        fipa_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == FIPAMessage.Performative.CFP:
            performative = fipa_pb2.FIPAMessage.CFP()  # type: ignore
            query = msg.query
            if query is None or query == b"":
                nothing = fipa_pb2.FIPAMessage.CFP.Nothing()  # type: ignore
                performative.nothing.CopyFrom(nothing)
            elif type(query) == Query:
                query = pickle.dumps(query)
                performative.query_bytes = query
            elif type(query) == bytes:
                performative.bytes = query
            else:
                raise ValueError("Query type not supported: {}".format(type(query)))
            fipa_msg.cfp.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.PROPOSE:
            performative = fipa_pb2.FIPAMessage.Propose()  # type: ignore
            proposal = cast(Description, msg.proposal)
            p_array_bytes = [pickle.dumps(p) for p in proposal]
            performative.proposal.extend(p_array_bytes)
            fipa_msg.propose.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.ACCEPT:
            performative = fipa_pb2.FIPAMessage.Accept()  # type: ignore
            fipa_msg.accept.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.MATCH_ACCEPT:
            performative = fipa_pb2.FIPAMessage.MatchAccept()  # type: ignore
            fipa_msg.match_accept.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.ACCEPT_W_INFORM:
            performative = fipa_pb2.FIPAMessage.AcceptWInform()  # type: ignore
            data = msg.info
            data_bytes = json.dumps(data).encode("utf-8")
            performative.bytes = data_bytes
            fipa_msg.accept_w_inform.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            performative = fipa_pb2.FIPAMessage.MatchAcceptWInform()  # type: ignore
            data = msg.info
            data_bytes = json.dumps(data).encode("utf-8")
            performative.bytes = data_bytes
            fipa_msg.match_accept_w_inform.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.DECLINE:
            performative = fipa_pb2.FIPAMessage.Decline()  # type: ignore
            fipa_msg.decline.CopyFrom(performative)
        elif performative_id == FIPAMessage.Performative.INFORM:
            performative = fipa_pb2.FIPAMessage.Inform()  # type: ignore
            data = msg.info
            data_bytes = json.dumps(data).encode("utf-8")
            performative.bytes = data_bytes
            fipa_msg.inform.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        fipa_bytes = fipa_msg.SerializeToString()
        return fipa_bytes

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a FIPA message."""
        fipa_pb = fipa_pb2.FIPAMessage()
        fipa_pb.ParseFromString(obj)
        message_id = fipa_pb.message_id
        dialogue_reference = (fipa_pb.dialogue_starter_reference, fipa_pb.dialogue_responder_reference)
        target = fipa_pb.target

        performative = fipa_pb.WhichOneof("performative")
        performative_id = FIPAMessage.Performative(str(performative))
        performative_content = dict()
        if performative_id == FIPAMessage.Performative.CFP:
            query_type = fipa_pb.cfp.WhichOneof("query")
            if query_type == "nothing":
                query = None
            elif query_type == "query_bytes":
                query = pickle.loads(fipa_pb.cfp.query_bytes)
            elif query_type == "bytes":
                query = fipa_pb.cfp.bytes
            else:
                raise ValueError("Query type not recognized.")  # pragma: no cover
            performative_content["query"] = query
        elif performative_id == FIPAMessage.Performative.PROPOSE:
            descriptions = []
            for p_bytes in fipa_pb.propose.proposal:
                p = pickle.loads(p_bytes)  # type: Description
                descriptions.append(p)
            performative_content["proposal"] = descriptions
        elif performative_id == FIPAMessage.Performative.ACCEPT:
            pass
        elif performative_id == FIPAMessage.Performative.MATCH_ACCEPT:
            pass
        elif performative_id == FIPAMessage.Performative.ACCEPT_W_INFORM:
            info = json.loads(fipa_pb.accept_w_inform.bytes)
            performative_content['info'] = info
        elif performative_id == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            info = json.loads(fipa_pb.match_accept_w_inform.bytes)
            performative_content['info'] = info
        elif performative_id == FIPAMessage.Performative.DECLINE:
            pass
        elif performative_id == FIPAMessage.Performative.INFORM:
            info = json.loads(fipa_pb.inform.bytes)
            performative_content["info"] = info
        else:
            raise ValueError("Performative not valid: {}.".format(performative))

        return FIPAMessage(message_id=message_id, dialogue_reference=dialogue_reference, target=target,
                           performative=performative, **performative_content)
