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

import collections
import copy
from typing import Dict, List, Union, cast

from web3 import Web3

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
from aea.mail.base import Address

SUPPLY_DATAMODEL_NAME = "supply"
DEMAND_DATAMODEL_NAME = "demand"
PREFIX = "pre_"


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
    currency_attribute = Attribute(
        "currency_id", str, True, "The currency for pricing and transacting the goods."
    )
    price_attribute = Attribute(
        "price", int, False, "The price of the goods in the currency."
    )
    seller_tx_fee_attribute = Attribute(
        "seller_tx_fee",
        int,
        False,
        "The transaction fee payable by the seller in the currency.",
    )
    buyer_tx_fee_attribute = Attribute(
        "buyer_tx_fee",
        int,
        False,
        "The transaction fee payable by the buyer in the currency.",
    )
    tx_nonce_attribute = Attribute(
        "tx_nonce", str, False, "The nonce to distinguish identical descriptions."
    )
    description = SUPPLY_DATAMODEL_NAME if is_supply else DEMAND_DATAMODEL_NAME
    attributes = good_quantities_attributes + [
        currency_attribute,
        price_attribute,
        seller_tx_fee_attribute,
        buyer_tx_fee_attribute,
        tx_nonce_attribute,
    ]
    data_model = DataModel(description, attributes)
    return data_model


def build_goods_description(
    good_id_to_quantities: Dict[str, int],
    currency_id: str,
    is_supply: bool,
    is_search_description: bool,
) -> Description:
    """
    Get the service description (good quantities supplied or demanded and their price).

    :param good_id_to_quantities: a dictionary mapping the ids of the goods to the quantities.
    :param currency_id: the currency used for pricing and transacting.
    :param is_supply: True if the description is indicating supply, False if it's indicating demand.
    :param is_search_description: Whether or not the description is used for search

    :return: the description to advertise on the Service Directory.
    """
    _good_id_to_quantities = copy.copy(good_id_to_quantities)
    if is_search_description:
        # the OEF does not accept attribute names consisting of integers only
        _good_id_to_quantities = {
            PREFIX + good_id: quantity
            for good_id, quantity in _good_id_to_quantities.items()
        }
    data_model = _build_goods_datamodel(
        good_ids=list(_good_id_to_quantities.keys()), is_supply=is_supply
    )
    values = cast(Dict[str, Union[int, str]], _good_id_to_quantities)
    values.update({"currency_id": currency_id})
    desc = Description(values, data_model=data_model)
    return desc


def build_goods_query(
    good_ids: List[str],
    currency_id: str,
    is_searching_for_sellers: bool,
    is_search_query: bool,
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
    :param is_searching_for_sellers: Boolean indicating whether the query is for sellers (supply) or buyers (demand).
    :param is_search_query: whether or not the query is used for search on OEF

    :return: the query
    """
    if is_search_query:
        # the OEF does not accept attribute names consisting of integers only
        good_ids = [PREFIX + good_id for good_id in good_ids]

    data_model = _build_goods_datamodel(
        good_ids=good_ids, is_supply=is_searching_for_sellers
    )
    constraints = [Constraint(good_id, ConstraintType(">=", 1)) for good_id in good_ids]
    constraints.append(Constraint("currency_id", ConstraintType("==", currency_id)))
    constraint_expr = cast(List[ConstraintExpr], constraints)

    if len(good_ids) > 1:
        constraint_expr = [Or(constraint_expr)]

    query = Query(constraint_expr, model=data_model)
    return query


def _get_hash(
    tx_sender_addr: Address,
    tx_counterparty_addr: Address,
    good_ids: List[int],
    sender_supplied_quantities: List[int],
    counterparty_supplied_quantities: List[int],
    tx_amount: int,
    tx_nonce: int,
) -> bytes:
    """
    Generate a hash from transaction information.

    :param tx_sender_addr: the sender address
    :param tx_counterparty_addr: the counterparty address
    :param good_ids: the list of good ids
    :param sender_supplied_quantities: the quantities supplied by the sender (must all be positive)
    :param counterparty_supplied_quantities: the quantities supplied by the counterparty (must all be positive)
    :param tx_amount: the amount of the transaction
    :param tx_nonce: the nonce of the transaction
    :return: the hash
    """
    aggregate_hash = Web3.keccak(
        b"".join(
            [
                good_ids[0].to_bytes(32, "big"),
                sender_supplied_quantities[0].to_bytes(32, "big"),
                counterparty_supplied_quantities[0].to_bytes(32, "big"),
            ]
        )
    )
    for idx, good_id in enumerate(good_ids):
        if not idx == 0:
            aggregate_hash = Web3.keccak(
                b"".join(
                    [
                        aggregate_hash,
                        good_id.to_bytes(32, "big"),
                        sender_supplied_quantities[idx].to_bytes(32, "big"),
                        counterparty_supplied_quantities[idx].to_bytes(32, "big"),
                    ]
                )
            )

    m_list = []  # type: List[bytes]
    m_list.append(tx_sender_addr.encode("utf-8"))
    m_list.append(tx_counterparty_addr.encode("utf-8"))
    m_list.append(aggregate_hash)
    m_list.append(tx_amount.to_bytes(32, "big"))
    m_list.append(tx_nonce.to_bytes(32, "big"))
    return Web3.keccak(b"".join(m_list))


def tx_hash_from_values(
    tx_sender_addr: str,
    tx_counterparty_addr: str,
    tx_quantities_by_good_id: Dict[str, int],
    tx_amount_by_currency_id: Dict[str, int],
    tx_nonce: int,
) -> bytes:
    """
    Get the hash for a transaction based on the transaction message.

    :param tx_message: the transaction message
    :return: the hash
    """
    _tx_quantities_by_good_id = {
        int(good_id): quantity for good_id, quantity in tx_quantities_by_good_id.items()
    }  # type: Dict[int, int]
    ordered = collections.OrderedDict(sorted(_tx_quantities_by_good_id.items()))
    good_uids = []  # type: List[int]
    sender_supplied_quantities = []  # type: List[int]
    counterparty_supplied_quantities = []  # type: List[int]
    for good_uid, quantity in ordered.items():
        good_uids.append(good_uid)
        if quantity >= 0:
            sender_supplied_quantities.append(quantity)
            counterparty_supplied_quantities.append(0)
        else:
            sender_supplied_quantities.append(0)
            counterparty_supplied_quantities.append(-quantity)
    assert len(tx_amount_by_currency_id) == 1
    for amount in tx_amount_by_currency_id.values():
        tx_amount = amount if amount >= 0 else 0
    tx_hash = _get_hash(
        tx_sender_addr=tx_sender_addr,
        tx_counterparty_addr=tx_counterparty_addr,
        good_ids=good_uids,
        sender_supplied_quantities=sender_supplied_quantities,
        counterparty_supplied_quantities=counterparty_supplied_quantities,
        tx_amount=tx_amount,
        tx_nonce=tx_nonce,
    )
    return tx_hash
