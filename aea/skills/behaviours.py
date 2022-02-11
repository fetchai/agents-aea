# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set

from aea.exceptions import enforce
from aea.skills.base import Behaviour


class SimpleBehaviour(Behaviour, ABC):
    """This class implements a simple behaviour."""

    def __init__(self, act: Optional[Callable[[], None]] = None, **kwargs: Any) -> None:
        """
        Initialize a simple behaviour.

        :param act: the act callable.
        :param kwargs: the keyword arguments to be passed to the parent class.
        """
        super().__init__(**kwargs)
        if act is not None:
            self.act = act  # type: ignore

    def setup(self) -> None:
        """Set the behaviour up."""

    def act(self) -> None:
        """Do the action."""
        raise NotImplementedError  # pragma: no cover

    def teardown(self) -> None:
        """Tear the behaviour down."""


class CompositeBehaviour(Behaviour, ABC):
    """This class implements a composite behaviour."""


class CyclicBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed until the agent is stopped."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the cyclic behaviour."""
        super().__init__(**kwargs)
        self._number_of_executions = 0

    @property
    def number_of_executions(self) -> int:
        """Get the number of executions."""
        return self._number_of_executions

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        if not self.is_done():
            super().act_wrapper()
            self._number_of_executions += 1

    def is_done(self) -> bool:
        """
        Return True if the behaviour is terminated, False otherwise.

        The user should implement it properly to determine the stopping condition.
        :return: bool indicating status
        """
        return False


class OneShotBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed only once."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the cyclic behaviour."""
        super().__init__(**kwargs)
        self._already_executed = False  # type

    def is_done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self._already_executed

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        if not self._already_executed:
            super().act_wrapper()
            self._already_executed = True


