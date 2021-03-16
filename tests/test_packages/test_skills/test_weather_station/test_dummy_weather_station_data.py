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
"""This module contains the tests of the dummy_weather_station_data class of the weather station skill."""
import datetime
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.weather_station.dummy_weather_station_data import Forecast
from packages.fetchai.skills.weather_station.dummy_weather_station_data import (
    _default_logger as logger,
)

from tests.conftest import ROOT_DIR


class TestDummyWeatherStationData(BaseSkillTestCase):
    """Test dummy_weather_station_data of weather station."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "weather_station")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.forecast = Forecast()

    def test_generate(self):
        """Test the generate method of the Forecast class."""
        # operation
        with patch.object(self.forecast, "add_data") as mock_add:
            self.forecast.generate(2)

        # after
        assert mock_add.call_count == 2

    def test_add_data(self):
        """Test the add_data method of the Forecast class."""
        # setup
        tagged_data = {
            "abs_pressure": 100,
            "delay": 20,
            "hum_in": 20,
            "hum_out": 20,
            int(
                (
                    datetime.datetime.now() - datetime.datetime.fromtimestamp(0)
                ).total_seconds()
            ): 20,
            "rain": 20,
            "temp_in": 20,
            "temp_out": 20,
            "wind_ave": 20,
            "wind_dir": 20,
            "wind_gust": 20,
        }

        mocked_conn = Mock(wrap=sqlite3.Connection)
        mocked_cursor = Mock(wraps=sqlite3.Cursor)

        # operation
        with patch("sqlite3.connect", return_value=mocked_conn) as mock_conn:
            with patch.object(
                mocked_conn, "cursor", return_value=mocked_cursor
            ) as mock_curs:
                with patch.object(mocked_cursor, "execute") as mock_exe:
                    with patch.object(logger, "info") as mock_logger:
                        with patch.object(mocked_cursor, "close") as mock_cur_close:
                            with patch.object(mocked_conn, "commit") as mock_con_commit:
                                with patch.object(
                                    mocked_conn, "close"
                                ) as mock_con_close:
                                    self.forecast.add_data(tagged_data)

        # after
        mock_conn.assert_called_once()
        mock_curs.assert_called_once()
        mock_exe.assert_any_call(
            """INSERT INTO data(abs_pressure,
                                       delay,
                                       hum_in,
                                       hum_out,
                                       idx,
                                       rain,
                                       temp_in,
                                       temp_out,
                                       wind_ave,
                                       wind_dir,
                                       wind_gust) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tagged_data["abs_pressure"],
                tagged_data["delay"],
                tagged_data["hum_in"],
                tagged_data["hum_out"],
                int(
                    (
                        datetime.datetime.now() - datetime.datetime.fromtimestamp(0)
                    ).total_seconds()
                ),
                tagged_data["rain"],
                tagged_data["temp_in"],
                tagged_data["temp_out"],
                tagged_data["wind_ave"],
                tagged_data["wind_dir"],
                tagged_data["wind_gust"],
            ),
        )
        mock_logger.assert_any_call("Wheather station: I added data in the db!")
        mock_cur_close.assert_called_once()
        mock_con_commit.assert_called_once()
        mock_con_close.assert_called_once()
