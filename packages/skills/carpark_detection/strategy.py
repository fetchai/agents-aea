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
import os
import time
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from aea.protocols.oef.models import Description, Query
from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.skills.carpark_detection.detection_database import DetectionDatabase
    from packages.skills.carpark_detection.carpark_detection_data_model import CarParkDataModel
#    from packages.skills.carpark_detection.carpark_detection_data_model import WEATHER_STATION_DATAMODEL, SCHEME

else:
    from carpark_detection_skill.detection_database import DetectionDatabase
    from carpark_detection_skill.carpark_detection_data_model import CarParkDataModel
 #   from carpark_detection_skill.carpark_detection_data_model import WEATHER_STATION_DATAMODEL, SCHEME

DEFAULT_PRICE_PER_ROW = 0.02
DEFAULT_CURRENCY_PBK = 'FET'
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
        self.currency = kwargs.pop('currency_pbk') if 'currency_pbk' in kwargs.keys() else DEFAULT_CURRENCY_PBK
        super().__init__(**kwargs)

        self.db = DetectionDatabase(os.path.dirname(__file__))
        self.data_price_fet = 2000
        self.lat = 43
        self.lon = 42

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """

        desc = Description(
            {
                "latitude": float(self.lat),
                "longitude": float(self.lon),
                "unique_id": self.context.agent_public_key
            }, data_model=CarParkDataModel()
        )

        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True

    def generate_proposal_and_data(self, query: Query) -> Tuple[Description, bytes]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :return: a tuple of proposal and the bytes of carpark data
        """
        # TODO, this is a stub
        data = self.db.get_latest_detection_data(1)
        data = self.db.get_latest_detection_data(1)
        if data is None:
            return None, None


        del data[0]['raw_image_path']
        del data[0]['processed_image_path']

        last_detection_time = data[0]["epoch"]
        max_spaces = data[0]["free_spaces"] + data[0]["total_count"]
        proposal = Description({
            "lat": data[0]["lat"],
            "lon": data[0]["lon"],
            "price": self.data_price_fet,
            "last_detection_time": int(time.time()),  #last_detection_time,
            "max_spaces": max_spaces,
        })
        print ("WARNING - always using now time")


        data[0]["price_fet"] = self.data_price_fet
        data[0]["message_type"] = "car_park_data"
        encoded_data = json.dumps(data[0]).encode("utf-8")

        return (proposal, encoded_data)
