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
"""This module contains the tests of the RegistrationDB class of the confirmation aw3 skill."""
import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from packages.fetchai.skills.confirmation_aw3.registration_db import RegistrationDB

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw3.intermediate_class import (
    ConfirmationAW3TestCase,
)


class TestStrategy(ConfirmationAW3TestCase):
    """Test RegistrationDB of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.custom_path = None
        cls.db = RegistrationDB(
            custom_path=cls.custom_path,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

        cls.address = "some_address"
        cls.timestamp = datetime.datetime.now()
        cls.data = {"some_key_1": "some_value_1", "some_key_2": "some_value_2"}
        cls.developer_handle = "developer_handle"

    def test_set_trade(self):
        """Test the set_trade method of the RegistrationDB class."""
        # operation
        with patch.object(self.db, "_execute_single_sql") as mock_exe:
            self.db.set_trade(
                self.address, self.timestamp, self.data,
            )

        # after
        mock_exe.assert_any_call(
            "INSERT INTO trades_table(address, created_at, data) values(?, ?, ?)",
            (self.address, self.timestamp, json.dumps(self.data)),
        )

    def test_get_trade_count(self):
        """Test the get_trade_count method of the RegistrationDB class."""
        # setup
        result = [["1", "2"], ["3", "4"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_result = self.db.get_trade_count(self.address,)

        # after
        mock_exe.assert_any_call(
            "SELECT COUNT(*) FROM trades_table where address=?", (self.address,),
        )
        assert actual_result == 1

    def test_get_developer_handle_i(self):
        """Test the get_developer_handle method of the RegistrationDB class which succeeds."""
        # setup
        result = [["developer_handle"], ["something_1", "something_2"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_result = self.db.get_developer_handle(self.address,)

        # after
        mock_exe.assert_any_call(
            "SELECT developer_handle FROM registered_table where address=?",
            (self.address,),
        )
        assert actual_result == "developer_handle"

    def test_get_developer_handle_ii(self):
        """Test the get_developer_handle method of the RegistrationDB class where the length of result[0] != 1."""
        # setup
        result = [["developer_handle", "something_1"], ["something_2", "something_3"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            with pytest.raises(
                ValueError,
                match=f"More than one developer_handle found for address={self.address}.",
            ):
                self.db.get_developer_handle(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT developer_handle FROM registered_table where address=?",
            (self.address,),
        )

    def test_get_addresses_i(self):
        """Test the get_addresses method of the RegistrationDB class where there are more than 0 addresses."""
        # setup
        result = [["address_1", "something_1"], ["address_2", "something_2"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_addresses = self.db.get_addresses(self.developer_handle,)

        # after
        mock_exe.assert_any_call(
            "SELECT address FROM registered_table where developer_handle=?",
            (self.developer_handle,),
        )
        assert actual_addresses == ["address_1", "address_2"]

    def test_get_addresses_ii(self):
        """Test the get_addresses method of the RegistrationDB class where there are 0 addresses."""
        # setup
        result = []

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            with pytest.raises(
                ValueError,
                match=f"Should find at least one address for developer_handle={self.developer_handle}.",
            ):
                self.db.get_addresses(self.developer_handle,)

        # after
        mock_exe.assert_any_call(
            "SELECT address FROM registered_table where developer_handle=?",
            (self.developer_handle,),
        )

    def test_get_handle_and_trades(self):
        """Test the get_handle_and_trades method of the RegistrationDB class."""
        # setup
        result = ["address_1", "address_2"]
        trade_counts = [2, 5]

        # operation
        with patch.object(
            self.db, "get_developer_handle", return_value=self.developer_handle
        ) as mock_developer_handle:
            with patch.object(
                self.db, "get_addresses", return_value=result
            ) as mock_addresses:
                with patch.object(
                    self.db, "get_trade_count", side_effect=trade_counts
                ) as mock_trade_counts:
                    actual_addresses = self.db.get_handle_and_trades(self.address,)

        # after
        mock_developer_handle.assert_any_call(self.address)
        mock_addresses.assert_any_call(self.developer_handle)
        mock_trade_counts.assert_called()

        assert actual_addresses == (self.developer_handle, sum(trade_counts))

    def test_get_all_addresses_and_handles(self):
        """Test the get_all_addresses_and_handles method of the RegistrationDB class."""
        # setup
        result = [("address_1", "something_1"), ("address_2", "something_2")]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_result = self.db.get_all_addresses_and_handles()

        # after
        mock_exe.assert_any_call(
            "SELECT address, developer_handle FROM registered_table", ()
        )
        assert actual_result == result

    def test_get_leaderboard_i(self):
        """Test the get_leaderboard method of the RegistrationDB class where none of the number of trades are 0."""
        # setup
        addresses_and_handlers = [
            ("address_1", "handler_1"),
            ("address_2", "handler_2"),
        ]
        trade_counts = [2, 5]

        expected_result = [("address_2", "handler_2", 5), ("address_1", "handler_1", 2)]

        # operation
        with patch.object(
            self.db,
            "get_all_addresses_and_handles",
            return_value=addresses_and_handlers,
        ) as mock_get_addresses:
            with patch.object(
                self.db, "get_trade_count", side_effect=trade_counts
            ) as mock_trade_counts:
                actual_result = self.db.get_leaderboard()

        # after
        mock_get_addresses.assert_called_once()
        mock_trade_counts.assert_called()

        assert actual_result == expected_result

    def test_get_leaderboard_ii(self):
        """Test the get_leaderboard method of the RegistrationDB class where some number of trades are 0."""
        # setup
        addresses_and_handlers = [
            ("address_1", "handler_1"),
            ("address_2", "handler_2"),
        ]
        trade_counts = [2, 0]

        expected_result = [("address_1", "handler_1", 2)]

        # operation
        with patch.object(
            self.db,
            "get_all_addresses_and_handles",
            return_value=addresses_and_handlers,
        ) as mock_get_addresses:
            with patch.object(
                self.db, "get_trade_count", side_effect=trade_counts
            ) as mock_trade_counts:
                actual_result = self.db.get_leaderboard()

        # after
        mock_get_addresses.assert_called_once()
        mock_trade_counts.assert_called()

        assert actual_result == expected_result

    def test_set_registered_i(self):
        """Test the set_registered method of the RegistrationDB class where is_registered is False."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=False
        ) as mock_registered:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_registered(self.address, self.developer_handle)

        # after
        mock_registered.assert_any_call(self.address)
        mock_exe.assert_any_call(
            "INSERT OR REPLACE INTO registered_table(address, ethereum_address, ethereum_signature, fetchai_signature, developer_handle, tweet) values(?, ?, ?, ?, ?, ?)",
            (self.address, "", "", "", self.developer_handle, ""),
        )

    def test_set_registered_ii(self):
        """Test the set_registered method of the RegistrationDB class where is_registered is True."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=True
        ) as mock_registered:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_registered(self.address, self.developer_handle)

        # after
        mock_registered.assert_any_call(self.address)
        mock_exe.assert_not_called()

    def test_is_registered_i(self):
        """Test the is_registered method of the RegistrationDB class where result's length is more than 0."""
        # setup
        result = [("address_1", "something_1"), ("address_2", "something_2")]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,),
        )
        assert is_registered is True

    def test_is_registered_ii(self):
        """Test the is_registered method of the RegistrationDB class where result's length is 0."""
        # setup
        result = []

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,),
        )
        assert is_registered is False
