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
"""This module contains the tests of the strategy class of the confirmation aw2 skill."""

import datetime
import logging
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

import pytest

from packages.fetchai.skills.confirmation_aw2.registration_db import RegistrationDB
from packages.fetchai.skills.confirmation_aw2.strategy import Strategy

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw2.intermediate_class import (
    ConfirmationAW2TestCase,
)


class TestStrategy(ConfirmationAW2TestCase):
    """Test Strategy of confirmation aw2."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw2")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.minimum_hours_between_txs = 4
        cls.minimum_minutes_since_last_attempt = 2
        cls.strategy = Strategy(
            aw1_aea="some_aw1_aea",
            mininum_hours_between_txs=cls.minimum_hours_between_txs,
            minimum_minutes_since_last_attempt=cls.minimum_minutes_since_last_attempt,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

        cls.address = "some_address"
        cls.info = {
            "ethereum_address": "some_value",
            "signature_of_ethereum_address": "some_signature_of_ethereum_address",
            "signature_of_fetchai_address": "some_signature_of_fetchai_address",
            "developer_handle": "some_developer_handle",
            "tweet": "some_tweet",
        }
        cls.logger = cls._skill.skill_context.logger
        cls.db = cast(RegistrationDB, cls._skill.skill_context.registration_db)

        cls.counterparty = "couterparty_1"

    def test__init__i(self):
        """Test the __init__ of Strategy class."""
        assert self.strategy.aw1_aea == self.aw1_aea
        assert self.strategy.minimum_hours_between_txs == self.minimum_hours_between_txs
        assert (
            self.strategy.minimum_minutes_since_last_attempt
            == self.minimum_minutes_since_last_attempt
        )

    def test__init__ii(self):
        """Test the __init__ of Strategy class where aw1_aea is None."""
        with pytest.raises(ValueError, match="aw1_aea must be provided!"):
            Strategy(
                aw1_aea=None,
                mininum_hours_between_txs=self.minimum_hours_between_txs,
                minimum_minutes_since_last_attempt=self.minimum_minutes_since_last_attempt,
                name="strategy",
                skill_context=self.skill.skill_context,
            )

    def test_get_acceptable_counterparties(self):
        """Test the get_acceptable_counterparties method of the Strategy class."""
        # setup
        couterparties = ("couterparty_1", "couterparty_2", "couterparty_3")
        is_valid_counterparty = [True, False, True]

        # operation
        with patch.object(
            self.strategy, "is_valid_counterparty", side_effect=is_valid_counterparty
        ):
            actual_acceptable_counterparties = self.strategy.get_acceptable_counterparties(
                couterparties
            )

        # after
        assert actual_acceptable_counterparties == ("couterparty_1", "couterparty_3")

    def test_is_enough_time_since_last_attempt_i(self):
        """Test the is_enough_time_since_last_attempt method of the Strategy class where now IS greater than last attempt + min minutes."""
        # setup
        counterparty_last_attempt_time_str = "2020-12-22 20:30:00.000000"
        counterparty_last_attempt_time = datetime.datetime.strptime(
            counterparty_last_attempt_time_str, "%Y-%m-%d %H:%M:%S.%f"
        )

        mocked_now_greater_than_last_plus_minimum = "2020-12-22 20:33:00.000000"
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            mocked_now_greater_than_last_plus_minimum, "%Y-%m-%d %H:%M:%S.%f"
        )
        self.strategy.last_attempt = {self.counterparty: counterparty_last_attempt_time}

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            is_enough_time = self.strategy.is_enough_time_since_last_attempt(
                self.counterparty
            )

        # after
        assert is_enough_time is True

    def test_is_enough_time_since_last_attempt_ii(self):
        """Test the is_enough_time_since_last_attempt method of the Strategy class where now is NOT greater than last attempt + min minutes."""
        # setup
        counterparty_last_attempt_time_str = "2020-12-22 20:30:00.000000"
        counterparty_last_attempt_time = datetime.datetime.strptime(
            counterparty_last_attempt_time_str, "%Y-%m-%d %H:%M:%S.%f"
        )

        mocked_now_less_than_last_plus_minimum = "2020-12-22 20:31:00.000000"
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime.strptime(
            mocked_now_less_than_last_plus_minimum, "%Y-%m-%d %H:%M:%S.%f"
        )
        self.strategy.last_attempt = {self.counterparty: counterparty_last_attempt_time}

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            is_enough_time = self.strategy.is_enough_time_since_last_attempt(
                self.counterparty
            )

        # after
        assert is_enough_time is False

    def test_is_enough_time_since_last_attempt_iii(self):
        """Test the is_enough_time_since_last_attempt method of the Strategy class where now counterparty is NOT in last_attempt."""
        # setup
        self.strategy.last_attempt = {}

        # operation
        is_enough_time = self.strategy.is_enough_time_since_last_attempt(
            self.counterparty
        )

        # after
        assert is_enough_time is True

    def test_is_valid_counterparty_i(self):
        """Test the is_valid_counterparty method of the Strategy class where is_registered is False."""
        # operation
        with patch.object(self.db, "is_registered", return_value=False):
            with patch.object(self.logger, "log") as mock_logger:
                is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"Invalid counterparty={self.counterparty}, not registered!",
        )
        assert is_valid is False

    def test_is_valid_counterparty_ii(self):
        """Test the is_valid_counterparty method of the Strategy class where is_enough_time_since_last_attempt is False."""
        # operation
        with patch.object(self.db, "is_registered", return_value=True):
            with patch.object(
                self.strategy, "is_enough_time_since_last_attempt", return_value=False
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"Not enough time since last attempt for counterparty={self.counterparty}!",
        )
        assert is_valid is False

    def test_is_valid_counterparty_iii(self):
        """Test the is_valid_counterparty method of the Strategy class where is_allowed_to_trade is False."""
        # operation
        with patch.object(self.db, "is_registered", return_value=True):
            with patch.object(
                self.strategy, "is_enough_time_since_last_attempt", return_value=True
            ):
                with patch.object(self.db, "is_allowed_to_trade", return_value=False):
                    is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        assert is_valid is False

    def test_is_valid_counterparty_iv(self):
        """Test the is_valid_counterparty method of the Strategy class where it succeeds."""
        # operation
        with patch.object(self.db, "is_registered", return_value=True):
            with patch.object(
                self.strategy, "is_enough_time_since_last_attempt", return_value=True
            ):
                with patch.object(self.db, "is_allowed_to_trade", return_value=True):
                    is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        assert is_valid is True

    def test_successful_trade_with_counterparty(self):
        """Test the successful_trade_with_counterparty method of the Strategy class."""
        # setup
        data = {"some_key_1": "some_value_1", "some_key_2": "some_value_2"}

        mocked_now_str = "2020-12-22 20:33:00.000000"
        mock_now = datetime.datetime.strptime(mocked_now_str, "%Y-%m-%d %H:%M:%S.%f")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_now

        # operation
        with patch.object(self.db, "set_trade") as mock_set_trade:
            with patch("datetime.datetime", new=datetime_mock):
                with patch.object(self.logger, "log") as mock_logger:
                    self.strategy.successful_trade_with_counterparty(
                        self.counterparty, data
                    )

        # after
        mock_set_trade.assert_any_call(self.counterparty, mock_now, data)

        mock_logger.assert_any_call(
            logging.INFO,
            f"Successful trade with={self.counterparty}. Data acquired={data}!",
        )

    def test_register_counterparty(self):
        """Test the register_counterparty method of the Strategy class."""
        # setup
        developer_handle = "some_developer_handle"

        # operation
        with patch.object(self.db, "set_registered") as mock_set_registered:
            self.strategy.register_counterparty(self.counterparty, developer_handle)

        # after
        mock_set_registered.assert_any_call(self.counterparty, developer_handle)
