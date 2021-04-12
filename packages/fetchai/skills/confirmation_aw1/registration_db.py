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

import logging
import os
import sqlite3
from typing import Any, List, Tuple

from aea.skills.base import Model


_default_logger = logging.getLogger(
    "aea.packages.fetchai.skills.carpark_detection.detection_database"
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
        if os.path.isfile(self.db_path):
            return
        self._execute_single_sql(
            "CREATE TABLE IF NOT EXISTS registered_table (address TEXT, ethereum_address TEXT, "
            "ethereum_signature TEXT, fetchai_signature TEXT, "
            "developer_handle TEXT, tweet TEXT)"
        )

    def set_registered(
        self,
        address: str,
        ethereum_address: str,
        ethereum_signature: str,
        fetchai_signature: str,
        developer_handle: str,
        tweet: str,
    ) -> None:
        """Record a registration."""
        command = "INSERT OR REPLACE INTO registered_table(address, ethereum_address, ethereum_signature, fetchai_signature, developer_handle, tweet) values(?, ?, ?, ?, ?, ?)"
        variables = (
            address,
            ethereum_address,
            ethereum_signature,
            fetchai_signature,
            developer_handle,
            tweet,
        )
        self._execute_single_sql(command, variables)

    def set_registered_developer_only(
        self, address: str, developer_handle: str,
    ) -> None:
        """Record a registration."""
        command = "INSERT OR REPLACE INTO registered_table(address, developer_handle) values(?, ?)"
        variables = (
            address,
            developer_handle,
        )
        self._execute_single_sql(command, variables)

    def is_registered(self, address: str) -> bool:
        """Check if an address is registered."""
        command = "SELECT * FROM registered_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        return len(result) != 0

    def get_developer_handle(self, address: str) -> str:
        """Get developer handle relating to an address."""
        command = "SELECT developer_handle FROM registered_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        if len(result[0]) != 1:
            raise ValueError(
                f"More than one developer_handle found for address={address}."
            )
        return result[0][0]

    def get_ethereum_address(
        self, address: str, developer_handle: str
    ) -> str:  # pragma: no cover
        """Get ethereum address relating to an address (hacky for backwards compatibility)."""
        command = "SELECT ethereum_address FROM registered_table WHERE address=?"
        variables = (address,)
        result = self._execute_single_sql(command, variables)
        if len(result) != 0 and len(result[0]) != 1:
            raise ValueError(
                f"More than one ethereum_address found for address={address}."
            )
        if len(result) != 0 and (result[0][0] != "" or developer_handle == ""):
            return result[0][0]
        command = (
            "SELECT ethereum_address FROM registered_table WHERE developer_handle=?"
        )
        variables = (developer_handle,)
        result = self._execute_single_sql(command, variables)
        if len(result) == 0:
            raise ValueError(
                f"No ethereum_address found for address={address} and developer_handle={developer_handle}."
            )
        if len(result[0]) != 1:
            raise ValueError(
                f"More than one ethereum_address found for developer_handle={developer_handle}."
            )
        return result[0][0]

    def get_all_registered(self) -> List[str]:
        """Get all registered AW-1 AEAs."""
        command = "SELECT address FROM registered_table"
        variables = ()
        results = self._execute_single_sql(command, variables)
        registered = [result[0] for result in results]
        return registered

    def _execute_single_sql(
        self,
        command: str,
        variables: Tuple[str, ...] = (),
        print_exceptions: bool = True,
    ) -> List[Tuple[str, ...]]:
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
