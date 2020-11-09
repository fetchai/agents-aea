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
import json
import logging
import os
import sqlite3
from typing import Any, Dict, Optional, Tuple

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
            "CREATE TABLE IF NOT EXISTS trade_table (address TEXT PRIMARY KEY, first_trade timestamp, "
            "second_trade timestamp, first_info TEXT, second_info TEXT)"
        )

    def set_trade(
        self, address: str, timestamp: datetime.datetime, data: Dict[str, str],
    ):
        """Record a registration."""
        record = self.get_trade_table(address)
        if record is None:
            return

        _, first_trade, second_trade, first_info, second_info = record
        is_second = first_trade is not None and second_trade is None
        if is_second:
            command = "INSERT INTO trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)"
            variables = (
                address,
                timestamp,
                second_trade,
                json.dumps(data),
                second_info,
            )
        else:
            command = "INSERT INTO trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)"
            variables = (address, first_trade, timestamp, first_info, json.dumps(data))
        self._execute_single_sql(command, variables)

    def get_trade_table(self, address: str) -> Optional[Tuple]:
        """Check whether a trade is second or not."""
        command = "SELECT * FROM trade_table where address=?"
        ret = self._execute_single_sql(command, (address,))
        return ret[0] if len(ret) > 0 else None

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
        record = result[0]
        first_trade: datetime.datetime = record[1]
        second_trade: datetime.datetime = record[2]
        first_trade_present: bool = first_trade is not None
        second_trade_present: bool = second_trade is not None
        if not first_trade_present and not second_trade_present:
            return True
        if first_trade_present and not second_trade_present:
            return second_trade - first_trade > datetime.timedelta(
                hours=mininum_hours_between_txs
            )
        return False

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
