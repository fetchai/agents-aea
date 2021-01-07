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
"""This module contains the tests of the RegistrationDB class of the confirmation aw2 skill."""
import datetime
import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

from packages.fetchai.skills.confirmation_aw2.registration_db import RegistrationDB

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw2.intermediate_class import (
    ConfirmationAW2TestCase,
)


class TestStrategy(ConfirmationAW2TestCase):
    """Test RegistrationDB of confirmation aw2."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw2")

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
        cls.logger = cls._skill.skill_context.logger

        cls.timestamp = datetime.datetime.now()
        cls.data = {"some_key_1": "some_value_1", "some_key_2": "some_value_2"}

        cls.developer_handle = "developer_handle"

        cls.first_trade = "2020-12-22 18:30:00.000000"
        cls.second_trade = "second_trade"
        cls.first_info = "first_info"
        cls.second_info = "second_info"

    def test__initialise_backend(self):
        """Test the _initialise_backend method of the RegistrationDB class."""
        # operation
        with patch.object(self.db, "_execute_single_sql") as mock_exe:
            self.db._initialise_backend()

        # after
        mock_exe.assert_any_call(
            "CREATE TABLE IF NOT EXISTS registered_table (address TEXT, ethereum_address TEXT, "
            "ethereum_signature TEXT, fetchai_signature TEXT, "
            "developer_handle TEXT, tweet TEXT)"
        )
        mock_exe.assert_any_call(
            "CREATE TABLE IF NOT EXISTS trade_table (address TEXT PRIMARY KEY, first_trade timestamp, "
            "second_trade timestamp, first_info TEXT, second_info TEXT)"
        )

    def test_set_trade_i(self):
        """Test the set_trade method of the RegistrationDB class where record IS None."""
        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=None
        ) as mock_get_trade_table:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_trade(
                    self.address, self.timestamp, self.data,
                )

        # after
        mock_get_trade_table.assert_called_once()
        mock_exe.assert_any_call(
            "INSERT INTO trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)",
            (self.address, self.timestamp, None, json.dumps(self.data), None),
        )

    def test_set_trade_ii(self):
        """Test the set_trade method of the RegistrationDB class where record is NOT None."""
        # setup
        record = (
            self.address,
            self.first_trade,
            None,
            self.first_info,
            self.second_info,
        )

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade_table:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_trade(
                    self.address, self.timestamp, self.data,
                )

        # after
        mock_get_trade_table.assert_called_once()

        mock_exe.assert_any_call(
            "INSERT or REPLACE into trade_table(address, first_trade, second_trade, first_info, second_info) values(?, ?, ?, ?, ?)",
            (
                self.address,
                self.first_trade,
                self.timestamp,
                self.first_info,
                json.dumps(self.data),
            ),
        )

    def test_set_trade_iii(self):
        """Test the set_trade method of the RegistrationDB class where record is NOT None and first_trade is None."""
        # setup
        record = (
            self.address,
            None,
            None,
            self.first_info,
            self.second_info,
        )

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade_table:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_trade(
                    self.address, self.timestamp, self.data,
                )

        # after
        mock_get_trade_table.assert_called_once()

        mock_exe.assert_not_called()

    def test_get_trade_table(self):
        """Test the get_trade_table method of the RegistrationDB class."""
        # setup
        trade_table = ("something_1", "something_2")
        result = [trade_table, ("something_3",)]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_trade_table = self.db.get_trade_table(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM trade_table where address=?", (self.address,)
        )
        assert actual_trade_table == trade_table

    def test_set_registered_i(self):
        """Test the set_registered method of the RegistrationDB class where is_registeredis is False."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=False
        ) as mock_is_registered:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_registered(
                    self.address, self.developer_handle,
                )

        # after
        mock_is_registered.assert_called_once()
        mock_exe.assert_any_call(
            "INSERT OR REPLACE INTO registered_table(address, ethereum_address, ethereum_signature, fetchai_signature, developer_handle, tweet) values(?, ?, ?, ?, ?, ?)",
            (self.address, "", "", "", self.developer_handle, ""),
        )

    def test_set_registered_ii(self):
        """Test the set_registered method of the RegistrationDB class where is_registeredis is True."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=True
        ) as mock_is_registered:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db.set_registered(
                    self.address, self.developer_handle,
                )

        # after
        mock_is_registered.assert_called_once()
        mock_exe.assert_not_called()

    def test_is_registered_i(self):
        """Test the is_registered method of the RegistrationDB class where result is NOT empty."""
        # setup
        result = [["1"], ["2", "3"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,)
        )
        assert is_registered

    def test_is_registered_ii(self):
        """Test the is_registered method of the RegistrationDB class where result is empty."""
        # setup
        result = []

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,)
        )
        assert not is_registered

    def test_is_allowed_to_trade_i(self):
        """Test the is_allowed_to_trade method of the RegistrationDB class where record IS None."""
        # setup
        mininum_hours_between_txs = 1
        record = None

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                is_registered = self.db.is_allowed_to_trade(
                    self.address, mininum_hours_between_txs
                )

        # after
        mock_get_trade.assert_called_once()
        mock_exe.assert_not_called()
        assert is_registered

    def test_is_allowed_to_trade_ii(self):
        """Test the is_allowed_to_trade method of the RegistrationDB class where first_trade and second_trade are NOT present."""
        # setup
        minimum_hours_between_txs = 1
        record = (self.address, None, None, self.first_info, self.second_info)

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            is_registered = self.db.is_allowed_to_trade(
                self.address, minimum_hours_between_txs
            )

        # after
        mock_get_trade.assert_called_once()
        assert is_registered

    def test_is_allowed_to_trade_iii(self):
        """Test the is_allowed_to_trade method of the RegistrationDB class where is_allowed_to_trade_ is True."""
        # setup
        minimum_hours_between_txs = 1
        record = (
            self.address,
            self.first_trade,
            None,
            self.first_info,
            self.second_info,
        )

        mocked_now_greater_than_minimum = "2020-12-22 20:30:00.000000"
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            mocked_now_greater_than_minimum, "%Y-%m-%d %H:%M:%S.%f"
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.db, "get_trade_table", return_value=record
            ) as mock_get_trade:
                is_registered = self.db.is_allowed_to_trade(
                    self.address, minimum_hours_between_txs
                )

        # after
        mock_get_trade.assert_called_once()
        assert is_registered

    def test_is_allowed_to_trade_iv(self):
        """Test the is_allowed_to_trade method of the RegistrationDB class where is_allowed_to_trade_ is False."""
        # setup
        minimum_hours_between_txs = 1
        record = (
            self.address,
            self.first_trade,
            None,
            self.first_info,
            self.second_info,
        )

        mocked_now_less_than_minimum = "2020-12-22 18:31:00.000000"

        # operation
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            mocked_now_less_than_minimum, "%Y-%m-%d %H:%M:%S.%f"
        )
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.db, "get_trade_table", return_value=record
            ) as mock_get_trade:
                with patch.object(self.logger, "log") as mock_logger:
                    is_registered = self.db.is_allowed_to_trade(
                        self.address, minimum_hours_between_txs
                    )

        # after
        mock_get_trade.assert_called_once()
        mock_logger.assert_any_call(
            logging.INFO,
            f"Invalid attempt for counterparty={self.address}, not enough time since last trade!",
        )
        assert not is_registered

    def test_is_allowed_to_trade_v(self):
        """Test the is_allowed_to_trade method of the RegistrationDB class where second_trade IS present."""
        # setup
        minimum_hours_between_txs = 1
        record = (
            self.address,
            self.first_trade,
            self.second_trade,
            self.first_info,
            self.second_info,
        )

        mocked_now = "2020-12-22 18:31:00.000000"
        # operation
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            mocked_now, "%Y-%m-%d %H:%M:%S.%f"
        )
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.db, "get_trade_table", return_value=record
            ) as mock_get_trade:
                with patch.object(self.logger, "log") as mock_logger:
                    is_registered = self.db.is_allowed_to_trade(
                        self.address, minimum_hours_between_txs
                    )

        # after
        mock_get_trade.assert_called_once()
        mock_logger.assert_any_call(
            logging.INFO,
            f"Invalid attempt for counterparty={self.address}, already completed 2 trades!",
        )
        assert not is_registered

    def test_has_completed_two_trades_i(self):
        """Test the has_completed_two_trades method of the RegistrationDB class where first and second trade are present."""
        # setup
        record = (
            self.address,
            self.first_trade,
            self.second_trade,
            self.first_info,
            self.second_info,
        )

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            has_completed = self.db.has_completed_two_trades(self.address)

        # after
        mock_get_trade.assert_called_once()
        assert has_completed

    def test_has_completed_two_trades_ii(self):
        """Test the has_completed_two_trades method of the RegistrationDB class where first and second trade are NOT present."""
        # setup
        record = (self.address, None, None, self.first_info, self.second_info)

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            has_completed = self.db.has_completed_two_trades(self.address)

        # after
        mock_get_trade.assert_called_once()
        assert not has_completed

    def test_has_completed_two_trades_iii(self):
        """Test the has_completed_two_trades method of the RegistrationDB class where first trade is NOT and second trade IS present."""
        # setup
        record = (
            self.address,
            None,
            self.second_trade,
            self.first_info,
            self.second_info,
        )

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            has_completed = self.db.has_completed_two_trades(self.address)

        # after
        mock_get_trade.assert_called_once()
        assert not has_completed

    def test_has_completed_two_trades_iv(self):
        """Test the has_completed_two_trades method of the RegistrationDB class where first trade IS and second trade is NOT present."""
        # setup
        record = (
            self.address,
            self.first_trade,
            None,
            self.first_info,
            self.second_info,
        )

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            has_completed = self.db.has_completed_two_trades(self.address)

        # after
        mock_get_trade.assert_called_once()
        assert not has_completed

    def test_has_completed_two_trades_v(self):
        """Test the has_completed_two_trades method of the RegistrationDB class where record IS None."""
        # setup
        record = None

        # operation
        with patch.object(
            self.db, "get_trade_table", return_value=record
        ) as mock_get_trade:
            has_completed = self.db.has_completed_two_trades(self.address)

        # after
        mock_get_trade.assert_called_once()
        assert not has_completed

    def test_completed_two_trades(self):
        """Test the completed_two_trades method of the RegistrationDB class."""
        # setup
        row_1 = (
            "address_1",
            "ethereum_address_1",
            "something2_1",
            "something3_1",
            "developer_handle_1",
        )
        row_2 = (
            "address_2",
            "ethereum_address_2",
            "something2_2",
            "something3_2",
            "developer_handle_2",
        )
        row_3 = (
            "address_3",
            "ethereum_address_3",
            "something2_3",
            "something3_3",
            "developer_handle_3",
        )
        result = [row_1, row_2, row_3]

        has_completed = [True, False, True]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            with patch.object(
                self.db, "has_completed_two_trades", side_effect=has_completed
            ):
                actual_completed = self.db.completed_two_trades()

        # after
        mock_exe.assert_any_call("SELECT * FROM registered_table", ())
        assert actual_completed == [
            ("address_1", "ethereum_address_1", "developer_handle_1"),
            ("address_3", "ethereum_address_3", "developer_handle_3"),
        ]
