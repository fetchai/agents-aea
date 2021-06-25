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

import json
import time
from typing import Any, Dict

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy
from packages.fetchai.skills.weather_station.db_communication import DBCommunication


DEFAULT_DATE_ONE = "3/10/2019"
DEFAULT_DATE_TWO = "15/10/2019"


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        self._date_one = kwargs.pop("date_one", DEFAULT_DATE_ONE)
        self._date_two = kwargs.pop("date_two", DEFAULT_DATE_TWO)
        self.db = DBCommunication()
        super().__init__(**kwargs)

    def collect_from_data_source(self) -> Dict[str, str]:
        """
        Build the data payload.

        :return: a tuple of the data and the rows
        """
        fetched_data = self.db.get_data_for_specific_dates(
            self._date_one, self._date_two
        )
        weather_data = {}  # type: Dict[str, str]
        row_data = {}  # type: Dict[int, Dict[str, Any]]
        counter = 0
        for items in fetched_data:
            if counter > 10:  # so not too much data is sent
                break  # pragma: nocover
            counter += 1
            dict_of_data = {
                "abs_pressure": items[0],
                "delay": items[1],
                "hum_in": items[2],
                "hum_out": items[3],
                "idx": time.ctime(int(items[4])),
                "rain": items[5],
                "temp_in": items[6],
                "temp_out": items[7],
                "wind_ave": items[8],
                "wind_dir": items[9],
                "wind_gust": items[10],
            }
            row_data[counter] = dict_of_data
        weather_data["weather_data"] = json.dumps(row_data)
        return weather_data
