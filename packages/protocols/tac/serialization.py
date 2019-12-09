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

"""Serialization for the TAC protocol."""

import sys
from typing import Any, Dict, TYPE_CHECKING

from aea.protocols.base import Message
from aea.protocols.base import Serializer

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.tac import tac_pb2
    from packages.protocols.tac.message import TACMessage
else:
    import tac_protocol.tac_pb2 as tac_pb2  # pragma: no cover
    from tac_protocol.message import TACMessage  # pragma: no cover


def _from_dict_to_pairs(d):
    """Convert a flat dictionary into a list of StrStrPair or StrIntPair."""
    result = []
    items = sorted(d.items(), key=lambda pair: pair[0])
    for key, value in items:
        if type(value) == int:
            pair = tac_pb2.StrIntPair()
        elif type(value) == str:
            pair = tac_pb2.StrStrPair()
        elif type(value) == float:
            pair = tac_pb2.StrFloatPair()
        else:
            raise ValueError("Either 'int' or 'str' or 'float', not {}".format(type(value)))
        pair.first = key
        pair.second = value
        result.append(pair)
    return result


def _from_pairs_to_dict(pairs):
    """Convert a list of StrStrPair or StrIntPair or StrFloatPair into a flat dictionary."""
    result = {}
    for pair in pairs:
        key = pair.first
        value = pair.second
        result[key] = value
    return result


