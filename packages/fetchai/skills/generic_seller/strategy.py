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
import logging
from typing import Any, Dict, List, Optional, Tuple

from aea.helpers.search.models import Description, Query
from aea.mail.base import Address
from aea.skills.base import SharedClass

from packages.fetchai.skills.generic_seller.generic_data_model import Generic_Data_Model


DEFAULT_SELLER_TX_FEE = 0
DEFAULT_TOTAL_PRICE = 10
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_HAS_DATA_SOURCE = False
DEFAULT_DATA_FOR_SALE = {}  # type: Optional[Dict[str, Any]]
DEFAULT_IS_LEDGER_TX = True

logger = logging.getLogger(__name__)


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self._total_price = kwargs.pop("total_price", DEFAULT_TOTAL_PRICE)
        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)

        # Read the data from the sensor if the bool is set to True.
        # Enables us to let the user implement his data collection logic without major changes.
        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()
        else:
            self._data_for_sale = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)

        super().__init__(**kwargs)
        self._oef_msg_id = 0

        self._scheme = kwargs.pop("search_data")
        self._datamodel = kwargs.pop("search_datamodel")

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        desc = Description(self._scheme, data_model=Generic_Data_Model(self._datamodel))
        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True

    def generate_proposal_and_data(
        self, query: Query, counterparty: Address
    ) -> Tuple[Description, Dict[str, List[Dict[str, Any]]]]:
        """
        Generate a proposal matching the query.

        :param counterparty: the counterparty of the proposal.
        :param query: the query
        :return: a tuple of proposal and the weather data
        """
        tx_nonce = self.context.ledger_apis.generate_tx_nonce(
            identifier=self._ledger_id,
            seller=self.context.agent_addresses[self._ledger_id],
            client=counterparty,
        )
        assert (
            self._total_price - self._seller_tx_fee > 0
        ), "This sale would generate a loss, change the configs!"
        proposal = Description(
            {
                "price": self._total_price,
                "seller_tx_fee": self._seller_tx_fee,
                "currency_id": self._currency_id,
                "ledger_id": self._ledger_id,
                "tx_nonce": tx_nonce if tx_nonce is not None else "",
            }
        )
        return proposal, self._data_for_sale

    def collect_from_data_source(self):
        """Implement the logic to communicate with the sensor."""
        raise NotImplementedError
