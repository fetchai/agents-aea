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
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from aea.protocols.oef.models import Description, Query
from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.skills.weather_station_ledger.db_communication import DBCommunication
    from packages.skills.weather_station_ledger.weather_station_data_model import WEATHER_STATION_DATAMODEL, SCHEME
else:
    from weather_station_ledger_skill.db_communication import DBCommunication
    from weather_station_ledger_skill.weather_station_data_model import WEATHER_STATION_DATAMODEL, SCHEME

DEFAULT_PRICE_PER_ROW = 2
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'fetchai'
DATE_ONE = "3/10/2019"
DATE_TWO = "15/10/2019"


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self.price_per_row = kwargs.pop('price_per_row') if 'price_per_row' in kwargs.keys() else DEFAULT_PRICE_PER_ROW
        self.currency_pbk = kwargs.pop('currency_pbk') if 'currency_pbk' in kwargs.keys() else DEFAULT_CURRENCY_PBK
        self.ledger_id = kwargs.pop('ledger_id') if 'ledger_id' in kwargs.keys() else DEFAULT_LEDGER_ID
        super().__init__(**kwargs)
        self.db = DBCommunication()

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
        # TODO, this is a stub
        fetched_data = self.db.get_data_for_specific_dates(DATE_ONE, DATE_TWO)
        weather_data, rows = self._build_data_payload(fetched_data)
        total_price = self.price_per_row * rows
        proposal = Description({"rows": rows,
                                "price": total_price,
                                "currency_pbk": self.currency_pbk,
                                "ledger_id": self.ledger_id})
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
