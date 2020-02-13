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

"""This module contains the tests for the behaviours."""
from collections import Counter

from aea.skills.behaviours import (
    OneShotBehaviour,
    SequenceBehaviour,
    FSMBehaviour, State)


def test_sequence_behaviour():
    """Test the sequence behaviour."""
    outputs = []

    class MySequenceBehaviour(SequenceBehaviour):
        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

    class SimpleOneShotBehaviour(OneShotBehaviour):
        def __init__(self, name, **kwargs):
            super().__init__(name=name, **kwargs)

        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

        def act(self) -> None:
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


def test_fms_behaviour():
    """Test the finite-state machine behaviour."""
    outputs = []

    class MyFSMBehaviour(FSMBehaviour):
        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

    class SimpleOneShotBehaviour(State):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.executed = False

        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

        def act(self) -> None:
            outputs.append(self.name)
            self.executed = True

        def is_done(self) -> bool:
            return self.executed

    a = SimpleOneShotBehaviour(name="a", skill_context=object())
    b = SimpleOneShotBehaviour(name="b", skill_context=object())
    c = SimpleOneShotBehaviour(name="c", skill_context=object())
    fsm = MyFSMBehaviour(name="abc", skill_context=object())
    fsm.register_state(str(a.name), a, initial=True)
    fsm.register_state(str(b.name), b)
    fsm.register_final_state(str(c.name), c)
    fsm.register_transition("a", "b")
    fsm.register_transition("b", "c")

    max_iterations = 10
    i = 0
    while not fsm.is_done() and i < max_iterations:
        fsm.act()
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
