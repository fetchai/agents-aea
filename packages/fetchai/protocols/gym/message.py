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

"""This module contains the FIPA message definition."""
from enum import Enum
from typing import cast, Dict, Any

from aea.protocols.base import Message


class GymMessage(Message):
    """The Gym message class."""

    protocol_id = "gym"

    class Performative(Enum):
        """Gym performatives."""

        ACT = 'act'
        PERCEPT = 'percept'
        RESET = 'reset'
        CLOSE = 'close'

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, performative: Performative, **kwargs):
        """
        Initialize.

        :param performative: the performative.
        """
        super().__init__(performative=performative, **kwargs)
        assert self._check_consistency(), "GymMessage initialization inconsistent."

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "Performative is not set."
        return GymMessage.Performative(self.get('performative'))

    @property
    def action(self) -> Any:
        """Get the action from the message."""
        assert self.is_set("action"), "Action is not set."
        return cast(Any, self.get("action"))

    @property
    def step_id(self) -> int:
        """Get the step id from the message."""
        assert self.is_set("step_id"), "Step_id is not set."
        return cast(int, self.get("step_id"))

    @property
    def observation(self) -> Any:
        """Get the observation from the message."""
        assert self.is_set("observation"), "Observation is not set."
        return cast(Any, self.get("observation"))

    @property
    def reward(self) -> float:
        """Get the reward from the message."""
        assert self.is_set("reward"), "Reward is not set."
        return cast(float, self.get("reward"))

    @property
    def done(self) -> bool:
        """Get the value of the done variable from the message."""
        assert self.is_set("done"), "Done is not set."
        return cast(bool, self.get("done"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get the info from the message."""
        assert self.is_set("info"), "Info is not set."
        return cast(Dict[str, Any], self.get("info"))

    def _check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert isinstance(self.performative, GymMessage.Performative)
            if self.performative == GymMessage.Performative.ACT:
                assert self.is_set("action"), "Action is not set."
                assert isinstance(self.step_id, int)
                assert len(self.body) == 3
            elif self.performative == GymMessage.Performative.PERCEPT:
                assert self.is_set("observation"), "Observation is not set."
                assert isinstance(self.reward, float)
                assert isinstance(self.done, bool)
                assert isinstance(self.info, dict)
                assert isinstance(self.step_id, int)
                assert len(self.body) == 6
            elif self.performative == GymMessage.Performative.RESET or self.performative == GymMessage.Performative.CLOSE:
                assert len(self.body) == 1
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):  # pragma: no cover
            return False

        return True
