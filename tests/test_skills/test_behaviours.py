# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the tests for the behaviours."""
from collections import Counter
from unittest import TestCase, mock

import pytest

from aea.exceptions import AEAActException, _StopRuntime
from aea.skills.behaviours import (
    CyclicBehaviour,
    FSMBehaviour,
    OneShotBehaviour,
    SequenceBehaviour,
    State,
    TickerBehaviour,
)


def test_sequence_behaviour():
    """Test the sequence behaviour."""
    outputs = []

    class MySequenceBehaviour(SequenceBehaviour):
        """Custom sequence behaviour."""

        def setup(self) -> None:
            """Setup behaviour."""
            pass

        def teardown(self) -> None:
            """Teardown behaviour."""
            pass

    class SimpleOneShotBehaviour(OneShotBehaviour):
        """Custom simple behaviour."""

        def __init__(self, name, **kwargs):
            super().__init__(name=name, **kwargs)

        def setup(self) -> None:
            """Setup behaviour."""
            pass

        def teardown(self) -> None:
            """Teardown behaviour."""
            pass

        def act(self) -> None:
            """Act implementation."""
            outputs.append(self.name)

    # TODO let the initialization of a behaviour action from constructor
    a = SimpleOneShotBehaviour("a", skill_context=object())
    b = SimpleOneShotBehaviour("b", skill_context=object())
    c = SimpleOneShotBehaviour("c", skill_context=object())
    sequence = MySequenceBehaviour([a, b, c], name="abc", skill_context=object())

    max_iterations = 10
    i = 0
    while not sequence.is_done() and i < max_iterations:
        sequence.act()
        i += 1

    assert outputs == ["a", "b", "c"]


def test_act_parameter():
    """Test the 'act' parameter."""
    counter = Counter(i=0)

    def increment_counter(counter=counter):
        counter += Counter(i=1)

    assert counter["i"] == 0

    one_shot_behaviour = OneShotBehaviour(
        act=lambda: increment_counter(), skill_context=object(), name="my_behaviour"
    )
    one_shot_behaviour.act()
    assert counter["i"] == 1


class SimpleFSMBehaviour(FSMBehaviour):
    """A Finite-State Machine behaviour for testing purposes."""

    def setup(self) -> None:
        """Setup behaviour."""
        pass

    def teardown(self) -> None:
        """Teardown behaviour."""
        pass


class SimpleStateBehaviour(State):
    """A simple state behaviour to be added in a FSMBehaviour."""

    def __init__(self, shared_list, event_to_trigger=None, **kwargs):
        """Initialise simple behaviour."""
        super().__init__(**kwargs)
        self.shared_list = shared_list
        self.event_to_trigger = event_to_trigger
        self.executed = False

    def setup(self) -> None:
        """Setup behaviour."""
        pass

    def teardown(self) -> None:
        """Teardown behaviour."""
        pass

    def act(self) -> None:
        """Act implementation."""
        self.shared_list.append(self.name)
        self.executed = True
        self._event = self.event_to_trigger

    def is_done(self) -> bool:
        """Get is done."""
        return self.executed


def test_fms_behaviour():
    """Test the finite-state machine behaviour."""
    outputs = []

    a = SimpleStateBehaviour(
        outputs, name="a", event_to_trigger="move_to_b", skill_context=object()
    )
    b = SimpleStateBehaviour(
        outputs, name="b", event_to_trigger="move_to_c", skill_context=object()
    )
    c = SimpleStateBehaviour(outputs, name="c", skill_context=object())
    fsm = SimpleFSMBehaviour(name="abc", skill_context=object())
    fsm.register_state(str(a.name), a, initial=True)
    fsm.register_state(str(b.name), b)
    fsm.register_final_state(str(c.name), c)
    fsm.register_transition("a", "b", "move_to_b")
    fsm.register_transition("b", "c", "move_to_c")

    max_iterations = 10
    i = 0
    while not fsm.is_done() and i < max_iterations:
        fsm.act()
        i += 1

    assert outputs == ["a", "b", "c"]


