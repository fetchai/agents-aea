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

"""This module contains the tasks for the 'gym' skill."""
from threading import Thread

from aea.skills.base import Task

from .context import GymContext
from .rl_agent import MyRLAgent, NB_STEPS, NB_GOODS


class GymTask(Task):
    """Gym task."""

    def __init__(self, gym_context: GymContext, **kwargs):
        """Initialize the task."""
        print("GymTask.__init__: arguments: {}".format(kwargs))
        super().__init__(gym_context, kwargs)
        self._rl_agent = MyRLAgent(NB_GOODS)
        self._rl_agent_training_thread = Thread(target=self._rl_agent.fit, args=[self.context.proxy_env, NB_STEPS])

    def execute(self) -> None:
        """Execute the task."""
        print("Gym Task: execute method called.")
        if not self.context.is_rl_agent_trained and not self.context.is_rl_agent_training:
            self.context.is_rl_agent_training = True
            self._rl_agent_training_thread.start()
        if self.context.is_rl_agent_trained and self.context.is_rl_agent_training:
            self.context.is_rl_agent_training = False
            print("Training finished.")
            self._rl_agent_training_thread.join()

    def teardown(self) -> None:
        """Teardown the task."""
        print("Gym Task: teardown method called.")
