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
from collections import defaultdict
from typing import Any, Dict, List, Tuple, cast

from aea.skills.base import Model


_default_logger = logging.getLogger(
    "aea.packages.fetchai.skills.confirmation_aw3.registration_db"
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
            "CREATE TABLE IF NOT EXISTS registered_table (address TEXT NOT NULL, ethereum_address TEXT, "
            "ethereum_signature TEXT, fetchai_signature TEXT, "
            "developer_handle TEXT NOT NULL, tweet TEXT, PRIMARY KEY (address, developer_handle))"
        )
        self._execute_single_sql(
            "CREATE TABLE IF NOT EXISTS trades_table (address TEXT, created_at timestamp, data TEXT)"
        )

    def set_trade(
        self, address: str, timestamp: datetime.datetime, data: Dict[str, str],
    ) -> None:
        """Record a registration."""
        command = "INSERT INTO trades_table(address, created_at, data) values(?, ?, ?)"
        variables: Tuple[str, datetime.datetime, str] = (
            address,
            timestamp,
            json.dumps(data),
        )
        self._execute_single_sql(command, variables)

    def get_trade_count(self, address: str) -> int:
        """Get trade count."""
        command = "SELECT COUNT(*) FROM trades_table where address=?"
        ret = self._execute_single_sql(command, (address,))
        return int(ret[0][0])

    def get_developer_handle(self, address: str) -> str:
        """Get developer handle for address."""
        command = "SELECT developer_handle FROM registered_table where address=?"
        ret = self._execute_single_sql(command, (address,))
        if len(ret[0]) != 1:
            raise ValueError(
                f"More than one developer_handle found for address={address}."
            )
        return ret[0][0]

    def get_addresses(self, developer_handle: str) -> List[str]:
        """Get addresses for developer handle."""
        command = "SELECT address FROM registered_table where developer_handle=?"
        ret = self._execute_single_sql(command, (developer_handle,))
        addresses = [address[0] for address in ret]
        if len(addresses) == 0:
            raise ValueError(
                f"Should find at least one address for developer_handle={developer_handle}."
            )
        return addresses

    def get_handle_and_trades(self, address: str) -> Tuple[str, int]:
        """Get developer and number of trades for address."""
        developer_handle = self.get_developer_handle(address)
        addresses = self.get_addresses(developer_handle)
        trades = 0
        for address_ in addresses:
            trades += self.get_trade_count(address_)
        return (developer_handle, trades)

    def get_all_addresses_and_handles(self) -> List[Tuple[str, str]]:
        """Get all addresses."""
        command = "SELECT address, developer_handle FROM registered_table"
        results = cast(List[Tuple[str, str]], self._execute_single_sql(command, ()))
        return results

    def get_leaderboard(self) -> List[Tuple[str, str, int]]:
        """Get the leader board."""
        addresses_and_handles = self.get_all_addresses_and_handles()
        results_dir: Dict[Tuple[str, str], int] = defaultdict(int)
        for address, developer_handle in addresses_and_handles:
            trades = self.get_trade_count(address)
            if trades == 0:
                continue
            results_dir[(address, developer_handle)] += trades
        results = [(k[0], k[1], v) for k, v in results_dir.items()]
        results.sort(key=lambda x: x[2], reverse=True)
        return results

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
