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

from typing import Any, Dict, Optional

from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Description
from aea.skills.base import Model

DEFAULT_IS_LEDGER_TX = True
DEFAULT_NFT = 1
DEFAULT_FT = 2
DEFAULT_NB_TOKENS = 10
DEFAULT_MINT_STOCK = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
DEFAULT_FROM_SUPPLY = 10
DEFAULT_TO_SUPPLY = 0
DEFAULT_VALUE = 0
DEFAULT_DATA_MODEL_NAME = "erc1155_deploy"
DEFAULT_DATA_MODEL = {
    "attribute_one": {
        "name": "has_erc1155_contract",
        "type": "bool",
        "is_required": "True",
    },
}  # type: Optional[Dict[str, Any]]
DEFAULT_SERVICE_DATA = {"has_erc1155_contract": True}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.
        :return: None
        """
        self.nft = kwargs.pop("nft", DEFAULT_NFT)
        self.ft = kwargs.pop("ft", DEFAULT_NFT)
        self.nb_tokens = kwargs.pop("nb_tokens", DEFAULT_NB_TOKENS)
        self.mint_stock = kwargs.pop("mint_stock", DEFAULT_MINT_STOCK)
        self.contract_address = kwargs.pop("contract_address", None)
        self.from_supply = kwargs.pop("from_supply", DEFAULT_FROM_SUPPLY)
        self.to_supply = kwargs.pop("to_supply", DEFAULT_TO_SUPPLY)
        self.value = kwargs.pop("value", DEFAULT_VALUE)
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        super().__init__(**kwargs)
        self._oef_msg_id = 0

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
        desc = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return desc
