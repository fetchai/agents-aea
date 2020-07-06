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

from typing import Any, Dict, Optional

from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.skills.base import Model

DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True

DEFAULT_CURRENCY_ID = "FET"
DEFAULT_MAX_UNIT_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_SERVICE_ID = "generic_service"

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
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": True},
    "attribute_two": {"name": "city", "type": "str", "is_required": True},
}  # type: Optional[Dict[str, Any]]
DEFAULT_DATA_MODEL_NAME = "location"

DEFAULT_MAX_NEGOTIATIONS = 2


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_ID)
        self._max_unit_price = kwargs.pop("max_unit_price", DEFAULT_MAX_UNIT_PRICE)
        self._max_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)

        self._max_negotiations = kwargs.pop(
            "max_negotiations", DEFAULT_MAX_NEGOTIATIONS
        )

        super().__init__(**kwargs)
        self._is_searching = False
        self._balance = 0

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_ledger_tx(self) -> bool:
        """Check whether or not tx are settled on a ledger."""
        return self._is_ledger_tx

    @property
    def is_searching(self) -> bool:
        """Check if the agent is searching."""
        return self._is_searching

    @is_searching.setter
    def is_searching(self, is_searching: bool) -> None:
        """Check if the agent is searching."""
        assert isinstance(is_searching, bool), "Can only set bool on is_searching!"
        self._is_searching = is_searching

    @property
    def balance(self) -> int:
        """Get the balance."""
        return self._balance

    @balance.setter
    def balance(self, balance: int) -> None:
        """Set the balance."""
        self._balance = balance

    @property
    def max_negotiations(self) -> int:
        """Get the maximum number of negotiations the agent can start."""
        return self._max_negotiations

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
                for constraint in self._search_query.values()
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
            all(
                [
                    key in proposal.values
                    for key in [
                        "ledger_id",
                        "currency_id",
                        "price",
                        "service_id",
                        "quantity",
                        "tx_nonce",
                    ]
                ]
            )
            and proposal.values["ledger_id"] == self.ledger_id
            and proposal.values["price"]
            <= proposal.values["quantity"] * self._max_unit_price
            and proposal.values["currency_id"] == self._currency_id
            and proposal.values["service_id"] == self._service_id
            and isinstance(proposal.values["tx_nonce"], str)
            and proposal.values["tx_nonce"] != ""
        )
        return result

    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = proposal.values.get("price", 0) + self._max_tx_fee
            result = self.balance >= payable
        else:
            result = True
        return result

    def terms_from_proposal(
        self, proposal: Description, counterparty_address: Address
    ) -> Terms:
        """
        Get the terms from a proposal.

        :param proposal: the proposal
        :return: terms
        """
        buyer_address = self.context.agent_addresses[proposal.values["ledger_id"]]
        terms = Terms(
            ledger_id=proposal.values["ledger_id"],
            sender_address=buyer_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={
                proposal.values["currency_id"]: -proposal.values["price"]
            },
            quantities_by_good_id={
                proposal.values["service_id"]: proposal.values["quantity"]
            },
            is_sender_payable_tx_fee=True,
            nonce=proposal.values["tx_nonce"],
            fee_by_currency_id={proposal.values["currency_id"]: self._max_tx_fee},
        )
        return terms
