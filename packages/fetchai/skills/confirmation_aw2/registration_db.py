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
from typing import Any, Dict, List, Optional, Tuple

from aea.skills.base import Model


_default_logger = logging.getLogger(
    "aea.packages.fetchai.skills.confirmation_aw2.registration_db"
)


class RegistrationDB(Model):
    """Communicate between the database and the python objects."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialise the class."""
        custom_path = kwargs.pop("custom_path", None)
        super().__init__(**kwargs)
        this_dir = os.getcwd()
        self.db_path = (
            os.path.join(this_dir, "registration.db")
            if custom_path is None
            else custom_path
        )
        if not os.path.exists(os.path.dirname(os.path.abspath(self.db_path))):
            raise ValueError(f"Path={self.db_path} not valid!")  # pragma: nocover
        self._initialise_backend()

    def _initialise_backend(self) -> None:
        """Set up database and initialise the tables."""
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
    ) -> None:
        """Record a registration."""
        record = self.get_trade_table(address)
        if record is None:
            command = "INSERT INTO trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)"
            variables: Tuple[
                str, datetime.datetime, Optional[datetime.datetime], str, Optional[str]
            ] = (address, timestamp, None, json.dumps(data), None)
        else:
            _, first_trade, second_trade, first_info, _ = record
            is_second = first_trade is not None and second_trade is None
            is_more_than_two = first_trade is not None and second_trade is not None
            if is_more_than_two or not is_second:
                return
            command = "INSERT or REPLACE into trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)"
            variables = (
                address,
                first_trade,
                timestamp,
                first_info,
                json.dumps(data),
            )
        self._execute_single_sql(command, variables)

    def get_trade_table(self, address: str) -> Optional[Tuple]:
        """Check whether a trade is second or not."""
        command = "SELECT * FROM trade_table where address=?"
        ret = self._execute_single_sql(command, (address,))
        return ret[0] if len(ret) > 0 else None

    def set_registered(self, address: str, developer_handle: str) -> None:
        """Record a registration."""
        if self.is_registered(address):
            return
        command = "INSERT OR REPLACE INTO registered_table(address, ethereum_address, ethereum_signature, fetchai_signature, developer_handle, tweet) values(?, ?, ?, ?, ?, ?)"
        variables = (
            address,
            "",
            "",
            "",
            developer_handle,
            "",
        )
        self._execute_single_sql(command, variables)

    def is_registered(self, address: str) -> bool:
        """Check if an address is registered."""
        command = "SELECT * FROM registered_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        return len(result) != 0

    def is_allowed_to_trade(self, address: str, minimum_hours_between_txs: int) -> bool:
        """Check if an address is registered."""
        record = self.get_trade_table(address)
        if record is None:
            # no record on trade: go ahead
            return True
        first_trade: Optional[str] = record[1]
        second_trade: Optional[str] = record[2]
        first_trade_present: bool = first_trade is not None
        second_trade_present: bool = second_trade is not None
        if not first_trade_present and not second_trade_present:
            # all trades empty: go ahead
            return True
        if first_trade is not None and not second_trade_present:
            now = datetime.datetime.now()
            first_trade_dt = datetime.datetime.strptime(
                first_trade, "%Y-%m-%d %H:%M:%S.%f"
            )
            is_allowed_to_trade_ = now - first_trade_dt > datetime.timedelta(
                hours=minimum_hours_between_txs
            )
            if not is_allowed_to_trade_:
                self.context.logger.info(
                    f"Invalid attempt for counterparty={address}, not enough time since last trade!"
                )
            return is_allowed_to_trade_
        self.context.logger.info(
            f"Invalid attempt for counterparty={address}, already completed 2 trades!"
        )
        return False

    def has_completed_two_trades(self, address: str) -> bool:
        """
        Check if address has completed two trades.

        :param address: the address to check
        :return: bool
        """
        record = self.get_trade_table(address)
        if record is None:
            return False
        first_trade: Optional[str] = record[1]
        second_trade: Optional[str] = record[2]
        first_trade_present: bool = first_trade is not None
        second_trade_present: bool = second_trade is not None
        return first_trade_present and second_trade_present

    def completed_two_trades(self) -> List[Tuple[str, str, str]]:
        """
        Get the address, ethereum_address and developer handle combos which completed two trades.

        :return: (address, ethereum_address, developer_handle)
        """
        command = "SELECT * FROM registered_table"
        variables = ()
        result = self._execute_single_sql(command, variables)
        completed: List[Tuple[str, str, str]] = []
        for row in result:
            address = row[0]
            ethereum_address = row[1]
            developer_handle = row[4]
            if self.has_completed_two_trades(address):
                completed.append((address, ethereum_address, developer_handle))
        return completed

    def _execute_single_sql(
        self,
        command: str,
        variables: Tuple[Any, ...] = (),
        print_exceptions: bool = True,
    ) -> List[Tuple[str, ...]]:
        """Query the database - all the other functions use this under the hood."""
        conn = None
        ret: List[Tuple[str, ...]] = []
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
