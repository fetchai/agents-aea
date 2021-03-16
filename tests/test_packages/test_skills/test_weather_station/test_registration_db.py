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
"""This module contains the tests of the RegistrationDB class of the weather station skill."""
import datetime
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.weather_station.db_communication import (
    DBCommunication,
    DB_SOURCE,
)

from tests.conftest import ROOT_DIR


class TestDBCommunication(BaseSkillTestCase):
    """Test RegistrationDB of weather station."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "weather_station")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.db = DBCommunication()

    def test_db_connection(self):
        """Test the db_connection method of the DBCommunication class."""
        # setup
        mocked_conn = Mock(wrap=sqlite3.Connection)

        # operation
        with patch("sqlite3.connect", return_value=mocked_conn) as mock_conn:
            actual_con = self.db.db_connection()

        # after
        mock_conn.assert_any_call(DB_SOURCE)
        assert actual_con == mocked_conn

    def test_get_data_for_specific_dates(self):
        """Test the get_data_for_specific_dates method of the DBCommunication class."""
        # setup
        start_date = "3/10/2019"
        end_date = "15/10/2019"
        result = {"abs_pressure": 100, "hum_in": 20}

        start_dt = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        end_dt = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        start = int((start_dt - datetime.datetime.fromtimestamp(0)).total_seconds())
        end = int((end_dt - datetime.datetime.fromtimestamp(0)).total_seconds())

        mocked_conn = Mock(wrap=sqlite3.Connection)
        mocked_cursor = Mock(wraps=sqlite3.Cursor)

        # operation
        with patch.object(
            self.db, "db_connection", return_value=mocked_conn
        ) as mock_conn:
            with patch.object(
                mocked_conn, "cursor", return_value=mocked_cursor
            ) as mock_curs:
                with patch.object(mocked_cursor, "execute") as mock_exe:
                    with patch.object(
                        mocked_cursor, "fetchall", return_value=result
                    ) as mock_fetchall:
                        with patch.object(mocked_cursor, "close") as mock_cur_close:
                            with patch.object(mocked_conn, "close") as mock_con_close:
                                actual_result = self.db.get_data_for_specific_dates(
                                    start_date, end_date
                                )

        # after
        mock_conn.assert_called_once()
        mock_curs.assert_called_once()
        mock_fetchall.assert_called_once()
        mock_exe.assert_any_call(
            "SELECT * FROM data WHERE idx BETWEEN ? AND ?", (str(start), str(end)),
        )
        mock_cur_close.assert_called_once()
        mock_con_close.assert_called_once()
        assert actual_result == result
