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

"""This module contains the agent context class."""

from queue import Queue
from typing import Dict

from aea.agent import Liveness
from aea.decision_maker.base import OwnershipState, Preferences
from aea.mail.base import OutBox


class AgentContext:
    """Provide read access to relevant data of the agent for the skills."""

    def __init__(self, agent_name: str,
                 public_keys: Dict[str, str],
                 outbox: OutBox,
                 decision_maker_message_queue: Queue,
                 ownership_state: OwnershipState,
                 preferences: Preferences,
                 is_ready_to_pursuit_goals: bool,
                 liveness: Liveness):
        """
        Initialize an agent context.

        :param agent_name: the agent's name
        :param public_keys: the public keys of the agent
        :param public_key: the default public key
        :param outbox: the outbox
        :param decision_maker_queue: the (in) queue of the decision maker
        :param ownership_state: the ownership state of the agent
        :param preferences: the preferences of the agent
        :param is_ready_to_pursuit_goals: whether the agent is ready to pursuit its goals
        :param liveness: the liveness object.
        """
        self._agent_name = agent_name
        self._public_keys = public_keys
        self._outbox = outbox
        self._decision_maker_message_queue = decision_maker_message_queue
        self._ownership_state = ownership_state
        self._preferences = preferences
        self._is_ready_to_pursuit_goals = is_ready_to_pursuit_goals
        self._liveness = liveness

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._agent_name

    @property
    def public_keys(self) -> Dict[str, str]:
        """Get public keys."""
        return self._public_keys

    @property
    def public_key(self) -> str:
        """Get the default public key."""
        return self._public_keys['default']

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._outbox

    @property
    def decision_maker_message_queue(self) -> Queue:
        """Get decision maker queue."""
        return self._decision_maker_message_queue

    @property
    def ownership_state(self) -> OwnershipState:
        """Get the ownership state of the agent."""
        return self._ownership_state

    @property
    def preferences(self) -> Preferences:
        """Get the preferences of the agent."""
        return self._preferences

    @property
    def is_ready_to_pursuit_goals(self) -> bool:
        """Get the goal pursuit readiness."""
        return self._is_ready_to_pursuit_goals

    @property
    def liveness(self) -> Liveness:
        """Get the liveness object."""
        return self._liveness
