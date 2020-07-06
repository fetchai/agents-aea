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
import random  # nosec
import time
from typing import Dict

import sqlalchemy as db

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._db_engine = db.create_engine("sqlite:///genericdb.db")
        self._tbl = self.create_database_and_table()
        self.insert_data()
        super().__init__(**kwargs)

    def collect_from_data_source(self) -> Dict[str, str]:
        """Implement the logic to collect data."""
        connection = self._db_engine.connect()
        query = db.select([self._tbl])
        result_proxy = connection.execute(query)
        data_points = result_proxy.fetchall()
        return {"data": json.dumps(list(map(tuple, data_points)))}

    def create_database_and_table(self):
        """Creates a database and a table to store the data if not exists."""
        metadata = db.MetaData()

        tbl = db.Table(
            "data",
            metadata,
            db.Column("timestamp", db.Integer()),
            db.Column("temprature", db.String(255), nullable=False),
        )
        metadata.create_all(self._db_engine)
        return tbl

    def insert_data(self):
        """Insert data in the database."""
        connection = self._db_engine.connect()
        for _ in range(10):
            query = db.insert(self._tbl).values(  # nosec
                timestamp=time.time(), temprature=str(random.randrange(10, 25))
            )
            connection.execute(query)
