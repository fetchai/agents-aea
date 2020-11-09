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

"""This package contains a the registration db model."""

import datetime
import logging
import os
import sqlite3
from typing import Any, Dict, Tuple

from aea.skills.base import Model


_default_logger = logging.getLogger(
    "aea.packages.fetchai.skills.carpark_detection.detection_database"
)


class RegistrationDB(Model):
    """Communicate between the database and the python objects."""

    def __init__(self, **kwargs):
        """Initialise the Detection Database Communication class."""
        custom_path = kwargs.pop("custom_path", None)
        super().__init__(**kwargs)
        this_dir = os.getcwd()
        self.db_path = (
            os.path.join(this_dir, "registration.db")
            if custom_path is None
            else custom_path
        )
        self._initialise_backend()

    def _initialise_backend(self) -> None:
        """Set up database and initialise the tables."""
        if os.path.isfile(self.db_path):
            return
        self._execute_single_sql(
            "CREATE TABLE IF NOT EXISTS registered_table (address TEXT, ethereum_address TEXT, "
            "ethereum_signature TEXT, fetchai_signature TEXT, "
            "developer_handle TEXT, tweet TEXT)"
        )
        self._execute_single_sql(
            "CREATE TABLE IF NOT EXISTS trade_table (address TEXT, first_trade timestamp, "
            "second_trade timestamp)"
        )

    def set_trade(
        self, address: str, timestamp: datetime.datetime, data: Dict[str, str],
    ):
        """Record a registration."""
        is_second = False  # todo, query from db
        # todo: also save data
        if is_second:
            command = (
                "INSERT OR REPLACE INTO trade_table(address, second_trade) values(?, ?)"
            )
        else:
            command = (
                "INSERT OR REPLACE INTO trade_table(address, first_trade) values(?, ?)"
            )
        variables = (
            address,
            timestamp,
        )
        self._execute_single_sql(command, variables)

    def is_registered(self, address: str) -> bool:
        """Check if an address is registered."""
        command = "SELECT * FROM registered_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        return len(result) != 0

    def is_allowed_to_trade(self, address: str, mininum_hours_between_txs: int) -> bool:
        """Check if an address is registered."""
        command = "SELECT * FROM trade_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        # todo: check :
        #  - if no timestamp present: return true
        #  - if first timestamp is present: return true iff the trade is 4 hours in past
        #  - if second timestamp is present: return false
        return result is None

    def _execute_single_sql(
        self,
        command: str,
        variables: Tuple[Any, ...] = (),
        print_exceptions: bool = True,
    ):
        """Query the database - all the other functions use this under the hood."""
        conn = None
        ret = []
        try:
            conn = sqlite3.connect(self.db_path, timeout=300)  # 5 mins
            c = conn.cursor()
            c.execute(command, variables)
            ret = c.fetchall()
            conn.commit()
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            if print_exceptions:
                self.context.logger.warning(f"Exception in database: {e}")
        finally:
            if conn is not None:
                conn.close()

        return ret
