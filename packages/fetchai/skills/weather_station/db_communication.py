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

"""This package contains the Database Communication for the weather agent."""

import datetime
import os.path
import sqlite3
from typing import Dict, cast


my_path = os.path.dirname(__file__)

DB_SOURCE = os.path.join(my_path, "dummy_weather_station_data.db")


class DBCommunication:
    """A class to communicate with a database."""

    def __init__(self) -> None:
        """Initialize the database communication."""
        self.source = DB_SOURCE

    def db_connection(self) -> sqlite3.Connection:
        """
        Get db connection.

        :return: the db connection
        """
        con = sqlite3.connect(self.source)
        return con

    def get_data_for_specific_dates(
        self, start_date: str, end_date: str
    ) -> Dict[str, int]:
        """
        Get data for specific dates.

        :param start_date: the start date
        :param end_date: the end date
        :return: the data
        """
        con = self.db_connection()
        cur = con.cursor()
        start_dt = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        start = int((start_dt - datetime.datetime.fromtimestamp(0)).total_seconds())
        end_dt = datetime.datetime.strptime(end_date, "%d/%m/%Y")
        end = int((end_dt - datetime.datetime.fromtimestamp(0)).total_seconds())
        cur.execute(
            "SELECT * FROM data WHERE idx BETWEEN ? AND ?", (str(start), str(end))
        )
        data = cast(Dict[str, int], cur.fetchall())
        cur.close()
        con.close()
        return data
