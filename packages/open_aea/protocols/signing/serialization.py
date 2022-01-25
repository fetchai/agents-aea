# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 open_aea
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

"""Serialization module for signing protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.open_aea.protocols.signing import signing_pb2
from packages.open_aea.protocols.signing.custom_types import (
    ErrorCode,
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    Terms,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class SigningSerializer(Serializer):
    """Serialization for the 'signing' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Signing' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(SigningMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        signing_msg = signing_pb2.SigningMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == SigningMessage.Performative.SIGN_TRANSACTION:
            performative = signing_pb2.SigningMessage.Sign_Transaction_Performative()  # type: ignore
            terms = msg.terms
            Terms.encode(performative.terms, terms)
            raw_transaction = msg.raw_transaction
            RawTransaction.encode(performative.raw_transaction, raw_transaction)
            signing_msg.sign_transaction.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGN_MESSAGE:
            performative = signing_pb2.SigningMessage.Sign_Message_Performative()  # type: ignore
            terms = msg.terms
            Terms.encode(performative.terms, terms)
            raw_message = msg.raw_message
            RawMessage.encode(performative.raw_message, raw_message)
            signing_msg.sign_message.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGNED_TRANSACTION:
            performative = signing_pb2.SigningMessage.Signed_Transaction_Performative()  # type: ignore
            signed_transaction = msg.signed_transaction
            SignedTransaction.encode(
                performative.signed_transaction, signed_transaction
            )
            signing_msg.signed_transaction.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGNED_MESSAGE:
            performative = signing_pb2.SigningMessage.Signed_Message_Performative()  # type: ignore
            signed_message = msg.signed_message
            SignedMessage.encode(performative.signed_message, signed_message)
            signing_msg.signed_message.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.ERROR:
            performative = signing_pb2.SigningMessage.Error_Performative()  # type: ignore
            error_code = msg.error_code
            ErrorCode.encode(performative.error_code, error_code)
            signing_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = signing_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Signing' message.

        :param obj: the bytes object.
        :return: the 'Signing' message.
        """
        message_pb = ProtobufMessage()
        signing_pb = signing_pb2.SigningMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        signing_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = signing_pb.WhichOneof("performative")
        performative_id = SigningMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == SigningMessage.Performative.SIGN_TRANSACTION:
            pb2_terms = signing_pb.sign_transaction.terms
            terms = Terms.decode(pb2_terms)
            performative_content["terms"] = terms
            pb2_raw_transaction = signing_pb.sign_transaction.raw_transaction
            raw_transaction = RawTransaction.decode(pb2_raw_transaction)
            performative_content["raw_transaction"] = raw_transaction
        elif performative_id == SigningMessage.Performative.SIGN_MESSAGE:
            pb2_terms = signing_pb.sign_message.terms
            terms = Terms.decode(pb2_terms)
            performative_content["terms"] = terms
            pb2_raw_message = signing_pb.sign_message.raw_message
            raw_message = RawMessage.decode(pb2_raw_message)
            performative_content["raw_message"] = raw_message
        elif performative_id == SigningMessage.Performative.SIGNED_TRANSACTION:
            pb2_signed_transaction = signing_pb.signed_transaction.signed_transaction
            signed_transaction = SignedTransaction.decode(pb2_signed_transaction)
            performative_content["signed_transaction"] = signed_transaction
        elif performative_id == SigningMessage.Performative.SIGNED_MESSAGE:
            pb2_signed_message = signing_pb.signed_message.signed_message
            signed_message = SignedMessage.decode(pb2_signed_message)
            performative_content["signed_message"] = signed_message
        elif performative_id == SigningMessage.Performative.ERROR:
            pb2_error_code = signing_pb.error.error_code
            error_code = ErrorCode.decode(pb2_error_code)
            performative_content["error_code"] = error_code
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return SigningMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
