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

import time
from typing import Any, Dict, List, Tuple

from aea.helpers.search.models import Description, Query
from aea.skills.base import SharedClass
from packages.fetchai.skills.weather_station_ledger.db_communication import DBCommunication
from packages.fetchai.skills.weather_station_ledger.weather_station_data_model import WEATHER_STATION_DATAMODEL, SCHEME

DEFAULT_PRICE_PER_ROW = 2
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'fetchai'
DEFAULT_DATE_ONE = "3/10/2019"
DEFAULT_DATE_TWO = "15/10/2019"


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._price_per_row = kwargs.pop('price_per_row') if 'price_per_row' in kwargs.keys() else DEFAULT_PRICE_PER_ROW
        self._seller_tx_fee = kwargs.pop('seller_tx_fee') if 'seller_tx_fee' in kwargs.keys() else DEFAULT_SELLER_TX_FEE
        self._currency_id = kwargs.pop('currency_id') if 'currency_id' in kwargs.keys() else DEFAULT_CURRENCY_PBK
        self._ledger_id = kwargs.pop('ledger_id') if 'ledger_id' in kwargs.keys() else DEFAULT_LEDGER_ID
        self._date_one = kwargs.pop('date_one') if 'date_one' in kwargs.keys() else DEFAULT_DATE_ONE
        self._date_two = kwargs.pop('date_two') if 'date_two' in kwargs.keys() else DEFAULT_DATE_TWO
        super().__init__(**kwargs)
        self.db = DBCommunication()
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
        desc = Description(SCHEME, data_model=WEATHER_STATION_DATAMODEL())
        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True

    def generate_proposal_and_data(self, query: Query) -> Tuple[Description, Dict[str, List[Dict[str, Any]]]]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :return: a tuple of proposal and the weather data
        """
        fetched_data = self.db.get_data_for_specific_dates(self._date_one, self._date_two)  # TODO: fetch real data
        weather_data, rows = self._build_data_payload(fetched_data)
        total_price = self._price_per_row * rows
        assert total_price - self._seller_tx_fee > 0, "This sale would generate a loss, change the configs!"
        proposal = Description({"rows": rows,
                                "price": total_price,
                                "seller_tx_fee": self._seller_tx_fee,
                                "currency_id": self._currency_id,
                                "ledger_id": self._ledger_id})
        return (proposal, weather_data)

    def _build_data_payload(self, fetched_data: Dict[str, int]) -> Tuple[Dict[str, List[Dict[str, Any]]], int]:
        """
        Build the data payload.

        :param fetched_data: the fetched data
        :return: a tuple of the data and the rows
        """
        weather_data = {}  # type: Dict[str, List[Dict[str, Any]]]
        weather_data['weather_data'] = []
        counter = 0
        for items in fetched_data:
            if counter > 10:
                break  # TODO: fix OEF so more data can be sent
            counter += 1
            dict_of_data = {
                'abs_pressure': items[0],
                'delay': items[1],
                'hum_in': items[2],
                'hum_out': items[3],
                'idx': time.ctime(int(items[4])),
                'rain': items[5],
                'temp_in': items[6],
                'temp_out': items[7],
                'wind_ave': items[8],
                'wind_dir': items[9],
                'wind_gust': items[10]
            }
            weather_data['weather_data'].append(dict_of_data)
        return weather_data, counter
