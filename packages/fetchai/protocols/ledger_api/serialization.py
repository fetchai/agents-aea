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

"""Serialization module for ledger_api protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.ledger_api import ledger_api_pb2
from packages.fetchai.protocols.ledger_api.custom_types import RawTransaction
from packages.fetchai.protocols.ledger_api.custom_types import SignedTransaction
from packages.fetchai.protocols.ledger_api.custom_types import Terms
from packages.fetchai.protocols.ledger_api.custom_types import TransactionDigest
from packages.fetchai.protocols.ledger_api.custom_types import TransactionReceipt
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage


class LedgerApiSerializer(Serializer):
    """Serialization for the 'ledger_api' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'LedgerApi' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(LedgerApiMessage, msg)
        ledger_api_msg = ledger_api_pb2.LedgerApiMessage()
        ledger_api_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        ledger_api_msg.dialogue_starter_reference = dialogue_reference[0]
        ledger_api_msg.dialogue_responder_reference = dialogue_reference[1]
        ledger_api_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == LedgerApiMessage.Performative.GET_BALANCE:
            performative = ledger_api_pb2.LedgerApiMessage.Get_Balance_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            address = msg.address
            performative.address = address
            ledger_api_msg.get_balance.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.GET_RAW_TRANSACTION:
            performative = ledger_api_pb2.LedgerApiMessage.Get_Raw_Transaction_Performative()  # type: ignore
            terms = msg.terms
            Terms.encode(performative.terms, terms)
            ledger_api_msg.get_raw_transaction.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION:
            performative = ledger_api_pb2.LedgerApiMessage.Send_Signed_Transaction_Performative()  # type: ignore
            signed_transaction = msg.signed_transaction
            SignedTransaction.encode(
                performative.signed_transaction, signed_transaction
            )
            ledger_api_msg.send_signed_transaction.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT:
            performative = ledger_api_pb2.LedgerApiMessage.Get_Transaction_Receipt_Performative()  # type: ignore
            transaction_digest = msg.transaction_digest
            TransactionDigest.encode(
                performative.transaction_digest, transaction_digest
            )
            ledger_api_msg.get_transaction_receipt.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.BALANCE:
            performative = ledger_api_pb2.LedgerApiMessage.Balance_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            balance = msg.balance
            performative.balance = balance
            ledger_api_msg.balance.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.RAW_TRANSACTION:
            performative = ledger_api_pb2.LedgerApiMessage.Raw_Transaction_Performative()  # type: ignore
            raw_transaction = msg.raw_transaction
            RawTransaction.encode(performative.raw_transaction, raw_transaction)
            ledger_api_msg.raw_transaction.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.TRANSACTION_DIGEST:
            performative = ledger_api_pb2.LedgerApiMessage.Transaction_Digest_Performative()  # type: ignore
            transaction_digest = msg.transaction_digest
            TransactionDigest.encode(
                performative.transaction_digest, transaction_digest
            )
            ledger_api_msg.transaction_digest.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.TRANSACTION_RECEIPT:
            performative = ledger_api_pb2.LedgerApiMessage.Transaction_Receipt_Performative()  # type: ignore
            transaction_receipt = msg.transaction_receipt
            TransactionReceipt.encode(
                performative.transaction_receipt, transaction_receipt
            )
            ledger_api_msg.transaction_receipt.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.ERROR:
            performative = ledger_api_pb2.LedgerApiMessage.Error_Performative()  # type: ignore
            code = msg.code
            performative.code = code
            if msg.is_set("message"):
                performative.message_is_set = True
                message = msg.message
                performative.message = message
            if msg.is_set("data"):
                performative.data_is_set = True
                data = msg.data
                performative.data = data
            ledger_api_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        ledger_api_bytes = ledger_api_msg.SerializeToString()
        return ledger_api_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'LedgerApi' message.

        :param obj: the bytes object.
        :return: the 'LedgerApi' message.
        """
        ledger_api_pb = ledger_api_pb2.LedgerApiMessage()
        ledger_api_pb.ParseFromString(obj)
        message_id = ledger_api_pb.message_id
        dialogue_reference = (
            ledger_api_pb.dialogue_starter_reference,
            ledger_api_pb.dialogue_responder_reference,
        )
        target = ledger_api_pb.target

        performative = ledger_api_pb.WhichOneof("performative")
        performative_id = LedgerApiMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == LedgerApiMessage.Performative.GET_BALANCE:
            ledger_id = ledger_api_pb.get_balance.ledger_id
            performative_content["ledger_id"] = ledger_id
            address = ledger_api_pb.get_balance.address
            performative_content["address"] = address
        elif performative_id == LedgerApiMessage.Performative.GET_RAW_TRANSACTION:
            pb2_terms = ledger_api_pb.get_raw_transaction.terms
            terms = Terms.decode(pb2_terms)
            performative_content["terms"] = terms
        elif performative_id == LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION:
            pb2_signed_transaction = (
                ledger_api_pb.send_signed_transaction.signed_transaction
            )
            signed_transaction = SignedTransaction.decode(pb2_signed_transaction)
            performative_content["signed_transaction"] = signed_transaction
        elif performative_id == LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT:
            pb2_transaction_digest = (
                ledger_api_pb.get_transaction_receipt.transaction_digest
            )
            transaction_digest = TransactionDigest.decode(pb2_transaction_digest)
            performative_content["transaction_digest"] = transaction_digest
        elif performative_id == LedgerApiMessage.Performative.BALANCE:
            ledger_id = ledger_api_pb.balance.ledger_id
            performative_content["ledger_id"] = ledger_id
            balance = ledger_api_pb.balance.balance
            performative_content["balance"] = balance
        elif performative_id == LedgerApiMessage.Performative.RAW_TRANSACTION:
            pb2_raw_transaction = ledger_api_pb.raw_transaction.raw_transaction
            raw_transaction = RawTransaction.decode(pb2_raw_transaction)
            performative_content["raw_transaction"] = raw_transaction
        elif performative_id == LedgerApiMessage.Performative.TRANSACTION_DIGEST:
            pb2_transaction_digest = ledger_api_pb.transaction_digest.transaction_digest
            transaction_digest = TransactionDigest.decode(pb2_transaction_digest)
            performative_content["transaction_digest"] = transaction_digest
        elif performative_id == LedgerApiMessage.Performative.TRANSACTION_RECEIPT:
            pb2_transaction_receipt = (
                ledger_api_pb.transaction_receipt.transaction_receipt
            )
            transaction_receipt = TransactionReceipt.decode(pb2_transaction_receipt)
            performative_content["transaction_receipt"] = transaction_receipt
        elif performative_id == LedgerApiMessage.Performative.ERROR:
            code = ledger_api_pb.error.code
            performative_content["code"] = code
            if ledger_api_pb.error.message_is_set:
                message = ledger_api_pb.error.message
                performative_content["message"] = message
            if ledger_api_pb.error.data_is_set:
                data = ledger_api_pb.error.data
                performative_content["data"] = data
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return LedgerApiMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
