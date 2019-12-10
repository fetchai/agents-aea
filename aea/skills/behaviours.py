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
import datetime
from abc import ABC
from typing import Optional

from aea.skills.base import Behaviour


class SimpleBehaviour(Behaviour, ABC):
    """This class implements a simple behaviour."""


class CompositeBehaviour(Behaviour, ABC):
    """This class implements a composite behaviour."""


class CyclicBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed until the agent is stopped."""

    def __init__(self, **kwargs):
        """Initialize the cyclic behaviour."""
        super().__init__(**kwargs)
        self._number_of_executions = 0

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        self.act()
        self._number_of_executions += 1

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return False


class OneShotBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed only once."""

    def __init__(self, **kwargs):
        """Initialize the cyclic behaviour."""
        super().__init__(**kwargs)
        self._already_executed = False  # type

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self._already_executed

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        if not self._already_executed:
            self.act()
            self._already_executed = True


class TickerBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed periodically with an interval."""

    def __init__(self, tick_interval: float = 1.0, start_at: Optional[datetime.datetime] = None, **kwargs):
        """
        Initialize the ticker behaviour.

        :param tick_interval: interval of the behaviour in seconds.
        :param start_at: whether to start the behaviour with an offset.
        """
        super().__init__(**kwargs)

        self._tick_interval = tick_interval
        self._start_at = start_at if start_at is not None else datetime.datetime.now()  # type: datetime.datetime

        self._last_act_time = datetime.datetime.now()

    @property
    def tick_interval(self) -> float:
        """Get the tick_interval in seconds."""
        return self._tick_interval

    @property
    def start_at(self) -> datetime.datetime:
        """Get the start time."""
        return self._start_at

    @property
    def last_act_time(self) -> datetime.datetime:
        """Get the last time the act method has been called."""
        return self._start_at

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        if self.is_time_to_act():
            self._last_act_time = datetime.datetime.now()
            self.act()

    def is_time_to_act(self) -> bool:
        """
        Check whether it is time to act, according to the tick_interval constraint and the 'start at' constraint.

        :return: True if it is time to act, false otherwise.
        """
        now = datetime.datetime.now()
        return now > self._start_at and (now - self._last_act_time).total_seconds() > self.tick_interval
