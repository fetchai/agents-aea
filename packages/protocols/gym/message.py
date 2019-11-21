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
from typing import Optional, Union

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

    def __init__(self, performative: Optional[Union[str, Performative]] = None, **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(performative=GymMessage.Performative(performative), **kwargs)
        assert self.check_consistency(), "GymMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("performative")
            performative = GymMessage.Performative(self.get("performative"))
            if performative == GymMessage.Performative.ACT:
                assert self.is_set("action")
                assert self.is_set("step_id")
                assert type(self.get("step_id")) == int
            elif performative == GymMessage.Performative.PERCEPT:
                assert self.is_set("observation")
                assert self.is_set("reward")
                assert type(self.get("reward")) == float
                assert self.is_set("done")
                assert type(self.get("done")) == bool
                assert self.is_set("info")
                assert type(self.get("info")) == dict
                assert self.is_set("step_id")
                assert type(self.get("step_id")) == int
            elif performative == GymMessage.Performative.RESET or performative == GymMessage.Performative.CLOSE:
                pass
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True
