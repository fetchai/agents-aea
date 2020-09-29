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

import copy
from typing import Dict, List, Union, cast

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintExpr,
    ConstraintType,
    DataModel,
    Description,
    Or,
    Query,
)


SUPPLY_DATAMODEL_NAME = "supply"
DEMAND_DATAMODEL_NAME = "demand"


def _build_goods_datamodel(good_ids: List[str], is_supply: bool) -> DataModel:
    """
    Build a data model for supply and demand of goods (i.e. for offered or requested goods).

    :param good_ids: a list of ids (i.e. identifiers) of the relevant goods.
    :param is_supply: Boolean indicating whether it is a supply or demand data model

    :return: the data model.
    """
    good_quantities_attributes = [
        Attribute(good_id, int, True, "A good on offer.") for good_id in good_ids
    ]
    ledger_id_attribute = Attribute(
        "ledger_id", str, True, "The ledger for transacting."
    )
    currency_attribute = Attribute(
        "currency_id", str, True, "The currency for pricing and transacting the goods."
    )
    price_attribute = Attribute(
        "price", int, False, "The price of the goods in the currency."
    )
    fee_attribute = Attribute(
        "fee", int, False, "The transaction fee payable by the buyer in the currency.",
    )
    nonce_attribute = Attribute(
        "nonce", str, False, "The nonce to distinguish identical descriptions."
    )
    description = SUPPLY_DATAMODEL_NAME if is_supply else DEMAND_DATAMODEL_NAME
    attributes = good_quantities_attributes + [
        ledger_id_attribute,
        currency_attribute,
        price_attribute,
        fee_attribute,
        nonce_attribute,
    ]
    data_model = DataModel(description, attributes)
    return data_model


def build_goods_description(
    quantities_by_good_id: Dict[str, int],
    currency_id: str,
    ledger_id: str,
    is_supply: bool,
) -> Description:
    """
    Get the service description (good quantities supplied or demanded and their price).

    :param quantities_by_good_id: a dictionary mapping the ids of the goods to the quantities.
    :param currency_id: the currency used for pricing and transacting.
    :param ledger_id: the ledger used for transacting.
    :param is_supply: True if the description is indicating supply, False if it's indicating demand.

    :return: the description to advertise on the Service Directory.
    """
    data_model = _build_goods_datamodel(
        good_ids=list(quantities_by_good_id.keys()), is_supply=is_supply
    )
    values = cast(Dict[str, Union[int, str]], copy.copy(quantities_by_good_id))
    values.update({"currency_id": currency_id})
    values.update({"ledger_id": ledger_id})
    desc = Description(values, data_model=data_model)
    return desc


def build_goods_query(
    good_ids: List[str],
    currency_id: str,
    ledger_id: str,
    is_searching_for_sellers: bool,
) -> Query:
    """
    Build buyer or seller search query.

    Specifically, build the search query
        - to look for sellers if the agent is a buyer, or
        - to look for buyers if the agent is a seller.

    In particular, if the agent is a buyer and the demanded good ids are {'tac_good_0', 'tac_good_2', 'tac_good_3'}, the resulting constraint expression is:

        tac_good_0 >= 1 OR tac_good_2 >= 1 OR tac_good_3 >= 1

    That is, the OEF will return all the sellers that have at least one of the good in the query
    (assuming that the sellers are registered with the data model specified).

    :param good_ids: the list of good ids to put in the query
    :param currency_id: the currency used for pricing and transacting.
    :param ledger_id: the ledger used for transacting.
    :param is_searching_for_sellers: Boolean indicating whether the query is for sellers (supply) or buyers (demand).

    :return: the query
    """
    data_model = _build_goods_datamodel(
        good_ids=good_ids, is_supply=is_searching_for_sellers
    )
    constraints = [Constraint(good_id, ConstraintType(">=", 1)) for good_id in good_ids]
    constraints.append(Constraint("currency_id", ConstraintType("==", currency_id)))
    constraints.append(Constraint("ledger_id", ConstraintType("==", ledger_id)))
    constraint_expr = cast(List[ConstraintExpr], constraints)

    if len(good_ids) > 1:
        constraint_expr = [Or(constraint_expr)]

    query = Query(constraint_expr, model=data_model)
    return query
