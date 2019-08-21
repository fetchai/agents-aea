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
import pickle

from google.protobuf.struct_pb2 import Struct

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer
from aea.protocols.fipa import fipa_pb2
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.oef.models import Description


class FIPASerializer(Serializer):
    """Serialization for the FIPA protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a FIPA message into bytes."""
        fipa_msg = fipa_pb2.FIPAMessage()
        fipa_msg.message_id = msg.get("id")
        fipa_msg.dialogue_id = msg.get("dialogue_id")
        fipa_msg.target = msg.get("target")

        performative_id = msg.get("performative").value
        if performative_id == "cfp":
            performative = fipa_pb2.FIPAMessage.CFP()
            query = msg.get("query")
            if query is None:
                nothing = fipa_pb2.FIPAMessage.CFP.Nothing()
                performative.nothing.CopyFrom(nothing)
            elif type(query) == dict:
                performative.json.update(query)
            elif type(query) == bytes:
                performative.bytes = query
            else:
                raise ValueError("Query type not supported: {}".format(type(query)))
            fipa_msg.cfp.CopyFrom(performative)
        elif performative_id == "propose":
            performative = fipa_pb2.FIPAMessage.Propose()
            proposal = msg.get("proposal")
            p_array_bytes = [p.to_pb().SerializeToString() for p in proposal]
            performative.proposal.extend(p_array_bytes)
            fipa_msg.propose.CopyFrom(performative)

        elif performative_id == "accept":
            performative = fipa_pb2.FIPAMessage.Accept()
            fipa_msg.accept.CopyFrom(performative)
        elif performative_id == "match_accept":
            performative = fipa_pb2.FIPAMessage.MatchAccept()
            fipa_msg.match_accept.CopyFrom(performative)
        elif performative_id == "decline":
            performative = fipa_pb2.FIPAMessage.Decline()
            fipa_msg.decline.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        fipa_bytes = fipa_msg.SerializeToString()
        return fipa_bytes

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a FIPA message."""
        fipa_pb = fipa_pb2.FIPAMessage()
        fipa_pb.ParseFromString(obj)
        message_id = fipa_pb.message_id
        dialogue_id = fipa_pb.dialogue_id
        target = fipa_pb.target

        performative = fipa_pb.WhichOneof("performative")
        performative_id = FIPAMessage.Performative(str(performative))
        performative_content = dict()
        if performative_id == FIPAMessage.Performative.CFP:
            query_type = fipa_pb.cfp.WhichOneof("query")
            if query_type == "nothing":
                query = None
            elif query_type == "json":
                query_pb = Struct()
                query_pb.update(fipa_pb.cfp.json)
                query = dict(query_pb)
            elif query_type == "bytes":
                query = fipa_pb.cfp.bytes
            else:
                raise ValueError("Query type not recognized.")

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
        elif performative_id == FIPAMessage.Performative.DECLINE:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative))

        return FIPAMessage(message_id=message_id, dialogue_id=dialogue_id, target=target,
                           performative=performative, **performative_content)
