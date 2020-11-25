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
"""This module contains the tests of the strategy class of the simple seller skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.simple_seller.strategy import Strategy

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of simple seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "simple_seller")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.mocked_name_of_data = "some_name_for_data"
        config_overrides = {
            "models": {
                "strategy": {"args": {"shared_state_key": cls.mocked_name_of_data}}
            }
        }

        super().setup(config_overrides=config_overrides)

        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.mocked_data_1 = (
            b'[{"type_1": "data_1", "type_2": "data_2", "type_3": "data_3"}]'
        )
        cls.mocked_data_2 = (
            b'{"type_1": "data_1", "type_2": "data_2", "type_3": "data_3"}'
        )
        cls.mocked_data_3 = b"some_non_jason_data"

    def test__init__(self):
        """Test the __init__ method of the Strategy class."""
        with pytest.raises(ValueError, match="No shared_state_key provided!"):
            Strategy(shared_state_key=None)

    def test_collect_from_data_source_i(self):
        """Test the collect_from_data_source method of the Strategy class where the data is NOT a dictionary."""
        self.skill.skill_context._agent_context._shared_state[
            self.mocked_name_of_data
        ] = self.mocked_data_1
        expected_formatted_data = {
            "data": '[{"type_1": "data_1", "type_2": "data_2", "type_3": "data_3"}]'
        }

        actual_data = self.strategy.collect_from_data_source()
        assert actual_data == expected_formatted_data

    def test_collect_from_data_source_ii(self):
        """Test the collect_from_data_source method of the Strategy class where the data IS a dictionary."""
        self.skill.skill_context._agent_context._shared_state[
            self.mocked_name_of_data
        ] = self.mocked_data_2
        expected_formatted_data = {
            "type_1": "data_1",
            "type_2": "data_2",
            "type_3": "data_3",
        }

        actual_data = self.strategy.collect_from_data_source()
        assert actual_data == expected_formatted_data

    def test_format_data_exception(self):
        """Test the _format_data method of the Strategy class where JSONDecodeError raises."""
        with patch.object(self.skill.skill_context.logger, "log") as mock_logger:
            self.strategy._format_data(self.mocked_data_3)

        mock_logger.assert_any_call(
            logging.WARNING,
            f"error when loading json: {'Expecting value: line 1 column 1 (char 0)'}",
        )
