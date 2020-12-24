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
"""This module contains the tests of the behaviour classes of the simple_data_request skill."""
from pathlib import Path

from aea.test_tools.test_skill import BaseSkillTestCase

from tests.conftest import ROOT_DIR


class ConfirmationAW3TestCase(BaseSkillTestCase):
    """Sets the confirmation_aw3 class up for testing (overrides the necessary config values so tests can be done on confirmation_aw3 skill)."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.aw1_aea = "some_aw1_aea"
        cls.leaderboard_url = "some_leaderboard_url"
        cls.leaderboard_token = "some_leaderboard_token"
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "aw1_aea": cls.aw1_aea,
                        "leaderboard_url": cls.leaderboard_url,
                        "leaderboard_token": cls.leaderboard_token,
                    }
                }
            }
        }

        super().setup(config_overrides=config_overrides)
