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

"""Serialization module for signing protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer
from aea.protocols.signing import signing_pb2
from aea.protocols.signing.custom_types import ErrorCode
from aea.protocols.signing.custom_types import RawMessage
from aea.protocols.signing.custom_types import RawTransaction
from aea.protocols.signing.custom_types import SignedMessage
from aea.protocols.signing.custom_types import SignedTransaction
from aea.protocols.signing.custom_types import Terms
from aea.protocols.signing.message import SigningMessage


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
        signing_msg = signing_pb2.SigningMessage()
        signing_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        signing_msg.dialogue_starter_reference = dialogue_reference[0]
        signing_msg.dialogue_responder_reference = dialogue_reference[1]
        signing_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == SigningMessage.Performative.SIGN_TRANSACTION:
            performative = signing_pb2.SigningMessage.Sign_Transaction_Performative()  # type: ignore
            skill_callback_ids = msg.skill_callback_ids
            performative.skill_callback_ids.extend(skill_callback_ids)
            skill_callback_info = msg.skill_callback_info
            performative.skill_callback_info.update(skill_callback_info)
            terms = msg.terms
            Terms.encode(performative.terms, terms)
            raw_transaction = msg.raw_transaction
            RawTransaction.encode(performative.raw_transaction, raw_transaction)
            signing_msg.sign_transaction.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGN_MESSAGE:
            performative = signing_pb2.SigningMessage.Sign_Message_Performative()  # type: ignore
            skill_callback_ids = msg.skill_callback_ids
            performative.skill_callback_ids.extend(skill_callback_ids)
            skill_callback_info = msg.skill_callback_info
            performative.skill_callback_info.update(skill_callback_info)
            terms = msg.terms
            Terms.encode(performative.terms, terms)
            raw_message = msg.raw_message
            RawMessage.encode(performative.raw_message, raw_message)
            signing_msg.sign_message.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGNED_TRANSACTION:
            performative = signing_pb2.SigningMessage.Signed_Transaction_Performative()  # type: ignore
            skill_callback_ids = msg.skill_callback_ids
            performative.skill_callback_ids.extend(skill_callback_ids)
            skill_callback_info = msg.skill_callback_info
            performative.skill_callback_info.update(skill_callback_info)
            signed_transaction = msg.signed_transaction
            SignedTransaction.encode(
                performative.signed_transaction, signed_transaction
            )
            signing_msg.signed_transaction.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.SIGNED_MESSAGE:
            performative = signing_pb2.SigningMessage.Signed_Message_Performative()  # type: ignore
            skill_callback_ids = msg.skill_callback_ids
            performative.skill_callback_ids.extend(skill_callback_ids)
            skill_callback_info = msg.skill_callback_info
            performative.skill_callback_info.update(skill_callback_info)
            signed_message = msg.signed_message
            SignedMessage.encode(performative.signed_message, signed_message)
            signing_msg.signed_message.CopyFrom(performative)
        elif performative_id == SigningMessage.Performative.ERROR:
            performative = signing_pb2.SigningMessage.Error_Performative()  # type: ignore
            skill_callback_ids = msg.skill_callback_ids
            performative.skill_callback_ids.extend(skill_callback_ids)
            skill_callback_info = msg.skill_callback_info
            performative.skill_callback_info.update(skill_callback_info)
            error_code = msg.error_code
            ErrorCode.encode(performative.error_code, error_code)
            signing_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        signing_bytes = signing_msg.SerializeToString()
        return signing_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Signing' message.

        :param obj: the bytes object.
        :return: the 'Signing' message.
        """
        signing_pb = signing_pb2.SigningMessage()
        signing_pb.ParseFromString(obj)
        message_id = signing_pb.message_id
        dialogue_reference = (
            signing_pb.dialogue_starter_reference,
            signing_pb.dialogue_responder_reference,
        )
        target = signing_pb.target

        performative = signing_pb.WhichOneof("performative")
        performative_id = SigningMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == SigningMessage.Performative.SIGN_TRANSACTION:
            skill_callback_ids = signing_pb.sign_transaction.skill_callback_ids
            skill_callback_ids_tuple = tuple(skill_callback_ids)
            performative_content["skill_callback_ids"] = skill_callback_ids_tuple
            skill_callback_info = signing_pb.sign_transaction.skill_callback_info
            skill_callback_info_dict = dict(skill_callback_info)
            performative_content["skill_callback_info"] = skill_callback_info_dict
            pb2_terms = signing_pb.sign_transaction.terms
            terms = Terms.decode(pb2_terms)
            performative_content["terms"] = terms
            pb2_raw_transaction = signing_pb.sign_transaction.raw_transaction
            raw_transaction = RawTransaction.decode(pb2_raw_transaction)
            performative_content["raw_transaction"] = raw_transaction
        elif performative_id == SigningMessage.Performative.SIGN_MESSAGE:
            skill_callback_ids = signing_pb.sign_message.skill_callback_ids
            skill_callback_ids_tuple = tuple(skill_callback_ids)
            performative_content["skill_callback_ids"] = skill_callback_ids_tuple
            skill_callback_info = signing_pb.sign_message.skill_callback_info
            skill_callback_info_dict = dict(skill_callback_info)
            performative_content["skill_callback_info"] = skill_callback_info_dict
            pb2_terms = signing_pb.sign_message.terms
            terms = Terms.decode(pb2_terms)
            performative_content["terms"] = terms
            pb2_raw_message = signing_pb.sign_message.raw_message
            raw_message = RawMessage.decode(pb2_raw_message)
            performative_content["raw_message"] = raw_message
        elif performative_id == SigningMessage.Performative.SIGNED_TRANSACTION:
            skill_callback_ids = signing_pb.signed_transaction.skill_callback_ids
            skill_callback_ids_tuple = tuple(skill_callback_ids)
            performative_content["skill_callback_ids"] = skill_callback_ids_tuple
            skill_callback_info = signing_pb.signed_transaction.skill_callback_info
            skill_callback_info_dict = dict(skill_callback_info)
            performative_content["skill_callback_info"] = skill_callback_info_dict
            pb2_signed_transaction = signing_pb.signed_transaction.signed_transaction
            signed_transaction = SignedTransaction.decode(pb2_signed_transaction)
            performative_content["signed_transaction"] = signed_transaction
        elif performative_id == SigningMessage.Performative.SIGNED_MESSAGE:
            skill_callback_ids = signing_pb.signed_message.skill_callback_ids
            skill_callback_ids_tuple = tuple(skill_callback_ids)
            performative_content["skill_callback_ids"] = skill_callback_ids_tuple
            skill_callback_info = signing_pb.signed_message.skill_callback_info
            skill_callback_info_dict = dict(skill_callback_info)
            performative_content["skill_callback_info"] = skill_callback_info_dict
            pb2_signed_message = signing_pb.signed_message.signed_message
            signed_message = SignedMessage.decode(pb2_signed_message)
            performative_content["signed_message"] = signed_message
        elif performative_id == SigningMessage.Performative.ERROR:
            skill_callback_ids = signing_pb.error.skill_callback_ids
            skill_callback_ids_tuple = tuple(skill_callback_ids)
            performative_content["skill_callback_ids"] = skill_callback_ids_tuple
            skill_callback_info = signing_pb.error.skill_callback_info
            skill_callback_info_dict = dict(skill_callback_info)
            performative_content["skill_callback_info"] = skill_callback_info_dict
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
