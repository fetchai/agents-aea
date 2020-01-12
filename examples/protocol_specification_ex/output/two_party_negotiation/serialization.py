"""Serialization for two_party_negotiation protocol."""

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from packages.fetchai.protocols.two_party_negotiation.message import TwoPartyNegotiationMessage

import json
import base64
import pickle


class TwoPartyNegotiationSerializer(Serializer):
    """Serialization for two_party_negotiation protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'TwoPartyNegotiation' message into bytes."""
        body = {}  # Dict[str, Any]
        body["message_id"] = msg.get("message_id")
        body["target"] = msg.get("target")
        body["performative"] = msg.get("performative")

        contents_dict = msg.get("contents")
        contents_dict_bytes = base64.b64encode(pickle.dumps(contents_dict)).decode("utf-8")
        body["contents"] = contents_dict_bytes

        bytes_msg = json.dumps(body).encode("utf-8")
        return bytes_msg

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a 'TwoPartyNegotiation' message."""
        json_body = json.loads(obj.decode("utf-8"))
        message_id = json_body["message_id"]
        target = json_body["target"]
        performative = json_body["performative"]

        contents_dict_bytes = base64.b64decode(json_body["contents"])
        contents_dict = pickle.loads(contents_dict_bytes)

        return TwoPartyNegotiationMessage(message_id=message_id, target=target, performative=performative, contents=contents_dict)
