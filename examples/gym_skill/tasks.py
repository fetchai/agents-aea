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
from queue import Queue
from threading import Thread


from aea.skills.base import Task

from gym_skill.helpers import ProxyEnv
from gym_skill.rl_agent import MyRLAgent, NB_STEPS, NB_GOODS


class GymTask(Task):
    """Gym task."""

    def __init__(self, **kwargs):
        """Initialize the task."""
        print("GymTask.__init__: arguments: {}".format(kwargs))
        super().__init__(**kwargs)
        self._rl_agent = MyRLAgent(NB_GOODS)
        self._proxy_env = ProxyEnv(self.context)
        self._rl_agent_training_thread = Thread(target=self._rl_agent.fit, args=[self._proxy_env, NB_STEPS])
        self.is_rl_agent_training = False

    @property
    def proxy_env_queue(self) -> Queue:
        """Get the queue."""
        return self._proxy_env.queue

    def execute(self) -> None:
        """Execute the task."""
        if not self._proxy_env.is_rl_agent_trained and not self.is_rl_agent_training:
            self._start_training()
        if self._proxy_env.is_rl_agent_trained and self.is_rl_agent_training:
            self._stop_training()

    def teardown(self) -> None:
        """Teardown the task."""
        print("Gym Task: teardown method called.")
        if self.is_rl_agent_training:
            self._stop_training()

    def _start_training(self) -> None:
        """Start training the RL agent."""
        print("Training starting ...")
        self.is_rl_agent_training = True
        self._rl_agent_training_thread.start()

    def _stop_training(self) -> None:
        """Stop training the RL agent."""
        self.is_rl_agent_training = False
        self._proxy_env.close()
        self._rl_agent_training_thread.join()
        print("Training finished.")
