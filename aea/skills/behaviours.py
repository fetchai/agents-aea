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

"""This module contains the classes for specific behaviours."""
from aea.skills.base import Behaviour


class CyclicBehaviour(Behaviour):
    """This behaviour is executed until the agent is stopped."""

    def __init__(self, **kwargs):
        """Initialize the """
        super().__init__(**kwargs)
        self._number_of_executions = 0

    def step(self):
        """Update the state of the behaviour."""
        self._number_of_executions += 1

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return False


class OneShotBehaviour(CyclicBehaviour):
    """This behaviour is executed only once."""

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self._number_of_executions >= 1
