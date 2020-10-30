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

import uuid
from typing import Any, Dict, Optional, Tuple

from aea.common import Address
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    SIMPLE_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location, Query
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model


DEFAULT_LEDGER_ID = DEFAULT_LEDGER
DEFAULT_IS_LEDGER_TX = True

DEFAULT_CURRENCY_ID = "FET"
DEFAULT_UNIT_PRICE = 4
DEFAULT_SERVICE_ID = "generic_service"

DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "seller_service", "value": "generic_service"}

DEFAULT_HAS_DATA_SOURCE = False
DEFAULT_DATA_FOR_SALE = {
    "some_generic_data_key": "some_generic_data_value"
}  # type: Optional[Dict[str, Any]]


class GenericStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)

        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_ID)
        self._unit_price = kwargs.pop("unit_price", DEFAULT_UNIT_PRICE)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._remove_service_data = {"key": self._set_service_data["key"]}
        self._simple_service_data = {
            self._set_service_data["key"]: self._set_service_data["value"]
        }

        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)
        data_for_sale_ordered = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)
        data_for_sale = {
            str(key): str(value) for key, value in data_for_sale_ordered.items()
        }

        super().__init__(**kwargs)
        enforce(
            self.context.agent_addresses.get(self._ledger_id, None) is not None,
            "Wallet does not contain cryptos for provided ledger id.",
        )

        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()  # pragma: nocover
        else:
            self._data_for_sale = data_for_sale
        self._sale_quantity = len(data_for_sale)

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_ledger_tx(self) -> bool:
        """Check whether or not tx are settled on a ledger."""
        return self._is_ledger_tx

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_service_description(self) -> Description:
        """
        Get the simple service description.

        :return: a description of the offered services
        """
        description = Description(
            self._simple_service_data, data_model=SIMPLE_SERVICE_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        return query.check(self.get_service_description())

    def generate_proposal_terms_and_data(  # pylint: disable=unused-argument
        self, query: Query, counterparty_address: Address
    ) -> Tuple[Description, Terms, Dict[str, str]]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :param counterparty_address: the counterparty of the proposal.
        :return: a tuple of proposal, terms and the weather data
        """
        seller_address = self.context.agent_addresses[self.ledger_id]
        total_price = self._sale_quantity * self._unit_price
        if self.is_ledger_tx:
            tx_nonce = LedgerApis.generate_tx_nonce(
                identifier=self.ledger_id,
                seller=seller_address,
                client=counterparty_address,
            )
        else:
            tx_nonce = uuid.uuid4().hex  # pragma: nocover
        proposal = Description(
            {
                "ledger_id": self.ledger_id,
                "price": total_price,
                "currency_id": self._currency_id,
                "service_id": self._service_id,
                "quantity": self._sale_quantity,
                "tx_nonce": tx_nonce,
            }
        )
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=seller_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={self._currency_id: total_price},
            quantities_by_good_id={self._service_id: -self._sale_quantity},
            is_sender_payable_tx_fee=False,
            nonce=tx_nonce,
            fee_by_currency_id={self._currency_id: 0},
        )
        return proposal, terms, self._data_for_sale

    def collect_from_data_source(self) -> Dict[str, str]:
        """Implement the logic to communicate with the sensor."""
        raise NotImplementedError
