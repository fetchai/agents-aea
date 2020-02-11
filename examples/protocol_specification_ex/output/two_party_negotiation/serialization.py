"""Serialization for two_party_negotiation protocol."""

from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.two_party_negotiation import two_party_negotiation_pb2
from packages.fetchai.protocols.two_party_negotiation.message import (
    TwoPartyNegotiationMessage,
)


class TwoPartyNegotiationSerializer(Serializer):
    """Serialization for two_party_negotiation protocol."""

    def encode(self, msg: Message) -> bytes:
        """Encode a 'TwoPartyNegotiation' message into bytes."""
        msg = cast(TwoPartyNegotiationMessage, msg)
        two_party_negotiation_msg = (
            two_party_negotiation_pb2.TwoPartyNegotiationMessage()
        )
        two_party_negotiation_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        two_party_negotiation_msg.dialogue_starter_reference = dialogue_reference[0]
        two_party_negotiation_msg.dialogue_responder_reference = dialogue_reference[1]
        two_party_negotiation_msg.target = msg.target

        two_party_negotiation_bytes = two_party_negotiation_msg.SerializeToString()
        return two_party_negotiation_bytes

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a 'TwoPartyNegotiation' message."""
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

        return TwoPartyNegotiationMessage(
            message_id=message_id, dialogue_reference=dialogue_reference, target=target,
        )
