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
        elif performative_id == LedgerApiMessage.Performative.SEND_SIGNED_TX:
            performative = ledger_api_pb2.LedgerApiMessage.Send_Signed_Tx_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            signed_tx = msg.signed_tx
            performative.signed_tx = signed_tx
            ledger_api_msg.send_signed_tx.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.GET_TX_RECEIPT:
            performative = ledger_api_pb2.LedgerApiMessage.Get_Tx_Receipt_Performative()  # type: ignore
            ledger_id = msg.ledger_id
            performative.ledger_id = ledger_id
            tx_digest = msg.tx_digest
            performative.tx_digest = tx_digest
            ledger_api_msg.get_tx_receipt.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.BALANCE:
            performative = ledger_api_pb2.LedgerApiMessage.Balance_Performative()  # type: ignore
            amount = msg.amount
            performative.amount = amount
            ledger_api_msg.balance.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.TX_DIGEST:
            performative = ledger_api_pb2.LedgerApiMessage.Tx_Digest_Performative()  # type: ignore
            digest = msg.digest
            performative.digest = digest
            ledger_api_msg.tx_digest.CopyFrom(performative)
        elif performative_id == LedgerApiMessage.Performative.TX_RECEIPT:
            performative = ledger_api_pb2.LedgerApiMessage.Tx_Receipt_Performative()  # type: ignore
            data = msg.data
            performative.data.update(data)
            ledger_api_msg.tx_receipt.CopyFrom(performative)
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
        elif performative_id == LedgerApiMessage.Performative.SEND_SIGNED_TX:
            ledger_id = ledger_api_pb.send_signed_tx.ledger_id
            performative_content["ledger_id"] = ledger_id
            signed_tx = ledger_api_pb.send_signed_tx.signed_tx
            performative_content["signed_tx"] = signed_tx
        elif performative_id == LedgerApiMessage.Performative.GET_TX_RECEIPT:
            ledger_id = ledger_api_pb.get_tx_receipt.ledger_id
            performative_content["ledger_id"] = ledger_id
            tx_digest = ledger_api_pb.get_tx_receipt.tx_digest
            performative_content["tx_digest"] = tx_digest
        elif performative_id == LedgerApiMessage.Performative.BALANCE:
            amount = ledger_api_pb.balance.amount
            performative_content["amount"] = amount
        elif performative_id == LedgerApiMessage.Performative.TX_DIGEST:
            digest = ledger_api_pb.tx_digest.digest
            performative_content["digest"] = digest
        elif performative_id == LedgerApiMessage.Performative.TX_RECEIPT:
            data = ledger_api_pb.tx_receipt.data
            data_dict = dict(data)
            performative_content["data"] = data_dict
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return LedgerApiMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
