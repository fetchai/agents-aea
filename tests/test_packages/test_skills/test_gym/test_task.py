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
"""This module contains the tests of the task class of the gym skill."""

from unittest.mock import patch

from tests.test_packages.test_skills.test_gym.intermediate_class import GymTestCase


class TestTask(GymTestCase):
    """Test Task of gym."""

    def test__init__(self):
        """Test the __init__ method of the GymTask class."""
        assert self.task.nb_steps == self.nb_steps
        assert self.task.is_rl_agent_training is False

    def test_properties(self):
        """Test the properties of the GymTask class."""
        assert self.task.proxy_env == self.task._proxy_env
        assert self.task.proxy_env_queue == self.task._proxy_env.queue

    def test_setup(self):
        """Test the setup method of the GymTask class."""
        # operation
        with patch.object(self.logger, "info") as mock_logger:
            self.task.setup()

        # after
        mock_logger.assert_any_call("Gym task: setup method called.")

    def test_execute_i(self):
        """Test the execute method of the GymTask class where agent is NOT trained/training."""
        # before
        self.task.proxy_env._is_rl_agent_trained = False
        self.task.is_rl_agent_training = False

        # operation
        with patch.object(self.task._rl_agent, "fit") as mock_fit:
            with patch.object(self.logger, "info") as mock_logger:
                self.task.execute()

        # after
        # _start_training
        mock_logger.assert_any_call("Training starting ...")
        assert self.task.is_rl_agent_training is True

        # _fit
        mock_fit.assert_called_with(self.task.proxy_env, self.nb_steps)
        mock_logger.assert_any_call("Training finished. You can exit now via CTRL+C.")

    def test_execute_ii(self):
        """Test the execute method of the GymTask class where agent IS trained/training."""
        # before
        self.task.proxy_env._is_rl_agent_trained = True
        self.task.is_rl_agent_training = True

        # operation
        with patch.object(self.task.proxy_env, "close") as mock_close:
            self.task.execute()

        # after
        # _stop_training
        assert self.task.is_rl_agent_training is False
        mock_close.assert_called_once()

    def test_teardown(self):
        """Test the teardown method of the GymTask class."""
        self.task.is_rl_agent_training = True

        # operation
        with patch.object(self.task.proxy_env, "close") as mock_close:
            with patch.object(self.logger, "info") as mock_logger:
                self.task.teardown()

        # after
        mock_logger.assert_any_call("Gym Task: teardown method called.")

        # _stop_training
        assert self.task.is_rl_agent_training is False
        mock_close.assert_called_once()
