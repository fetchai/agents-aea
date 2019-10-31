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
import os
from typing import Any, Dict, List, Tuple, TYPE_CHECKING, cast
import time

from aea.protocols.oef.models import Description, Query
from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.skills.carpark_detection.detection_database import DetectionDatabase
    from packages.skills.carpark_detection.carpark_detection_data_model import CarParkDataModel

else:
    from carpark_detection_skill.detection_database import DetectionDatabase
    from carpark_detection_skill.carpark_detection_data_model import CarParkDataModel

DEFAULT_PRICE = 2000
DEFAULT_DB_IS_REL_TO_CWD = False
DEFAULT_DB_REL_DIR = "temp_files_placeholder"


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        db_is_rel_to_cwd = kwargs.pop('db_is_rel_to_cwd') if 'db_is_rel_to_cwd' in kwargs.keys() else DEFAULT_DB_IS_REL_TO_CWD
        db_rel_dir = kwargs.pop('db_rel_dir') if 'db_rel_dir' in kwargs.keys() else DEFAULT_DB_REL_DIR

        if db_is_rel_to_cwd:
            db_dir = os.path.join(os.getcwd(), db_rel_dir)
        else:
            db_dir = os.path.join(os.path.dirname(__file__), DEFAULT_DB_REL_DIR)

        self.data_price_fet = kwargs.pop('data_price_fet') if 'data_price_fet' in kwargs.keys() else DEFAULT_PRICE
        super().__init__(**kwargs)

        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))

        if not os.path.isdir(db_dir):
            print("WARNING - DATABASE dir does not exist")

        self.db = DetectionDatabase(db_dir, False)
        self.lat = 43
        self.lon = 42
        self.record_balance(balance)


    def record_balance(self, balance):
        self.db.set_fet(balance, time.time())

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

    def has_data(self) -> bool:
        """Return whether we have any useful data to sell"""
        data = self.db.get_latest_detection_data(1)
        return len(data) > 0

    def generate_proposal_and_data(self, query: Query) -> Tuple[Description, Dict[str, List[Dict[str, Any]]]]:
        """
        Generate a proposal matching the query.

        :param query: the query
        :return: a tuple of proposal and the bytes of carpark data
        """
        # TODO, this is a stub
        data = self.db.get_latest_detection_data(1)
        assert (len(data) > 0)

        del data[0]['raw_image_path']
        del data[0]['processed_image_path']

        last_detection_time = data[0]["epoch"]
        max_spaces = data[0]["free_spaces"] + data[0]["total_count"]
        proposal = Description({

            "lat": data[0]["lat"],
            "lon": data[0]["lon"],
            "price": self.data_price_fet,
            "last_detection_time": last_detection_time,
            "max_spaces": max_spaces,
        })

        data[0]["price_fet"] = self.data_price_fet
        data[0]["message_type"] = "car_park_data"

        return proposal, data[0]

