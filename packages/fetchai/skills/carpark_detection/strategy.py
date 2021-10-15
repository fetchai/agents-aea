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
from typing import Any, Dict

from aea.exceptions import enforce

from packages.fetchai.skills.carpark_detection.database import DetectionDatabase
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


DEFAULT_DB_IS_REL_TO_CWD = False
DEFAULT_DB_REL_DIR = "temp_files_placeholder"


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        db_is_rel_to_cwd = kwargs.pop("db_is_rel_to_cwd", DEFAULT_DB_IS_REL_TO_CWD)
        db_rel_dir = kwargs.pop("db_rel_dir", DEFAULT_DB_REL_DIR)

        if db_is_rel_to_cwd:
            db_dir = os.path.join(os.getcwd(), db_rel_dir)
        else:
            db_dir = os.path.join(os.path.dirname(__file__), db_rel_dir)

        if not os.path.isdir(db_dir):
            raise ValueError("Database directory does not exist!")

        super().__init__(**kwargs)
        self.db = DetectionDatabase(db_dir, False, logger=self.context.logger)
        self._update_service_data()

    def collect_from_data_source(self) -> Dict[str, str]:
        """
        Build the data payload.

        :return: the data
        """
        enforce(self.db.is_db_exits(), "Db doesn't exist.")
        data = self.db.get_latest_detection_data(1)
        enforce(len(data) > 0, "Did not find any data.")
        free_spaces = data[0]["free_spaces"]
        return {"free_spaces": str(free_spaces)}

    def _update_service_data(self) -> None:
        """Update lat and long in service data if db present."""
        if self.db.is_db_exits() and len(self.db.get_latest_detection_data(1)) > 0:
            lat, lon = self.db.get_lat_lon()
            if lat is not None and lon is not None:
                data = {
                    "latitude": lat,
                    "longitude": lon,
                }
                self._service_data = data
