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

from google.protobuf.struct_pb2 import Struct

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer
from aea.protocols.tac import tac_pb2
from aea.protocols.tac.message import TACMessage


def _from_dict_to_pairs(d):
    """Convert a flat dictionary into a list of StrStrPair or StrIntPair."""
    result = []
    items = sorted(d.items(), key=lambda pair: pair[0])
    for key, value in items:
        if type(value) == int:
            pair = tac_pb2.StrIntPair()
        elif type(value) == str:
            pair = tac_pb2.StrStrPair()
        else:
            raise ValueError("Either 'int' or 'str', not {}".format(type(value)))
        pair.first = key
        pair.second = value
        result.append(pair)
    return result


def _from_pairs_to_dict(pairs):
    """Convert a list of StrStrPair or StrIntPair into a flat dictionary."""
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
            tac_msg = tac_pb2.TACAgent.Register()
            tac_msg.agent_name = agent_name
            tac_container.register.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.UNREGISTER:
            tac_msg = tac_pb2.TACAgent.Unregister()
            tac_container.unregister.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TRANSACTION:
            tac_msg = tac_pb2.TACAgent.Transaction()
            tac_msg.transaction_id = msg.get("transaction_id")
            tac_msg.is_sender_buyer = msg.get("is_sender_buyer")
            tac_msg.counterparty = msg.get("counterparty")
            tac_msg.amount = msg.get("amount")
            tac_msg.quantities.extend(_from_dict_to_pairs(msg.get("quantities_by_good_pbk")))
            tac_container.transaction.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.GET_STATE_UPDATE:
            tac_msg = tac_pb2.TACAgent.GetStateUpdate()
            tac_container.get_state_update.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.CANCELLED:
            tac_msg = tac_pb2.TACController.Cancelled()
            tac_container.cancelled.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.GAME_DATA:
            tac_msg = tac_pb2.TACController.GameData()
            tac_msg.money = msg.get("money")
            tac_msg.endowment.extend(msg.get("endowment"))
            tac_msg.utility_params.extend(msg.get("utility_params"))
            tac_msg.nb_agents = msg.get("nb_agents")
            tac_msg.nb_goods = msg.get("nb_goods")
            tac_msg.tx_fee = msg.get("tx_fee")
            tac_msg.agent_pbk_to_name.extend(_from_dict_to_pairs(msg.get("agent_pbk_to_name")))
            tac_msg.good_pbk_to_name.extend(_from_dict_to_pairs(msg.get("good_pbk_to_name")))
            tac_container.game_data.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TRANSACTION_CONFIRMATION:
            tac_msg = tac_pb2.TACController.TransactionConfirmation()
            tac_msg.transaction_id = msg.get("transaction_id")
            tac_container.transaction_confirmation.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.STATE_UPDATE:
            tac_msg = tac_pb2.TACController.StateUpdate()
            game_data_json = msg.get("initial_state")
            game_data = tac_pb2.TACController.GameData()
            game_data.money = game_data_json["money"]
            game_data.endowment.extend(game_data_json["endowment"])
            game_data.utility_params.extend(game_data_json["utility_params"])
            game_data.nb_agents = game_data_json["nb_agents"]
            game_data.nb_goods = game_data_json["nb_goods"]
            game_data.tx_fee = game_data_json["tx_fee"]
            game_data.agent_pbk_to_name.extend(_from_dict_to_pairs(game_data_json["agent_pbk_to_name"]))
            game_data.good_pbk_to_name.extend(_from_dict_to_pairs(game_data_json["good_pbk_to_name"]))

            tac_msg.initial_state.CopyFrom(game_data)

            transactions = []
            for t in msg.get("transactions"):
                tx = tac_pb2.TACAgent.Transaction()
                tx.transaction_id = t.get("transaction_id")
                tx.is_sender_buyer = t.get("is_sender_buyer")
                tx.counterparty = t.get("counterparty")
                tx.amount = t.get("amount")
                tx.quantities.extend(_from_dict_to_pairs(t.get("quantities_by_good_pbk")))
                transactions.append(tx)
            tac_msg.txs.extend(transactions)
            tac_container.state_update.CopyFrom(tac_msg)
        elif tac_type == TACMessage.Type.TAC_ERROR:
            tac_msg = tac_pb2.TACController.Error()
            tac_msg.error_code = msg.get("error_code").value
            if msg.is_set("error_msg"):
                tac_msg.error_msg = msg.get("error_msg")
            if msg.is_set("details"):
                tac_msg.details = Struct()
                tac_msg.details.update(msg.get("details"))

            tac_container.error.CopyFrom(tac_msg)
        else:
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

        new_body = {}
        tac_type = tac_container.WhichOneof("content")

        if tac_type == "register":
            new_body["type"] = TACMessage.Type.REGISTER
            new_body["agent_name"] = tac_container.register.agent_name
        elif tac_type == "unregister":
            new_body["type"] = TACMessage.Type.UNREGISTER
        elif tac_type == "transaction":
            new_body["type"] = TACMessage.Type.TRANSACTION
            new_body["transaction_id"] = tac_container.transaction.transaction_id
            new_body["is_sender_buyer"] = tac_container.transaction.is_sender_buyer
            new_body["counterparty"] = tac_container.transaction.counterparty
            new_body["amount"] = tac_container.transaction.amount
            new_body["quantities_by_good_pbk"] = _from_pairs_to_dict(tac_container.transaction.quantities)
        elif tac_type == "get_state_update":
            new_body["type"] = TACMessage.Type.GET_STATE_UPDATE
        elif tac_type == "cancelled":
            new_body["type"] = TACMessage.Type.CANCELLED
        elif tac_type == "game_data":
            new_body["type"] = TACMessage.Type.GAME_DATA
            new_body["money"] = tac_container.game_data.money
            new_body["endowment"] = list(tac_container.game_data.endowment)
            new_body["utility_params"] = list(tac_container.game_data.utility_params)
            new_body["nb_agents"] = tac_container.game_data.nb_agents
            new_body["nb_goods"] = tac_container.game_data.nb_goods
            new_body["tx_fee"] = tac_container.game_data.tx_fee
            new_body["agent_pbk_to_name"] = _from_pairs_to_dict(tac_container.game_data.agent_pbk_to_name)
            new_body["good_pbk_to_name"] = _from_pairs_to_dict(tac_container.game_data.good_pbk_to_name)
        elif tac_type == "transaction_confirmation":
            new_body["type"] = TACMessage.Type.TRANSACTION_CONFIRMATION
            new_body["transaction_id"] = tac_container.transaction_confirmation.transaction_id
        elif tac_type == "state_update":
            new_body["type"] = TACMessage.Type.STATE_UPDATE
            game_data = dict(
                money=tac_container.state_update.initial_state.money,
                endowment=tac_container.state_update.initial_state.endowment,
                utility_params=tac_container.state_update.initial_state.utility_params,
                nb_agents=tac_container.state_update.initial_state.nb_agents,
                nb_goods=tac_container.state_update.initial_state.nb_goods,
                tx_fee=tac_container.state_update.initial_state.tx_fee,
                agent_pbk_to_name=_from_pairs_to_dict(tac_container.state_update.initial_state.agent_pbk_to_name),
                good_pbk_to_name=_from_pairs_to_dict(tac_container.state_update.initial_state.good_pbk_to_name),
            )
            new_body["initial_state"] = game_data
            transactions = []
            for t in tac_container.state_update.txs:
                tx_json = dict(
                    transaction_id=t.transaction_id,
                    is_sender_buyer=t.is_sender_buyer,
                    counterparty=t.counterparty,
                    amount=t.amount,
                    quantities_by_good_pbk=_from_pairs_to_dict(t.quantities),
                )
                transactions.append(tx_json)
            new_body["transactions"] = transactions
        elif tac_type == "error":
            new_body["type"] = TACMessage.Type.TAC_ERROR
            new_body["error_code"] = TACMessage.ErrorCode(tac_container.error.error_code)
            if tac_container.error.error_msg:
                new_body["error_msg"] = tac_container.error.error_msg
            if tac_container.error.details:
                new_body["details"] = dict(tac_container.error.details)
        else:
            raise ValueError("Type not recognized.")

        new_body["type"] = TACMessage.Type(new_body["type"])
        tac_message = Message(body=new_body)
        return tac_message
