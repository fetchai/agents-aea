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

"""This module contains the strategy class."""

from typing import Any, Dict, Optional, cast

from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.skills.base import Model

DEFAULT_MAX_PRICE = 5
DEFAULT_MAX_BUYER_TX_FEE = 2
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True
DEFAULT_SEARCH_QUERY = {
    "constraint_one": {
        "search_term": "country",
        "search_value": "UK",
        "constraint_type": "==",
    },
    "constraint_two": {
        "search_term": "city",
        "search_value": "Cambridge",
        "constraint_type": "==",
    },
}
DEFAULT_DATA_MODEL_NAME = "location"
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": True},
    "attribute_two": {"name": "city", "type": "str", "is_required": True},
}  # type: Optional[Dict[str, Any]]


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._max_price = kwargs.pop("max_price", DEFAULT_MAX_PRICE)
        self.max_buyer_tx_fee = kwargs.pop("max_buyer_tx_fee", DEFAULT_MAX_BUYER_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self.search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        super().__init__(**kwargs)
        self.is_searching = False

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query(
            [
                Constraint(
                    constraint["search_term"],
                    ConstraintType(
                        constraint["constraint_type"], constraint["search_value"],
                    ),
                )
                for constraint in self.search_query.values()
            ],
            model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return query

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (
            (proposal.values["price"] - proposal.values["seller_tx_fee"] > 0)
            and (proposal.values["price"] <= self._max_price)
            and (proposal.values["currency_id"] == self._currency_id)
            and (proposal.values["ledger_id"] == self._ledger_id)
        )
        return result

    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = proposal.values["price"] + self.max_buyer_tx_fee
            ledger_id = proposal.values["ledger_id"]
            address = cast(str, self.context.agent_addresses.get(ledger_id))
            balance = self.context.ledger_apis.get_balance(ledger_id, address)
            result = balance >= payable
        else:
            result = True
        return result
