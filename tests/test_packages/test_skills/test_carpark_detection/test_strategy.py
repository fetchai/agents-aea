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
"""This module contains the tests of the strategy class of the carpark detection skill."""

from pathlib import Path
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.carpark_detection.strategy import (
    DEFAULT_DB_IS_REL_TO_CWD,
    DEFAULT_DB_REL_DIR,
    Strategy,
)

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of carpark detection."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "carpark_detection")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.db_is_rel_to_cwd = DEFAULT_DB_IS_REL_TO_CWD
        cls.db_rel_dir = DEFAULT_DB_REL_DIR

        cls.strategy = Strategy(
            db_is_rel_to_cwd=cls.db_is_rel_to_cwd,
            db_rel_dir=cls.db_rel_dir,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test__init__i(self):
        """Test the __init__ method of the Strategy class where db_dir does NOT exist."""
        # operation
        with patch("os.path.isdir", return_value=False):
            with pytest.raises(ValueError, match="Database directory does not exist!"):
                Strategy(
                    db_is_rel_to_cwd=self.db_is_rel_to_cwd,
                    db_rel_dir=self.db_rel_dir,
                    name="strategy",
                    skill_context=self.skill.skill_context,
                )

    def test__init__ii(self):
        """Test the __init__ method of the Strategy class where db_is_rel_to_cwd is True."""
        # operation
        with patch("os.path.isdir", return_value=True):
            with patch.object(self.strategy, "_update_service_data") as mock_update:
                self.strategy.__init__(
                    db_is_rel_to_cwd=True,
                    db_rel_dir=self.db_rel_dir,
                    name="strategy",
                    skill_context=self.skill.skill_context,
                )

        mock_update.assert_called_once()

    def test_update_service_data(self):
        """Test the _update_service_data method of the Strategy class."""
        lat = 2
        lon = 3

        # operation
        with patch.object(
            self.strategy.db, "is_db_exits", return_value=True
        ) as mock_db_exists:
            with patch.object(
                self.strategy.db, "get_latest_detection_data", return_value=[1, 2]
            ) as mock_latest_detection:
                with patch.object(
                    self.strategy.db, "get_lat_lon", return_value=(lat, lon)
                ) as mock_lat_lon:
                    self.strategy._update_service_data()

        # after
        mock_db_exists.assert_called_once()
        mock_latest_detection.assert_any_call(1)
        mock_lat_lon.assert_called_once()
        assert self.strategy._service_data == {
            "latitude": lat,
            "longitude": lon,
        }

    def test_collect_from_data_source_i(self):
        """Test the collect_from_data_source method of the Strategy class where len(data)>0."""
        # setup
        free_spaces = 24
        data = [
            {
                "epoch": "some_epoch",
                "raw_image_path": "some_raw_image_path",
                "processed_image_path": "some_processed_image_path",
                "total_count": "some_total_count",
                "moving_count": "some_moving_count",
                "free_spaces": free_spaces,
                "lat": "some_lat",
                "lon": "some_lon",
            },
            {
                "epoch": "some_other_epoch",
                "raw_image_path": "some_other_raw_image_path",
                "processed_image_path": "some_other_processed_image_path",
                "total_count": "some_other_total_count",
                "moving_count": "some_other_moving_count",
                "free_spaces": 10,
                "lat": "some_other_lat",
                "lon": "some_other_lon",
            },
            {
                "epoch": "some_yet_another_epoch",
                "raw_image_path": "some_yet_another_raw_image_path",
                "processed_image_path": "some_yet_another_processed_image_path",
                "total_count": "some_yet_another_total_count",
                "moving_count": "some_yet_another_moving_count",
                "free_spaces": 2,
                "lat": "some_yet_another_lat",
                "lon": "some_yet_another_lon",
            },
        ]
        expected_result = {"free_spaces": str(free_spaces)}

        # operation
        with patch.object(
            self.strategy.db, "get_latest_detection_data", return_value=data
        ) as mock_get_data:
            result = self.strategy.collect_from_data_source()

        # after
        mock_get_data.assert_any_call(1)
        assert result == expected_result

    def test_collect_from_data_source_ii(self):
        """Test the collect_from_data_source method of the Strategy class where len(data)==0."""
        # setup
        data = []

        # operation
        with patch.object(
            self.strategy.db, "get_latest_detection_data", return_value=data
        ) as mock_get_data:
            with pytest.raises(AEAEnforceError, match="Did not find any data."):
                self.strategy.collect_from_data_source()

        # after
        mock_get_data.assert_any_call(1)
