# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

"""Serialization module for contract_api protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.contract_api import contract_api_pb2
from packages.fetchai.protocols.contract_api.custom_types import (
    Kwargs,
    RawMessage,
    RawTransaction,
    State,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage


class ContractApiSerializer(Serializer):
    """Serialization for the 'contract_api' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'ContractApi' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(ContractApiMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        contract_api_msg = contract_api_pb2.ContractApiMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION:
            performative = contract_api_pb2.ContractApiMessage.Get_Deploy_Transaction_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            contract_id = msg.contract_id
            performative.contract_id = contract_id
            callable = msg.callable
            performative.callable = callable
            kwargs = msg.kwargs
            Kwargs.encode(performative.kwargs, kwargs)
            contract_api_msg.get_deploy_transaction.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.GET_RAW_TRANSACTION:
            performative = contract_api_pb2.ContractApiMessage.Get_Raw_Transaction_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            contract_id = msg.contract_id
            performative.contract_id = contract_id
            contract_address = msg.contract_address
            performative.contract_address = contract_address
            callable = msg.callable
            performative.callable = callable
            kwargs = msg.kwargs
            Kwargs.encode(performative.kwargs, kwargs)
            contract_api_msg.get_raw_transaction.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.GET_RAW_MESSAGE:
            performative = contract_api_pb2.ContractApiMessage.Get_Raw_Message_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            contract_id = msg.contract_id
            performative.contract_id = contract_id
            contract_address = msg.contract_address
            performative.contract_address = contract_address
            callable = msg.callable
            performative.callable = callable
            kwargs = msg.kwargs
            Kwargs.encode(performative.kwargs, kwargs)
            contract_api_msg.get_raw_message.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.GET_STATE:
            performative = contract_api_pb2.ContractApiMessage.Get_State_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            contract_id = msg.contract_id
            performative.contract_id = contract_id
            contract_address = msg.contract_address
            performative.contract_address = contract_address
            callable = msg.callable
            performative.callable = callable
            kwargs = msg.kwargs
            Kwargs.encode(performative.kwargs, kwargs)
            contract_api_msg.get_state.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.STATE:
            performative = contract_api_pb2.ContractApiMessage.State_Performative()  # type: ignore
            state = msg.state
            State.encode(performative.state, state)
            contract_api_msg.state.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.RAW_TRANSACTION:
            performative = contract_api_pb2.ContractApiMessage.Raw_Transaction_Performative()  # type: ignore
            raw_transaction = msg.raw_transaction
            RawTransaction.encode(performative.raw_transaction, raw_transaction)
            contract_api_msg.raw_transaction.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.RAW_MESSAGE:
            performative = contract_api_pb2.ContractApiMessage.Raw_Message_Performative()  # type: ignore
            raw_message = msg.raw_message
            RawMessage.encode(performative.raw_message, raw_message)
            contract_api_msg.raw_message.CopyFrom(performative)
        elif performative_id == ContractApiMessage.Performative.ERROR:
            performative = contract_api_pb2.ContractApiMessage.Error_Performative()  # type: ignore
            if msg.is_set("code"):
                performative.code_is_set = True
                code = msg.code
                performative.code = code
            if msg.is_set("message"):
                performative.message_is_set = True
                message = msg.message
                performative.message = message
            data = msg.data
            performative.data = data
            contract_api_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = contract_api_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'ContractApi' message.

        :param obj: the bytes object.
        :return: the 'ContractApi' message.
        """
        message_pb = ProtobufMessage()
        contract_api_pb = contract_api_pb2.ContractApiMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        contract_api_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = contract_api_pb.WhichOneof("performative")
        performative_id = ContractApiMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION:
            ledger_id = contract_api_pb.get_deploy_transaction.ledger_id
            performative_content["ledger_id"] = ledger_id
            contract_id = contract_api_pb.get_deploy_transaction.contract_id
            performative_content["contract_id"] = contract_id
            callable = contract_api_pb.get_deploy_transaction.callable
            performative_content["callable"] = callable
            pb2_kwargs = contract_api_pb.get_deploy_transaction.kwargs
            kwargs = Kwargs.decode(pb2_kwargs)
            performative_content["kwargs"] = kwargs
        elif performative_id == ContractApiMessage.Performative.GET_RAW_TRANSACTION:
            ledger_id = contract_api_pb.get_raw_transaction.ledger_id
            performative_content["ledger_id"] = ledger_id
            contract_id = contract_api_pb.get_raw_transaction.contract_id
            performative_content["contract_id"] = contract_id
            contract_address = contract_api_pb.get_raw_transaction.contract_address
            performative_content["contract_address"] = contract_address
            callable = contract_api_pb.get_raw_transaction.callable
            performative_content["callable"] = callable
            pb2_kwargs = contract_api_pb.get_raw_transaction.kwargs
            kwargs = Kwargs.decode(pb2_kwargs)
            performative_content["kwargs"] = kwargs
        elif performative_id == ContractApiMessage.Performative.GET_RAW_MESSAGE:
            ledger_id = contract_api_pb.get_raw_message.ledger_id
            performative_content["ledger_id"] = ledger_id
            contract_id = contract_api_pb.get_raw_message.contract_id
            performative_content["contract_id"] = contract_id
            contract_address = contract_api_pb.get_raw_message.contract_address
            performative_content["contract_address"] = contract_address
            callable = contract_api_pb.get_raw_message.callable
            performative_content["callable"] = callable
            pb2_kwargs = contract_api_pb.get_raw_message.kwargs
            kwargs = Kwargs.decode(pb2_kwargs)
            performative_content["kwargs"] = kwargs
        elif performative_id == ContractApiMessage.Performative.GET_STATE:
            ledger_id = contract_api_pb.get_state.ledger_id
            performative_content["ledger_id"] = ledger_id
            contract_id = contract_api_pb.get_state.contract_id
            performative_content["contract_id"] = contract_id
            contract_address = contract_api_pb.get_state.contract_address
            performative_content["contract_address"] = contract_address
            callable = contract_api_pb.get_state.callable
            performative_content["callable"] = callable
            pb2_kwargs = contract_api_pb.get_state.kwargs
            kwargs = Kwargs.decode(pb2_kwargs)
            performative_content["kwargs"] = kwargs
        elif performative_id == ContractApiMessage.Performative.STATE:
            pb2_state = contract_api_pb.state.state
            state = State.decode(pb2_state)
            performative_content["state"] = state
        elif performative_id == ContractApiMessage.Performative.RAW_TRANSACTION:
            pb2_raw_transaction = contract_api_pb.raw_transaction.raw_transaction
            raw_transaction = RawTransaction.decode(pb2_raw_transaction)
            performative_content["raw_transaction"] = raw_transaction
        elif performative_id == ContractApiMessage.Performative.RAW_MESSAGE:
            pb2_raw_message = contract_api_pb.raw_message.raw_message
            raw_message = RawMessage.decode(pb2_raw_message)
            performative_content["raw_message"] = raw_message
        elif performative_id == ContractApiMessage.Performative.ERROR:
            if contract_api_pb.error.code_is_set:
                code = contract_api_pb.error.code
                performative_content["code"] = code
            if contract_api_pb.error.message_is_set:
                message = contract_api_pb.error.message
                performative_content["message"] = message
            data = contract_api_pb.error.data
            performative_content["data"] = data
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return ContractApiMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
