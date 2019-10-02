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

"""This class contains the helpers for FIPA negotiation."""
from typing import Dict, List

from aea.protocols.oef.models import Attribute, DataModel, Description

from fipa_negotiation_skill.dialogues import DialogueLabel


Address = str

SUPPLY_DATAMODEL_NAME = 'supply'
DEMAND_DATAMODEL_NAME = 'demand'


def build_goods_datamodel(good_pbks: List[str], currency: str, is_supply: bool) -> DataModel:
    """
    Build a data model for supply and demand of goods (i.e. for offered or requested goods).

    :param good_pbks: a list of public keys (i.e. identifiers) of the relevant goods.
    :param currency: the currency used for trading.
    :param is_supply: Boolean indicating whether it is a supply or demand data model

    :return: the data model.
    """
    goods_quantities_attributes = [Attribute(good_pbk, Type(int), False)
                                   for good_pbk in good_pbks]
    price_attribute = Attribute(currency, Type(float), False)
    description = SUPPLY_DATAMODEL_NAME if is_supply else DEMAND_DATAMODEL_NAME
    attributes = goods_quantities_attributes + [price_attribute]
    data_model = DataModel(description, attributes)
    return data_model


def build_goods_description(good_pbk_to_quantities: Dict[str, int], is_supply: bool) -> Description:
    """
    Get the service description (good quantities supplied or demanded and their price).

    :param good_pbk_to_quantities: a dictionary mapping the public keys of the goods to the quantities.
    :param is_supply: True if the description is indicating supply, False if it's indicating demand.

    :return: the description to advertise on the Service Directory.
    """
    data_model = build_goods_datamodel(good_pbks=list(good_pbk_to_quantities.keys()), currency='FET', is_supply=is_supply)
    desc = Description(good_pbk_to_quantities, data_model=data_model)
    return desc


def generate_transaction_id(agent_pbk: Address, opponent_pbk: Address, dialogue_label: DialogueLabel, agent_is_seller: bool) -> str:
    """
    Make a transaction id.

    :param agent_pbk: the pbk of the agent.
    :param opponent_pbk: the public key of the opponent.
    :param dialogue_label: the dialogue label
    :param agent_is_seller: boolean indicating if the agent is a seller
    :return: a transaction id
    """
    # the format is {buyer_pbk}_{seller_pbk}_{dialogue_id}_{dialogue_starter_pbk}
    assert opponent_pbk == dialogue_label.dialogue_opponent_pbk
    buyer_pbk, seller_pbk = (opponent_pbk, agent_pbk) if agent_is_seller else (agent_pbk, opponent_pbk)
    transaction_id = "{}_{}_{}_{}".format(buyer_pbk, seller_pbk, dialogue_label.dialogue_id, dialogue_label.dialogue_starter_pbk)
    return transaction_id
