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

from aea.protocols.oef.models import Attribute, DataModel, Description
from aea.skills.base import SharedClass

DEFAULT_PRICE_PER_PREDICTION = 2
DEFAULT_PRICE_PER_DATA_BATCH = 1
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_BUYER_TX_FEE = 0
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'fetchai'


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._price_per_row = kwargs.pop('price_per_prediction') if 'price_per_prediction' in kwargs.keys() else DEFAULT_PRICE_PER_PREDICTION
        self._price_per_row = kwargs.pop('price_per_data_batch') if 'price_per_data_batch' in kwargs.keys() else DEFAULT_PRICE_PER_DATA_BATCH
        self._seller_tx_fee = kwargs.pop('seller_tx_fee') if 'seller_tx_fee' in kwargs.keys() else DEFAULT_SELLER_TX_FEE
        self._buyer_tx_fee = kwargs.pop('buyer_tx_fee') if 'buyer_tx_fee' in kwargs.keys() else DEFAULT_BUYER_TX_FEE
        self._currency_pbk = kwargs.pop('currency_pbk') if 'currency_pbk' in kwargs.keys() else DEFAULT_CURRENCY_PBK
        self._ledger_id = kwargs.pop('ledger_id') if 'ledger_id' in kwargs.keys() else DEFAULT_LEDGER_ID
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
        dm = DataModel("ml_datamodel", [Attribute("ml_data", str, True)])
        desc = Description({'ml_data': 'Fashion MNIST'}, data_model=dm)
        return desc

    # def generate_proposal_and_data(self, query: Query) -> Tuple[Description, Dict[str, List[Dict[str, Any]]]]:
    #     """
    #     Generate a proposal matching the query.

    #     :param query: the query
    #     :return: a tuple of proposal and the weather data
    #     """
    #     proposal = Description({"rows": rows,
    #                             "price": total_price,
    #                             "seller_tx_fee": self._seller_tx_fee,
    #                             "currency_pbk": self._currency_pbk,
    #                             "ledger_id": self._ledger_id})
    #     return (proposal, weather_data)
