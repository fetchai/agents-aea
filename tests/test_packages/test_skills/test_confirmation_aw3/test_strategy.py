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
"""This module contains the tests of the strategy class of the confirmation aw3 skill."""

import datetime
import json
import logging
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

import pytest

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.confirmation_aw3.registration_db import RegistrationDB
from packages.fetchai.skills.confirmation_aw3.strategy import (
    HTTP_CLIENT_PUBLIC_ID,
    Strategy,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw3.intermediate_class import (
    ConfirmationAW3TestCase,
)


class TestStrategy(ConfirmationAW3TestCase):
    """Test Strategy of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.location_name = "berlin"
        cls.locations = {
            cls.location_name: {"latitude": 52.52, "longitude": 13.405},
        }
        cls.search_query_type = "weather"
        cls.search_queries = {
            cls.search_query_type: {
                "constraint_type": "==",
                "search_key": "seller_service",
                "search_value": "weather_data",
            },
        }
        cls.leaderboard_url = "some_url"
        cls.leaderboard_token = "some_token"

        cls.strategy = Strategy(
            aw1_aea="some_aw1_aea",
            locations=cls.locations,
            search_queries=cls.search_queries,
            leaderboard_url=cls.leaderboard_url,
            leaderboard_token=cls.leaderboard_token,
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
        assert self.strategy._locations == self.locations
        assert self.strategy._search_queries == self.search_queries
        assert self.strategy.leaderboard_url == f"{self.leaderboard_url}/insert"
        assert self.strategy.leaderboard_token == self.leaderboard_token

    def test__init__ii(self):
        """Test the __init__ of Strategy class where aw1_aea is None."""
        with pytest.raises(ValueError, match="aw1_aea must be provided!"):
            Strategy(
                aw1_aea=None,
                locations=self.locations,
                search_queries=self.search_queries,
                leaderboard_url=self.leaderboard_url,
                leaderboard_token=self.leaderboard_token,
                name="strategy",
                skill_context=self.skill.skill_context,
            )

    def test__init__iii(self):
        """Test the __init__ of Strategy class where length of locations is 0."""
        with pytest.raises(ValueError, match="locations must have at least one entry"):
            Strategy(
                aw1_aea="some_aw1_aea",
                locations={},
                search_queries=self.search_queries,
                leaderboard_url=self.leaderboard_url,
                leaderboard_token=self.leaderboard_token,
                name="strategy",
                skill_context=self.skill.skill_context,
            )

    def test__init__iv(self):
        """Test the __init__ of Strategy class where length of search_queries is 0."""
        with pytest.raises(
            ValueError, match="search_queries must have at least one entry"
        ):
            Strategy(
                aw1_aea="some_aw1_aea",
                locations=self.locations,
                search_queries={},
                leaderboard_url=self.leaderboard_url,
                leaderboard_token=self.leaderboard_token,
                name="strategy",
                skill_context=self.skill.skill_context,
            )

    def test__init__v(self):
        """Test the __init__ of Strategy class where leaderboard_url is None."""
        with pytest.raises(ValueError, match="No leader board url provided!"):
            Strategy(
                aw1_aea="some_aw1_aea",
                locations=self.locations,
                search_queries=self.search_queries,
                leaderboard_url=None,
                leaderboard_token=self.leaderboard_token,
                name="strategy",
                skill_context=self.skill.skill_context,
            )

    def test__init__vi(self):
        """Test the __init__ of Strategy class where leaderboard_token is None."""
        with pytest.raises(ValueError, match="No leader board token provided!"):
            Strategy(
                aw1_aea="some_aw1_aea",
                locations=self.locations,
                search_queries=self.search_queries,
                leaderboard_url=self.leaderboard_url,
                leaderboard_token=None,
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

    def test_is_valid_counterparty_i(self):
        """Test the is_valid_counterparty method of the Strategy class where is_registered is False."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=False
        ) as mock_is_regostered:
            with patch.object(self.logger, "log") as mock_logger:
                is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        mock_is_regostered.assert_any_call(self.counterparty)
        mock_logger.assert_any_call(
            logging.INFO, f"Invalid counterparty={self.counterparty}, not registered!",
        )
        assert is_valid is False

    def test_is_valid_counterparty_ii(self):
        """Test the is_valid_counterparty method of the Strategy class where is_registered is True."""
        # operation
        with patch.object(
            self.db, "is_registered", return_value=True
        ) as mock_is_regostered:
            is_valid = self.strategy.is_valid_counterparty(self.counterparty)

        # after
        mock_is_regostered.assert_any_call(self.counterparty)
        assert is_valid is True

    def test_successful_trade_with_counterparty(self):
        """Test the successful_trade_with_counterparty method of the Strategy class."""
        # setup
        data = {"some_key_1": "some_value_1", "some_key_2": "some_value_2"}
        developer_handle = "some_developer_handle"
        nb_trades = 5

        mocked_now_str = "2020-12-22 20:33:00.000000"
        mock_now = datetime.datetime.strptime(mocked_now_str, "%Y-%m-%d %H:%M:%S.%f")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_now

        # operation
        with patch.object(self.db, "set_trade") as mock_set_trade:
            with patch("datetime.datetime", new=datetime_mock):
                with patch.object(self.logger, "log") as mock_logger:
                    with patch.object(
                        self.db,
                        "get_handle_and_trades",
                        return_value=(developer_handle, nb_trades),
                    ) as mock_handle:
                        self.strategy.successful_trade_with_counterparty(
                            self.counterparty, data
                        )

        # after
        mock_set_trade.assert_any_call(self.counterparty, mock_now, data)
        mock_handle.assert_any_call(self.counterparty)

        mock_logger.assert_any_call(
            logging.INFO, f"Successful trade with={self.counterparty}.",
        )

        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method="POST",
            url=self.strategy.leaderboard_url,
            headers="Content-Type: application/json; charset=utf-8",
            version="",
            body=json.dumps(
                {
                    "name": developer_handle,
                    "points": nb_trades,
                    "token": self.leaderboard_token,
                }
            ).encode("utf-8"),
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Notifying leaderboard: developer_handle={developer_handle}, nb_trades={nb_trades}.",
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

    def test_update_search_query_params(self):
        """Test the update_search_query_params method of the Strategy class."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.strategy.update_search_query_params()

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"New search_type={self.search_query_type} and location={self.location_name}.",
        )