class TACSerializer(Serializer):
    """Serialization for the TAC protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Decode the message.

        :param msg: the message object
        :return: the bytes
        """
        tac_type = TACMessage.Type(msg.get("type"))
        tac_container = tac_pb2.TACMessage()

        if tac_type == TACMessage.Type.REGISTER:
            agent_name = msg.get("agent_name")
            tac_msg = tac_pb2.TACAgent.Register()  # type: ignore
            tac_msg.agent_name = agent_name
            tac_container.register.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.UNREGISTER:
            tac_msg = tac_pb2.TACAgent.Unregister()  # type: ignore
            tac_container.unregister.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TRANSACTION:
            tac_msg = tac_pb2.TACAgent.Transaction()  # type: ignore
            tac_msg.transaction_id = msg.get("transaction_id")
            tac_msg.counterparty = msg.get("counterparty")
            tac_msg.amount_by_currency.extend(_from_dict_to_pairs(msg.get("amount_by_currency")))
            tac_msg.sender_tx_fee = msg.get("sender_tx_fee")
            tac_msg.counterparty_tx_fee = msg.get("counterparty_tx_fee")
            tac_msg.quantities_by_good_pbk.extend(_from_dict_to_pairs(msg.get("quantities_by_good_pbk")))
            tac_container.transaction.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.GET_STATE_UPDATE:
            tac_msg = tac_pb2.TACAgent.GetStateUpdate()  # type: ignore
            tac_container.get_state_update.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.CANCELLED:
            tac_msg = tac_pb2.TACController.Cancelled()  # type: ignore
            tac_container.cancelled.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.GAME_DATA:
            tac_msg = tac_pb2.TACController.GameData()  # type: ignore
            tac_msg.amount_by_currency.extend(_from_dict_to_pairs(msg.get("amount_by_currency")))
            tac_msg.exchange_params_by_currency.extend(_from_dict_to_pairs(msg.get("exchange_params_by_currency")))
            tac_msg.quantities_by_good_pbk.extend(_from_dict_to_pairs(msg.get("quantities_by_good_pbk")))
            tac_msg.utility_params_by_good_pbk.extend(_from_dict_to_pairs(msg.get("utility_params_by_good_pbk")))
            tac_msg.tx_fee = msg.get("tx_fee")
            tac_msg.agent_pbk_to_name.extend(_from_dict_to_pairs(msg.get("agent_pbk_to_name")))
            tac_msg.good_pbk_to_name.extend(_from_dict_to_pairs(msg.get("good_pbk_to_name")))
            tac_msg.version_id = msg.get("version_id")
            tac_container.game_data.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TRANSACTION_CONFIRMATION:
            tac_msg = tac_pb2.TACController.TransactionConfirmation()  # type: ignore
            tac_msg.transaction_id = msg.get("transaction_id")
            tac_msg.amount_by_currency.extend(_from_dict_to_pairs(msg.get("amount_by_currency")))
            tac_msg.quantities_by_good_pbk.extend(_from_dict_to_pairs(msg.get("quantities_by_good_pbk")))
            tac_container.transaction_confirmation.CopyFrom(tac_msg)
        # elif tac_type == TACMessage.Type.STATE_UPDATE:
        #     tac_msg = tac_pb2.TACController.StateUpdate()  # type: ignore
        #     game_data_json = msg.get("game_data")
        #     game_data = tac_pb2.TACController.GameData()  # type: ignore
        #     game_data.amount_by_currency.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["amount_by_currency"])))  # type: ignore
        #     game_data.exchange_params_by_currency.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["exchange_params_by_currency"])))  # type: ignore
        #     game_data.quantities_by_good_pbk.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["quantities_by_good_pbk"])))  # type: ignore
        #     game_data.utility_params_by_good_pbk.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["utility_params_by_good_pbk"])))  # type: ignore
        #     game_data.tx_fee = game_data_json["tx_fee"]  # type: ignore
        #     game_data.agent_pbk_to_name.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["agent_pbk_to_name"])))  # type: ignore
        #     game_data.good_pbk_to_name.extend(_from_dict_to_pairs(cast(Dict[str, str], game_data_json["good_pbk_to_name"])))  # type: ignore

        #     tac_msg.initial_state.CopyFrom(game_data)

        #     transactions = []
        #     msg_transactions = cast(List[Any], msg.get("transactions"))
        #     for t in msg_transactions:
        #         tx = tac_pb2.TACAgent.Transaction()  # type: ignore
        #         tx.transaction_id = t.get("transaction_id")
        #         tx.counterparty = t.get("counterparty")
        #         tx.amount_by_currency.extend(_from_dict_to_pairs(t.get("amount_by_currency")))
        #         tx.sender_tx_fee = t.get("sender_tx_fee")
        #         tx.counterparty_tx_fee = t.get("counterparty_tx_fee")
        #         tx.quantities_by_good_pbk.extend(_from_dict_to_pairs(t.get("quantities_by_good_pbk")))
        #         transactions.append(tx)
        #     tac_msg.txs.extend(transactions)
        #     tac_container.state_update.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TAC_ERROR:  # pragma: no cover
            tac_msg = tac_pb2.TACController.Error()  # type: ignore
            tac_msg.error_code = TACMessage.ErrorCode(msg.get("error_code")).value
            if msg.is_set("info"):
                tac_msg.info.extend(_from_dict_to_pairs(msg.get("info")))
            tac_container.error.CopyFrom(tac_msg)
        else:  # pragma: no cover
            raise ValueError("Type not recognized: {}.".format(tac_type))

        tac_message_bytes = tac_container.SerializeToString()
        return tac_message_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode the message.

        :param obj: the bytes object
        :return: the message
        """
        tac_container = tac_pb2.TACMessage()
        tac_container.ParseFromString(obj)

        new_body = {}  # type: Dict[str, Any]
        tac_type = tac_container.WhichOneof("content")

        if tac_type == "register":
            new_body["type"] = TACMessage.Type.REGISTER
            new_body["agent_name"] = tac_container.register.agent_name
        elif tac_type == "unregister":
            new_body["type"] = TACMessage.Type.UNREGISTER
        elif tac_type == "transaction":
            new_body["type"] = TACMessage.Type.TRANSACTION
            new_body["transaction_id"] = tac_container.transaction.transaction_id
            new_body["counterparty"] = tac_container.transaction.counterparty
            new_body["amount_by_currency"] = _from_pairs_to_dict(tac_container.transaction.amount_by_currency)
            new_body["sender_tx_fee"] = tac_container.transaction.sender_tx_fee
            new_body["counterparty_tx_fee"] = tac_container.transaction.counterparty_tx_fee
            new_body["quantities_by_good_pbk"] = _from_pairs_to_dict(tac_container.transaction.quantities_by_good_pbk)
        elif tac_type == "get_state_update":
            new_body["type"] = TACMessage.Type.GET_STATE_UPDATE
        elif tac_type == "cancelled":
            new_body["type"] = TACMessage.Type.CANCELLED
        elif tac_type == "game_data":
            new_body["type"] = TACMessage.Type.GAME_DATA
            new_body["amount_by_currency"] = _from_pairs_to_dict(tac_container.game_data.amount_by_currency)
            new_body["exchange_params_by_currency"] = _from_pairs_to_dict(tac_container.game_data.exchange_params_by_currency)
            new_body["quantities_by_good_pbk"] = _from_pairs_to_dict(tac_container.game_data.quantities_by_good_pbk)
            new_body["utility_params_by_good_pbk"] = _from_pairs_to_dict(tac_container.game_data.utility_params_by_good_pbk)
            new_body["tx_fee"] = tac_container.game_data.tx_fee
            new_body["agent_pbk_to_name"] = _from_pairs_to_dict(tac_container.game_data.agent_pbk_to_name)
            new_body["good_pbk_to_name"] = _from_pairs_to_dict(tac_container.game_data.good_pbk_to_name)
            new_body["version_id"] = tac_container.game_data.version_id
        elif tac_type == "transaction_confirmation":
            new_body["type"] = TACMessage.Type.TRANSACTION_CONFIRMATION
            new_body["transaction_id"] = tac_container.transaction_confirmation.transaction_id
            new_body["amount_by_currency"] = _from_pairs_to_dict(tac_container.transaction_confirmation.amount_by_currency)
            new_body["quantities_by_good_pbk"] = _from_pairs_to_dict(tac_container.transaction_confirmation.quantities_by_good_pbk)
        # elif tac_type == "state_update":
        #     new_body["type"] = TACMessage.Type.STATE_UPDATE
        #     game_data = dict(
        #         amount_by_currency=_from_pairs_to_dict(tac_container.state_update.game_data.amount_by_currency),
        #         exchange_params_by_currency=_from_pairs_to_dict(tac_container.state_update.game_data.exchange_params_by_currency),
        #         quantities_by_good_pbk=_from_pairs_to_dict(tac_container.state_update.game_data.quantities_by_good_pbk),
        #         utility_params_by_good_pbk=_from_pairs_to_dict(tac_container.state_update.game_data.utility_params_by_good_pbk),
        #         tx_fee=tac_container.state_update.game_data.tx_fee,
        #         agent_pbk_to_name=_from_pairs_to_dict(tac_container.state_update.game_data.agent_pbk_to_name),
        #         good_pbk_to_name=_from_pairs_to_dict(tac_container.state_update.game_data.good_pbk_to_name),
        #         version_id=tac_container.state_update.game_data.version_id
        #     )
        #     new_body["game_data"] = game_data
        #     transactions = []
        #     for transaction in tac_container.state_update.transactions:
        #         tx_json = dict(
        #             transaction_id=transaction.transaction_id,
        #             counterparty=transaction.counterparty,
        #             amount_by_currency=_from_pairs_to_dict(transaction.amount_by_currency),
        #             sender_tx_fee=transaction.sender_tx_fee,
        #             counterparty_tx_fee=transaction.counterparty_tx_fee,
        #             quantities_by_good_pbk=_from_pairs_to_dict(transaction.quantities_by_good_pbk),
        #         )
        #         transactions.append(tx_json)
        #     new_body["transactions"] = transactions
        elif tac_type == "error":   # pragma: no cover
            new_body["type"] = TACMessage.Type.TAC_ERROR
            new_body["error_code"] = TACMessage.ErrorCode(tac_container.error.error_code)
            if tac_container.error.error_msg:
                new_body["error_msg"] = tac_container.error.error_msg
            if tac_container.error.details:
                new_body["details"] = dict(tac_container.error.details)
        else:  # pragma: no cover
            if tac_container.error.info:
                new_body["info"] = _from_pairs_to_dict(tac_container.error.info)

        tac_type = TACMessage.Type(new_body["type"])
        new_body["type"] = tac_type
        tac_message = TACMessage(tac_type=tac_type, body=new_body)
        return tac_message
