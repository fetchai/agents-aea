# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests of the behaviour class of the echo skill."""
# pylint: skip-file

import inspect
import logging
import os
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.echo.behaviours import EchoBehaviour


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore


class TestEchoBehaviour(BaseSkillTestCase):
    """Test EchoBehaviour behaviour of echo."""

    path_to_skill = Path(CUR_PATH, "..")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.echo_behaviour = cast(
            EchoBehaviour, cls._skill.skill_context.behaviours.echo
        )
        cls.logger = cls._skill.skill_context.logger

    def test_setup(self):
        """Test the setup method of the echo behaviour."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            assert self.echo_behaviour.setup() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO, "Echo Behaviour: setup method called."
        )

    def test_act(self):
        """Test the act method of the echo behaviour."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            assert self.echo_behaviour.act() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(logging.INFO, "Echo Behaviour: act method called.")

    def test_teardown(self):
        """Test the teardown method of the echo behaviour."""
        # operation
        with patch.object(self.logger, "log") as mock_logger:
            assert self.echo_behaviour.teardown() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO, "Echo Behaviour: teardown method called."
        )
