# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

from aea.helpers.search.models import Description, Query
from aea.skills.base import Model

from packages.fetchai.skills.erc1155_deploy.generic_data_model import Generic_Data_Model


DEFAULT_LEDGER_ID = "ethereum"
DEFAULT_IS_LEDGER_TX = True
DEFAULT_NFT = 1
DEFAULT_FT = 2
DEFAULT_ITEMS_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
DEFAULT_MINT_STOCK = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
DEFAULT_FROM_SUPPLY = 10
DEFAULT_TO_SUPPLY = 0
DEFAULT_VALUE = 0


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self.nft = kwargs.pop("nft", DEFAULT_NFT)
        self.ft = kwargs.pop("ft", DEFAULT_NFT)
        self.item_ids = kwargs.pop("item_ids", DEFAULT_ITEMS_IDS)
        self.mint_stock = kwargs.pop("mint_stock", DEFAULT_MINT_STOCK)
        self.contract_address = kwargs.pop("contract_address", None)
        self.from_supply = kwargs.pop("from_supply", DEFAULT_FROM_SUPPLY)
        self.to_supply = kwargs.pop("to_supply", DEFAULT_TO_SUPPLY)
        self.value = kwargs.pop("value", DEFAULT_VALUE)

        # Read the data from the sensor if the bool is set to True.
        # Enables us to let the user implement his data collection logic without major changes.

        super().__init__(**kwargs)
        self._oef_msg_id = 0

        self._scheme = kwargs.pop("search_data")
        self._datamodel = kwargs.pop("search_schema")

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
