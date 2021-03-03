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


class SimpleDataRequestTestCase(BaseSkillTestCase):
    """Sets the simple_data_request class up for testing (overrides the necessary config values so tests can be done on simple_data_request skill)."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_data_request"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.mocked_method = "some_method"
        cls.mocked_url = "some_url"
        cls.mocked_shared_state_key = "some_name_for_data"

        config_overrides = {
            "behaviours": {
                "http_request": {
                    "args": {"method": cls.mocked_method, "url": cls.mocked_url}
                }
            },
            "handlers": {
                "http": {"args": {"shared_state_key": cls.mocked_shared_state_key}}
            },
        }

        super().setup(config_overrides=config_overrides)
