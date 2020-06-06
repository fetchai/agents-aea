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

"""Serialization module for tac protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.tac import tac_pb2
from packages.fetchai.protocols.tac.custom_types import ErrorCode
from packages.fetchai.protocols.tac.message import TacMessage


class TacSerializer(Serializer):
    """Serialization for the 'tac' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Tac' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(TacMessage, msg)
        tac_msg = tac_pb2.TacMessage()
        tac_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        tac_msg.dialogue_starter_reference = dialogue_reference[0]
        tac_msg.dialogue_responder_reference = dialogue_reference[1]
        tac_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == TacMessage.Performative.REGISTER:
            performative = tac_pb2.TacMessage.Register_Performative()  # type: ignore
            agent_name = msg.agent_name
            performative.agent_name = agent_name
            tac_msg.register.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.UNREGISTER:
            performative = tac_pb2.TacMessage.Unregister_Performative()  # type: ignore
            tac_msg.unregister.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.TRANSACTION:
            performative = tac_pb2.TacMessage.Transaction_Performative()  # type: ignore
            tx_id = msg.tx_id
            performative.tx_id = tx_id
            tx_sender_addr = msg.tx_sender_addr
            performative.tx_sender_addr = tx_sender_addr
            tx_counterparty_addr = msg.tx_counterparty_addr
            performative.tx_counterparty_addr = tx_counterparty_addr
            amount_by_currency_id = msg.amount_by_currency_id
            performative.amount_by_currency_id.update(amount_by_currency_id)
            tx_sender_fee = msg.tx_sender_fee
            performative.tx_sender_fee = tx_sender_fee
            tx_counterparty_fee = msg.tx_counterparty_fee
            performative.tx_counterparty_fee = tx_counterparty_fee
            quantities_by_good_id = msg.quantities_by_good_id
            performative.quantities_by_good_id.update(quantities_by_good_id)
            tx_nonce = msg.tx_nonce
            performative.tx_nonce = tx_nonce
            tx_sender_signature = msg.tx_sender_signature
            performative.tx_sender_signature = tx_sender_signature
            tx_counterparty_signature = msg.tx_counterparty_signature
            performative.tx_counterparty_signature = tx_counterparty_signature
            tac_msg.transaction.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.CANCELLED:
            performative = tac_pb2.TacMessage.Cancelled_Performative()  # type: ignore
            tac_msg.cancelled.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.GAME_DATA:
            performative = tac_pb2.TacMessage.Game_Data_Performative()  # type: ignore
            amount_by_currency_id = msg.amount_by_currency_id
            performative.amount_by_currency_id.update(amount_by_currency_id)
            exchange_params_by_currency_id = msg.exchange_params_by_currency_id
            performative.exchange_params_by_currency_id.update(
                exchange_params_by_currency_id
            )
            quantities_by_good_id = msg.quantities_by_good_id
            performative.quantities_by_good_id.update(quantities_by_good_id)
            utility_params_by_good_id = msg.utility_params_by_good_id
            performative.utility_params_by_good_id.update(utility_params_by_good_id)
            tx_fee = msg.tx_fee
            performative.tx_fee = tx_fee
            agent_addr_to_name = msg.agent_addr_to_name
            performative.agent_addr_to_name.update(agent_addr_to_name)
            currency_id_to_name = msg.currency_id_to_name
            performative.currency_id_to_name.update(currency_id_to_name)
            good_id_to_name = msg.good_id_to_name
            performative.good_id_to_name.update(good_id_to_name)
            version_id = msg.version_id
            performative.version_id = version_id
            if msg.is_set("info"):
                performative.info_is_set = True
                info = msg.info
                performative.info.update(info)
            tac_msg.game_data.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.TRANSACTION_CONFIRMATION:
            performative = tac_pb2.TacMessage.Transaction_Confirmation_Performative()  # type: ignore
            tx_id = msg.tx_id
            performative.tx_id = tx_id
            amount_by_currency_id = msg.amount_by_currency_id
            performative.amount_by_currency_id.update(amount_by_currency_id)
            quantities_by_good_id = msg.quantities_by_good_id
            performative.quantities_by_good_id.update(quantities_by_good_id)
            tac_msg.transaction_confirmation.CopyFrom(performative)
        elif performative_id == TacMessage.Performative.TAC_ERROR:
            performative = tac_pb2.TacMessage.Tac_Error_Performative()  # type: ignore
            error_code = msg.error_code
            ErrorCode.encode(performative.error_code, error_code)
            if msg.is_set("info"):
                performative.info_is_set = True
                info = msg.info
                performative.info.update(info)
            tac_msg.tac_error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        tac_bytes = tac_msg.SerializeToString()
        return tac_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Tac' message.

        :param obj: the bytes object.
        :return: the 'Tac' message.
        """
        tac_pb = tac_pb2.TacMessage()
        tac_pb.ParseFromString(obj)
        message_id = tac_pb.message_id
        dialogue_reference = (
            tac_pb.dialogue_starter_reference,
            tac_pb.dialogue_responder_reference,
        )
        target = tac_pb.target

        performative = tac_pb.WhichOneof("performative")
        performative_id = TacMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == TacMessage.Performative.REGISTER:
            agent_name = tac_pb.register.agent_name
            performative_content["agent_name"] = agent_name
        elif performative_id == TacMessage.Performative.UNREGISTER:
            pass
        elif performative_id == TacMessage.Performative.TRANSACTION:
            tx_id = tac_pb.transaction.tx_id
            performative_content["tx_id"] = tx_id
            tx_sender_addr = tac_pb.transaction.tx_sender_addr
            performative_content["tx_sender_addr"] = tx_sender_addr
            tx_counterparty_addr = tac_pb.transaction.tx_counterparty_addr
            performative_content["tx_counterparty_addr"] = tx_counterparty_addr
            amount_by_currency_id = tac_pb.transaction.amount_by_currency_id
            amount_by_currency_id_dict = dict(amount_by_currency_id)
            performative_content["amount_by_currency_id"] = amount_by_currency_id_dict
            tx_sender_fee = tac_pb.transaction.tx_sender_fee
            performative_content["tx_sender_fee"] = tx_sender_fee
            tx_counterparty_fee = tac_pb.transaction.tx_counterparty_fee
            performative_content["tx_counterparty_fee"] = tx_counterparty_fee
            quantities_by_good_id = tac_pb.transaction.quantities_by_good_id
            quantities_by_good_id_dict = dict(quantities_by_good_id)
            performative_content["quantities_by_good_id"] = quantities_by_good_id_dict
            tx_nonce = tac_pb.transaction.tx_nonce
            performative_content["tx_nonce"] = tx_nonce
            tx_sender_signature = tac_pb.transaction.tx_sender_signature
            performative_content["tx_sender_signature"] = tx_sender_signature
            tx_counterparty_signature = tac_pb.transaction.tx_counterparty_signature
            performative_content[
                "tx_counterparty_signature"
            ] = tx_counterparty_signature
        elif performative_id == TacMessage.Performative.CANCELLED:
            pass
        elif performative_id == TacMessage.Performative.GAME_DATA:
            amount_by_currency_id = tac_pb.game_data.amount_by_currency_id
            amount_by_currency_id_dict = dict(amount_by_currency_id)
            performative_content["amount_by_currency_id"] = amount_by_currency_id_dict
            exchange_params_by_currency_id = (
                tac_pb.game_data.exchange_params_by_currency_id
            )
            exchange_params_by_currency_id_dict = dict(exchange_params_by_currency_id)
            performative_content[
                "exchange_params_by_currency_id"
            ] = exchange_params_by_currency_id_dict
            quantities_by_good_id = tac_pb.game_data.quantities_by_good_id
            quantities_by_good_id_dict = dict(quantities_by_good_id)
            performative_content["quantities_by_good_id"] = quantities_by_good_id_dict
            utility_params_by_good_id = tac_pb.game_data.utility_params_by_good_id
            utility_params_by_good_id_dict = dict(utility_params_by_good_id)
            performative_content[
                "utility_params_by_good_id"
            ] = utility_params_by_good_id_dict
            tx_fee = tac_pb.game_data.tx_fee
            performative_content["tx_fee"] = tx_fee
            agent_addr_to_name = tac_pb.game_data.agent_addr_to_name
            agent_addr_to_name_dict = dict(agent_addr_to_name)
            performative_content["agent_addr_to_name"] = agent_addr_to_name_dict
            currency_id_to_name = tac_pb.game_data.currency_id_to_name
            currency_id_to_name_dict = dict(currency_id_to_name)
            performative_content["currency_id_to_name"] = currency_id_to_name_dict
            good_id_to_name = tac_pb.game_data.good_id_to_name
            good_id_to_name_dict = dict(good_id_to_name)
            performative_content["good_id_to_name"] = good_id_to_name_dict
            version_id = tac_pb.game_data.version_id
            performative_content["version_id"] = version_id
            if tac_pb.game_data.info_is_set:
                info = tac_pb.game_data.info
                info_dict = dict(info)
                performative_content["info"] = info_dict
        elif performative_id == TacMessage.Performative.TRANSACTION_CONFIRMATION:
            tx_id = tac_pb.transaction_confirmation.tx_id
            performative_content["tx_id"] = tx_id
            amount_by_currency_id = (
                tac_pb.transaction_confirmation.amount_by_currency_id
            )
            amount_by_currency_id_dict = dict(amount_by_currency_id)
            performative_content["amount_by_currency_id"] = amount_by_currency_id_dict
            quantities_by_good_id = (
                tac_pb.transaction_confirmation.quantities_by_good_id
            )
            quantities_by_good_id_dict = dict(quantities_by_good_id)
            performative_content["quantities_by_good_id"] = quantities_by_good_id_dict
        elif performative_id == TacMessage.Performative.TAC_ERROR:
            pb2_error_code = tac_pb.tac_error.error_code
            error_code = ErrorCode.decode(pb2_error_code)
            performative_content["error_code"] = error_code
            if tac_pb.tac_error.info_is_set:
                info = tac_pb.tac_error.info
                info_dict = dict(info)
                performative_content["info"] = info_dict
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return TacMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