class TickerBehaviour(SimpleBehaviour, ABC):
    """This behaviour is executed periodically with an interval."""

    def __init__(
        self,
        tick_interval: float = 1.0,
        start_at: Optional[datetime.datetime] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the ticker behaviour.

        :param tick_interval: interval of the behaviour in seconds.
        :param start_at: whether to start the behaviour with an offset.
        :param kwargs: the keyword arguments.
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
        if not self.is_done() and self.is_time_to_act():
            self._last_act_time = datetime.datetime.now()
            super().act_wrapper()

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

    def __init__(self, behaviour_sequence: List[Behaviour], **kwargs: Any) -> None:
        """
        Initialize the sequence behaviour.

        :param behaviour_sequence: the sequence of behaviour.
        :param kwargs: the keyword arguments
        """
        super().__init__(**kwargs)

        self._behaviour_sequence = behaviour_sequence
        enforce(len(self._behaviour_sequence) > 0, "at least one behaviour.")
        self._index = 0

    @property
    def current_behaviour(self) -> Optional[Behaviour]:
        """
        Get the current behaviour.

        If None, the sequence behaviour can be considered done.

        :return: current behaviour or None
        """
        return (
            None
            if self._index >= len(self._behaviour_sequence)
            else self._behaviour_sequence[self._index]
        )

    def _increase_index_if_possible(self) -> None:
        if self._index < len(self._behaviour_sequence):
            self._index += 1

    def act(self) -> None:
        """Implement the behaviour."""
        while (
            not self.is_done()
            and self.current_behaviour is not None
            and self.current_behaviour.is_done()
        ):
            self._increase_index_if_possible()

        if (
            not self.is_done()
            and self.current_behaviour is not None
            and not self.current_behaviour.is_done()
        ):
            self.current_behaviour.act_wrapper()

    def is_done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self._index >= len(self._behaviour_sequence)


class State(SimpleBehaviour, ABC):
    """
    A state of a FSMBehaviour.

    A State behaviour is a simple behaviour with a
    special property 'event' that is opportunely set
    by the implementer. The event is read by the framework
    when the behaviour is done in order to pick the
    transition to trigger.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a state of the state machine."""
        super().__init__(**kwargs)
        self._event = None  # type: Optional[str]

    @property
    def event(self) -> Optional[str]:
        """Get the event to be triggered at the end of the behaviour."""
        return self._event

    @abstractmethod
    def is_done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        raise NotImplementedError  # pragma: no cover

    def reset(self) -> None:
        """Reset initial conditions."""


class FSMBehaviour(CompositeBehaviour, ABC):
    """This class implements a finite-state machine behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the finite-state machine behaviour."""
        super().__init__(**kwargs)

        self._name_to_state = {}  # type: Dict[str, State]
        self._initial_state = None  # type: Optional[str]
        self._final_states = set()  # type: Set[str]
        self.current = None  # type: Optional[str]

        # mapping from state to mappings event-next_state
        self.transitions = {}  # type: Dict[str, Dict[Optional[str], str]]

    @property
    def is_started(self) -> bool:
        """Check if the behaviour is started."""
        return self._initial_state is not None

    def register_state(self, name: str, state: State, initial: bool = False) -> None:
        """
        Register a state.

        :param name: the name of the state.
        :param state: the behaviour in that state.
        :param initial: whether the state is an initial state.
        :raises ValueError: if a state with the provided name already exists.
        """
        if name in self._name_to_state:
            raise ValueError("State name already existing.")
        self._name_to_state[name] = state
        if initial:
            self._initial_state = name
            self.current = self._initial_state

    def register_final_state(self, name: str, state: State) -> None:
        """
        Register a final state.

        :param name: the name of the state.
        :param state: the state.
        :raises ValueError: if a state with the provided name already exists.
        """
        if name in self._name_to_state:
            raise ValueError("State name already existing.")
        self._name_to_state[name] = state
        self._final_states.add(name)

    def unregister_state(self, name: str) -> None:
        """
        Unregister a state.

        :param name: the state name to unregister.
        :raises ValueError: if the state is not registered.
        """
        if name not in self._name_to_state:
            raise ValueError("State name not registered.")
        # remove state from mapping
        self._name_to_state.pop(name)
        # if it is an initial state, reset it to None.
        if name == self._initial_state:
            self._initial_state = None
        # if it is a final state, remove from the final state set.
        if name in self._final_states:
            self._final_states.remove(name)

    @property
    def states(self) -> Set[str]:
        """Get all the state names."""
        return set(self._name_to_state.keys())

    @property
    def initial_state(self) -> Optional[str]:
        """Get the initial state name."""
        return self._initial_state

    @initial_state.setter
    def initial_state(self, name: str) -> None:
        """Set the initial state."""
        if name not in self._name_to_state:
            raise ValueError("Name is not registered as state.")
        self._initial_state = name
        self.current = self._initial_state

    @property
    def final_states(self) -> Set[str]:
        """Get the final state names."""
        return self._final_states

    def get_state(self, name: str) -> Optional[State]:
        """Get a state from its name."""
        return self._name_to_state.get(name, None)

    def act(self) -> None:
        """Implement the behaviour."""
        if self.current is None:
            return

        current_state = self.get_state(self.current)
        if current_state is None:
            return
        current_state.act_wrapper()

        if current_state.is_done():
            if current_state in self._final_states:
                # we reached a final state - return.
                self.current = None
                return
            event = current_state.event
            next_state = self.transitions.get(self.current, {}).get(event, None)
            self.current = next_state

    def is_done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return self.current is None

    def register_transition(
        self, source: str, destination: str, event: Optional[str] = None
    ) -> None:
        """
        Register a transition.

        No sanity check is done.

        :param source: the source state name.
        :param destination: the destination state name.
        :param event: the event.
        :raises ValueError: if a transition from source with event is already present.
        """
        if source in self.transitions and event in self.transitions.get(source, {}):
            raise ValueError("Transition already registered.")

        self.transitions.setdefault(source, {})[event] = destination

    def unregister_transition(
        self, source: str, destination: str, event: Optional[str] = None
    ) -> None:
        """
        Unregister a transition.

        :param source: the source state name.
        :param destination: the destination state name.
        :param event: the event.
        :raises ValueError: if a transition from source with event is not present.
        """
        if (
            source not in self.transitions.keys()
            or event not in self.transitions[source].keys()
            or self.transitions[source][event] != destination
        ):
            raise ValueError("Transaction not registered.")

        self.transitions.get(source, {}).pop(event, None)
        if len(self.transitions[source]) == 0:
            self.transitions.pop(source, None)
