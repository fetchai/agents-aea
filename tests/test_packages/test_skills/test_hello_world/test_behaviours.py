# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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
"""Tests for hello_world skill's behaviour."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.hello_world.behaviours import HelloWorld

from tests.conftest import ROOT_DIR


class TestHelloWorld(BaseSkillTestCase):
    """Test HelloWorld behaviour of hello world."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "hello_world")
    is_agent_to_agent_messages = False

    def setup_method(self):
        """Set up the test environment."""
        self.message = "Hello Something Custom!"
        config_overrides = {
            "behaviours": {"hello_world": {"args": {"message": self.message}}}
        }

        super().setup(config_overrides=config_overrides)
        self.hello_world_behaviour = cast(
            HelloWorld, self._skill.skill_context.behaviours.hello_world
        )
        self.logger = self._skill.skill_context.logger

    def test_act(self):
        """Test the act method of the hello_world behaviour."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            assert self.hello_world_behaviour.act() is None

        # after
        mock_logger.assert_any_call(logging.INFO, self.message)