class TestFSMBehaviourCreation:
    """Test FSMBehaviour creation."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.fsm_behaviour = SimpleFSMBehaviour(name="fsm", skill_context=object())
        cls.outputs = []
        cls.a = SimpleStateBehaviour(cls.outputs, name="a", skill_context=object())
        cls.b = SimpleStateBehaviour(cls.outputs, name="b", skill_context=object())
        cls.c = SimpleStateBehaviour(cls.outputs, name="c", skill_context=object())

    def test_initial_state_is_none(self):
        """Test that the initial state is None."""
        assert self.fsm_behaviour.initial_state is None

    def test_states_is_empty(self):
        """Test that the states is an empty set."""
        assert self.fsm_behaviour.states == set()

    def test_final_states_is_empty(self):
        """Test that the final states is an empty set."""
        assert self.fsm_behaviour.final_states == set()

    def test_add_and_remove_state(self):
        """Test that adding and removing a state works correctly."""
        assert self.fsm_behaviour.states == set()
        self.fsm_behaviour.register_state("a", self.a)
        assert self.fsm_behaviour.states == {"a"}
        self.fsm_behaviour.unregister_state("a")
        assert self.fsm_behaviour.states == set()

    def test_add_and_remove_initial_state(self):
        """Test that adding and removing an initial state works correctly."""
        assert self.fsm_behaviour.states == set()
        self.fsm_behaviour.register_state("a", self.a, initial=True)
        assert self.fsm_behaviour.states == {"a"}
        assert self.fsm_behaviour.initial_state == "a"
        assert self.fsm_behaviour.final_states == set()
        self.fsm_behaviour.unregister_state("a")
        assert self.fsm_behaviour.states == set()
        assert self.fsm_behaviour.initial_state is None
        assert self.fsm_behaviour.final_states == set()

    def test_add_and_remove_final_state(self):
        """Test that adding and removing final states works correctly."""
        assert self.fsm_behaviour.states == set()
        self.fsm_behaviour.register_final_state("a", self.a)
        assert self.fsm_behaviour.states == {"a"}
        assert self.fsm_behaviour.initial_state is None
        assert self.fsm_behaviour.final_states == {"a"}
        self.fsm_behaviour.unregister_state("a")
        assert self.fsm_behaviour.states == set()
        assert self.fsm_behaviour.initial_state is None
        assert self.fsm_behaviour.final_states == set()

    def test_register_initial_state_twice(self):
        """Test that the register state with initial=True works correctly when called twice."""
        assert self.fsm_behaviour.initial_state is None
        self.fsm_behaviour.register_state("a", self.a, initial=True)
        assert self.fsm_behaviour.initial_state == "a"
        self.fsm_behaviour.register_state("b", self.b, initial=True)
        assert self.fsm_behaviour.initial_state == "b"
        self.fsm_behaviour.unregister_state("a")
        self.fsm_behaviour.unregister_state("b")
        assert self.fsm_behaviour.initial_state is None

    def test_register_twice_same_state(self):
        """Test that registering twice a state with the same name raises an error."""
        self.fsm_behaviour.register_state("a", self.a)
        with pytest.raises(ValueError, match="State name already existing."):
            self.fsm_behaviour.register_state("a", self.a)
        self.fsm_behaviour.unregister_state("a")

    def test_register_transition(self):
        """Test register transition."""
        self.fsm_behaviour.register_transition("state_1", "state_2")
        self.fsm_behaviour.register_transition("state_1", "state_2", "an_event")
        assert self.fsm_behaviour.transitions == {
            "state_1": {None: "state_2", "an_event": "state_2"}
        }
        self.fsm_behaviour.unregister_transition("state_1", "state_2", None)
        self.fsm_behaviour.unregister_transition("state_1", "state_2", "an_event")
        assert self.fsm_behaviour.transitions == dict()

    def test_register_same_transition_twice(self):
        """Test that when we try to register twice the same transition we raise an error."""
        self.fsm_behaviour.register_transition("state_1", "state_2")
        with pytest.raises(ValueError, match="Transition already registered."):
            self.fsm_behaviour.register_transition("state_1", "state_2")
        self.fsm_behaviour.unregister_transition("state_1", "state_2")

        self.fsm_behaviour.register_transition("state_1", "state_2", "an_event")
        with pytest.raises(ValueError, match="Transition already registered."):
            self.fsm_behaviour.register_transition("state_1", "state_2", "an_event")
        self.fsm_behaviour.unregister_transition("state_1", "state_2", "an_event")


class CyclicBehaviourTestCase(TestCase):
    """Test case for CyclicBehaviour class."""

    def setUp(self):
        """Set the test up."""

        class TestCyclicBehaviour(CyclicBehaviour):
            """Class for testing CyclicBehaviour abstract class."""

            def setup(self, *args):
                """Set up."""
                pass

            def teardown(self, *args):
                """Tear down."""
                pass

        self.TestCyclicBehaviour = TestCyclicBehaviour

    def test_init_positive(self):
        """Test for init positive result."""
        self.TestCyclicBehaviour(skill_context="skill_context", name="name")

    def test_act_wrapper_positive(self):
        """Test for act_wrapper positive result."""
        obj = self.TestCyclicBehaviour(skill_context="skill_context", name="name")
        obj.act = mock.Mock()
        assert obj.number_of_executions == 0
        obj.act_wrapper()
        obj.act.assert_called_once()
        assert obj.number_of_executions == 1

    def test_act_wrapper_negative_standard_exception(self):
        """Test for act_wrapper negative result."""

        def exception_act():
            """Act method with exception."""
            raise ValueError("expected")

        with pytest.raises(AEAActException):
            with pytest.raises(ValueError):
                obj = self.TestCyclicBehaviour(skill_context=mock.Mock(), name="name")
                obj.act = exception_act
                assert obj.number_of_executions == 0
                obj.act_wrapper()
                obj.act.assert_called_once()
                assert obj.number_of_executions == 1

    def test_act_wrapper_negative_stop_runtime(self):
        """Test for act_wrapper negative result."""
        obj = self.TestCyclicBehaviour(skill_context="skill_context", name="name")
        obj.act = mock.Mock()

        with pytest.raises(_StopRuntime):
            with mock.patch.object(obj, "act", side_effect=_StopRuntime()):
                assert obj.number_of_executions == 0
                obj.act_wrapper()
                obj.act.assert_called_once()
                assert obj.number_of_executions == 1


class TickerBehaviourTestCase(TestCase):
    """Test case for TickerBehaviour class."""

    def setUp(self):
        """Set the test up."""

        class TestTickerBehaviour(TickerBehaviour):
            """Class for testing TickerBehaviour abstract class."""

            def setup(self, *args):
                """Set up."""
                pass

            def teardown(self, *args):
                """Tear down."""
                pass

        self.TestTickerBehaviour = TestTickerBehaviour

    def test_init_positive(self):
        """Test for init positive result."""
        self.TestTickerBehaviour(skill_context="skill_context", name="name")

    def test_tick_interval_positive(self):
        """Test for tick_interval property positive result."""
        obj = self.TestTickerBehaviour(skill_context="skill_context", name="name")
        obj.tick_interval

    def test_start_at_positive(self):
        """Test for start_at property positive result."""
        obj = self.TestTickerBehaviour(skill_context="skill_context", name="name")
        obj.start_at

    def test_last_act_time_positive(self):
        """Test for last_act_time property positive result."""
        obj = self.TestTickerBehaviour(skill_context="skill_context", name="name")
        obj.last_act_time

    def test_act_wrapper_positive(self):
        """Test for act_wrapper positive result."""
        obj = self.TestTickerBehaviour(skill_context="skill_context", name="name")
        obj.is_done = mock.Mock(return_value=False)
        obj.is_time_to_act = mock.Mock(return_value=True)
        obj.act = mock.Mock()
        obj.act_wrapper()
        obj.act.assert_called_once()

    def test_is_time_to_act_positive(self):
        """Test for is_time_to_act positive result."""
        obj = self.TestTickerBehaviour(skill_context="skill_context", name="name")
        obj.is_time_to_act()


class FSMBehaviourTestCase(TestCase):
    """Test case for FSMBehaviour class."""

    def setUp(self):
        """Set the test up."""

        class TestFSMBehaviour(FSMBehaviour):
            """Class for testing FSMBehaviour abstract class."""

            def setup(self, *args):
                """Set up."""
                pass

            def teardown(self, *args):
                """Tear down."""
                pass

        self.TestFSMBehaviour = TestFSMBehaviour

    def test_is_started_positive(self):
        """Test for is_started property positive result."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj.is_started

    def test_register_final_state_already_exists(self):
        """Test for register_final_state already exists."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj._name_to_state = ["name"]
        with self.assertRaises(ValueError):
            obj.register_final_state("name", "state")

    def test_unregister_state_not_exists(self):
        """Test for unregister_state not exists."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj._name_to_state = []
        with self.assertRaises(ValueError):
            obj.unregister_state("name")

    def test_initial_state_not_state(self):
        """Test for initial_state not a state."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj._name_to_state = []
        with self.assertRaises(ValueError):
            obj.initial_state = "name"

    def test_initial_state_positive(self):
        """Test for initial_state positive result."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj._name_to_state = ["name"]
        obj.initial_state = "name"

    def test_act_no_current(self):
        """Test for act method no current state."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj.current = None
        obj.act()

    def test_act_no_current_got(self):
        """Test for act method no current state got."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj.get_state = mock.Mock(return_value=None)
        obj.current = "current"
        obj.act()
        obj.get_state.assert_called_once()

    def test_act_current_in_final_states(self):
        """Test for act method current in final_states."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        current_state = mock.Mock()
        current_state.act_wrapper = mock.Mock()
        current_state.is_done = mock.Mock(return_value=True)

        obj.final_states.add(current_state)
        obj.get_state = mock.Mock(return_value=current_state)
        obj.current = "current"
        obj.act()

        obj.get_state.assert_called_once()
        current_state.act_wrapper.assert_called_once()
        current_state.is_done.assert_called_once()

    def test_unregister_transition_value_error(self):
        """Test for unregister_transition method ValueError raises."""
        obj = self.TestFSMBehaviour(skill_context="skill_context", name="name")
        obj.transitions = {}
        with self.assertRaises(ValueError):
            obj.unregister_transition("source", "destination")
