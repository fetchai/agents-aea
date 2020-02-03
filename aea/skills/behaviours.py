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
from typing import Dict, List, Optional

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
        if not self.done():
            self.act()
            self._number_of_executions += 1

    def done(self) -> bool:
        """
        Return True if the behaviour is terminated, False otherwise.

        The user should implement it properly to determine the stopping condition.
        """
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

    def __init__(
        self,
        tick_interval: float = 1.0,
        start_at: Optional[datetime.datetime] = None,
        **kwargs
    ):
        """
        Initialize the ticker behaviour.

        :param tick_interval: interval of the behaviour in seconds.
        :param start_at: whether to start the behaviour with an offset.
        """
        super().__init__(**kwargs)

        self._tick_interval = tick_interval
        self._start_at = (
            start_at if start_at is not None else datetime.datetime.now()
        )  # type: datetime.datetime
        # note, we set _last_act_time to be in the past so the ticker starts immediately
        self._last_act_time = datetime.datetime.now() - datetime.timedelta(
            seconds=tick_interval
        )

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
        if not self.done() and self.is_time_to_act():
            self._last_act_time = datetime.datetime.now()
            self.act()

    def is_time_to_act(self) -> bool:
        """
        Check whether it is time to act, according to the tick_interval constraint and the 'start at' constraint.

        :return: True if it is time to act, false otherwise.
        """
        now = datetime.datetime.now()
        return (
            now > self._start_at
            and (now - self._last_act_time).total_seconds() > self.tick_interval
        )


class SequenceBehaviour(CompositeBehaviour, ABC):
    """This behaviour executes sub-behaviour serially."""

    def __init__(self, behaviour_sequence: List[Behaviour], **kwargs):
        """
        Initialize the sequence behaviour.

        :param behaviour_sequence: the sequence of behaviour.
        :param kwargs:
        """
        super().__init__(**kwargs)

        self._behaviour_sequence = behaviour_sequence
        assert len(self._behaviour_sequence) > 0, "at least one behaviour."
        self._index = 0

    @property
    def current_behaviour(self) -> Optional[Behaviour]:
        """
        Get the current behaviour.

        If None, the sequence behaviour can be considered done.
        """
        return (
            None
            if self._index >= len(self._behaviour_sequence)
            else self._behaviour_sequence[self._index]
        )

    def _increase_index_if_possible(self):
        if self._index < len(self._behaviour_sequence):
            self._index += 1

    def act(self) -> None:
        """Implement the behaviour."""
        while (
            not self.done()
            and self.current_behaviour is not None
            and self.current_behaviour.done()
        ):
            self._increase_index_if_possible()

        if (
            not self.done()
            and self.current_behaviour is not None
            and not self.current_behaviour.done()
        ):
            self.current_behaviour.act_wrapper()

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self._index >= len(self._behaviour_sequence)


class State(OneShotBehaviour, ABC):
    """A state of a FSMBehaviour is a OneShotBehaviour."""

    def __init__(self, **kwargs):
        """Initialize a state of the state machine."""
        super().__init__(**kwargs)
        self._next_state = None

    @property
    def next_state(self) -> Optional[str]:
        """Get the next state name. If None, the current state is supposed to be final."""
        return self._next_state

    @next_state.setter
    def next_state(self, state_name):
        """
        Set the state to transition to when this state is finished.

        The argument 'state_name' must be a valid state and the transition must be registered.
        If the setter is not called then current state is a final state.

        :param: state_name: the name of the state to transition to
        """
        self._next_state = state_name


class FSMBehaviour(CompositeBehaviour, ABC):
    """This class implements a finite-state machine behaviour."""

    def __init__(self, **kwargs):
        """Initialize the finite-state machine behaviour."""
        super().__init__(**kwargs)

        self.name_to_state = {}  # type: Dict[str, State]
        self._initial_state = None  # type: Optional[str]
        self.current = None  # type: Optional[str]

        self.transitions = {}  # type: Dict[str, Dict[str, str]]

    @property
    def is_started(self) -> bool:
        """Check if the behaviour is started."""
        return self._initial_state is not None

    def register_state(self, name: str, state: State, initial: bool = False) -> None:
        """
        Register a state.

        :param name: the name of the state.
        :param state: the behaviour in that state.
        :return: None
        """
        self.name_to_state[name] = state
        if initial:
            self._initial_state = name
            self.current = self._initial_state

    @property
    def initial_state(self) -> Optional[str]:
        """Get the initial state name."""
        return self._initial_state

    @initial_state.setter
    def initial_state(self, name: str):
        """Set the initial state."""
        if name not in self.name_to_state:
            raise ValueError("Name is not registered as state.")
        self._initial_state = name

    def get_state(self, name) -> Optional[State]:
        """Get a state from its name."""
        return self.name_to_state.get(name, None)

    def reset(self):
        """Reset the behaviour to its initial conditions."""
        self.current = None

    def act(self):
        """Implement the behaviour."""
        if self.current is None:
            return

        current_state = self.get_state(self.current)
        if current_state is None:
            return
        current_state.act_wrapper()

        if current_state.done():
            self.current = current_state.next_state

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self.current is None
