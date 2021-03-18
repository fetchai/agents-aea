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
"""This module contains the tests of the strategy class of the weather station skill."""

import json
import time
from pathlib import Path
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.weather_station.strategy import (
    DEFAULT_DATE_ONE,
    DEFAULT_DATE_TWO,
    Strategy,
)

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of weather station."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "weather_station")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.strategy = Strategy(
            date_one=DEFAULT_DATE_ONE,
            date_two=DEFAULT_DATE_TWO,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_collect_from_data_source(self):
        """Test the collect_from_data_source method of the Strategy class."""
        # setup
        fetched_data = [
            (1023, 4, 35, 70, 1615894962, 72, 23, 22, 5, 3, 4),
            (1024, 3, 34, 50, 1615894961, 71, 19, 5, 2, 12, 2),
            (1025, 5, 36, 40, 1615894963, 73, 28, 20, 6, 4, 7),
            (1023, 7, 38, 75, 1615894964, 74, 25, 16, 9, 2, 5),
            (1025, 6, 37, 80, 1615894965, 72, 22, 12, 3, 8, 3),
        ]
        counter = 0
        row_data = {}
        for items in fetched_data:
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
        expected_weather_data = {"weather_data": json.dumps(row_data)}

        # operation
        with patch.object(
            self.strategy.db, "get_data_for_specific_dates", return_value=fetched_data
        ) as mock_get_data:
            weather_data = self.strategy.collect_from_data_source()

        # after
        mock_get_data.assert_any_call(DEFAULT_DATE_ONE, DEFAULT_DATE_TWO)
        assert weather_data == expected_weather_data
