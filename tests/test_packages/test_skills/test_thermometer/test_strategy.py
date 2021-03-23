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
"""This module contains the tests of the strategy class of the thermometer skill."""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.thermometer.strategy import MAX_RETRIES, Strategy

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of thermometer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "thermometer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.strategy = Strategy(
            name="strategy", skill_context=cls._skill.skill_context,
        )
        cls.logger = cls._skill.skill_context.logger

    def test_collect_from_data_source_i(self):
        """Test the collect_from_data_source method of the Strategy class where max retires result is successful."""
        # setup
        temp = 24
        results = [{"internal temperature": temp, "some_other_info": "some_info"}]
        expected_degree = {"thermometer_data": str(temp)}

        temper_mock = Mock()
        temper_mock.read.return_value = results

        # operation
        with patch("temper.Temper.__init__", return_value=None) as mock_init:
            with patch("temper.Temper.read", return_value=results) as mock_read:
                with patch.object(self.logger, "log") as mock_logger:
                    degree = self.strategy.collect_from_data_source()

        # after
        mock_init.assert_called_once()
        mock_read.assert_called_once()
        mock_logger.assert_not_called()
        assert degree == expected_degree

    def test_collect_from_data_source_ii(self):
        """Test the collect_from_data_source method of the Strategy class where max retires result is successful."""
        # setup
        temp = 24
        results = [{"NOT internal temperature": temp, "some_other_info": "some_info"}]

        temper_mock = Mock()
        temper_mock.read.return_value = results

        # operation
        with patch("temper.Temper.__init__", return_value=None) as mock_init:
            with patch("temper.Temper.read", return_value=results) as mock_read:
                with patch.object(self.logger, "log") as mock_logger:
                    degree = self.strategy.collect_from_data_source()

        # after
        mock_init.assert_called_once()
        assert mock_read.call_count == MAX_RETRIES
        mock_logger.assert_any_call(
            logging.DEBUG, "Couldn't read the sensor I am re-trying."
        )
        assert degree == {}
