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

"""This package contains dummy weather station data."""

import datetime
import logging
import os.path
import random
import sqlite3
import time
from typing import Dict, Union

logger = logging.getLogger("aea.weather_station_skill")

my_path = os.path.dirname(__file__)

DB_SOURCE = os.path.join(my_path, 'dummy_weather_station_data.db')

# Checking if the database exists
con = sqlite3.connect(DB_SOURCE)
cur = con.cursor()

cur.close()
con.commit()
con.close()

# Create a table if it doesn't exist'
command = (''' CREATE TABLE IF NOT EXISTS data (
                                 abs_pressure REAL,
                                 delay REAL,
                                 hum_in REAL,
                                 hum_out REAL,
                                 idx TEXT,
                                 rain REAL,
                                 temp_in REAL,
                                 temp_out REAL,
                                 wind_ave REAL,
                                 wind_dir REAL,
                                 wind_gust REAL)''')

con = sqlite3.connect(DB_SOURCE)
cur = con.cursor()
cur.execute(command)
cur.close()
con.commit()
if con is not None:
    logger.debug("Weather station: I closed the db after checking it is populated!")
    con.close()


class Forecast():
    """Represents a whether forecast."""

    def add_data(self, tagged_data: Dict[str, Union[int, datetime.datetime]]) -> None:
        """
        Add data to the forecast.

        :param tagged_data: the data dictionary
        :return: None
        """
        con = sqlite3.connect(DB_SOURCE)
        cur = con.cursor()
        cur.execute('''INSERT INTO data(abs_pressure,
                                       delay,
                                       hum_in,
                                       hum_out,
                                       idx,
                                       rain,
                                       temp_in,
                                       temp_out,
                                       wind_ave,
                                       wind_dir,
                                       wind_gust) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tagged_data['abs_pressure'],
                     tagged_data['delay'],
                     tagged_data['hum_in'],
                     tagged_data['hum_out'],
                     datetime.datetime.now().strftime('%s'),
                     tagged_data['rain'],
                     tagged_data['temp_in'],
                     tagged_data['temp_out'],
                     tagged_data['wind_ave'],
                     tagged_data['wind_dir'],
                     tagged_data['wind_gust']))
        logger.info("Wheather station: I added data in the db!")
        cur.close()
        con.commit()
        con.close()

    def generate(self):
        """Generate weather data."""
        while True:
            dict_of_data = {'abs_pressure': random.randrange(1022.0, 1025, 1), 'delay': random.randint(2, 7),
                            'hum_in': random.randrange(33.0, 40.0, 1), 'hum_out': random.randrange(33.0, 80.0, 1),
                            'idx': datetime.datetime.now(), 'rain': random.randrange(70.0, 74.0, 1),
                            'temp_in': random.randrange(18, 28, 1), 'temp_out': random.randrange(2, 20, 1),
                            'wind_ave': random.randrange(0, 10, 1), 'wind_dir': random.randrange(0, 14, 1),
                            'wind_gust': random.randrange(1, 7, 1)}  # type: Dict[str, Union[int, datetime.datetime]]
            self.add_data(dict_of_data)
            time.sleep(5)


if __name__ == '__main__':
    a = Forecast()
    a.generate()
