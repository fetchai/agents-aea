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

"""This module contains the base classes for the skills."""
from queue import Queue

from aea.skills.base import AgentContext, SkillContext

from .helpers import ProxyEnv


class GymContext(SkillContext):
    """This class implements the context of a skill."""

    def __init__(self, agent_context: AgentContext):
        """
        Initialize a skill context.

        :param agent_context: the agent's context
        """
        super().__init__(agent_context)
        self._proxy_env = ProxyEnv(self)
        self._queue = Queue()  # type: Queue
        self.is_rl_agent_trained = False
        self.is_rl_agent_training = False

    @property
    def proxy_env(self) -> ProxyEnv:
        """Get the proxy env."""
        return self._proxy_env

    @property
    def queue(self) -> Queue:
        """Get the queue."""
        return self._queue
