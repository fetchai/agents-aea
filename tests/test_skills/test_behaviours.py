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
from aea.skills.behaviours import SequenceBehaviour, OneShotBehaviour, FSMBehaviour, State


def test_sequence_behaviour():
    """Test the sequence behaviour."""
    outputs = []

    class MySequenceBehaviour(SequenceBehaviour):

        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

    class SimpleOneShotBehaviour(OneShotBehaviour):

        def __init__(self, id, **kwargs):
            super().__init__(**kwargs)
            self.id = id

        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

        def act(self) -> None:
            outputs.append(self.id)

    # TODO let the initialization of a behaviour action from constructor
    a = SimpleOneShotBehaviour("a", skill_context=None)
    b = SimpleOneShotBehaviour("b", skill_context=None)
    c = SimpleOneShotBehaviour("c", skill_context=None)
    sequence = MySequenceBehaviour([a, b, c], skill_context=None)

    max_iterations = 10
    i = 0
    while not sequence.done() and i < max_iterations:
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

        def __init__(self, id: int, **kwargs):
            super().__init__(**kwargs)
            self.id = id
            self.executed = False

        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

        def act(self) -> None:
            outputs.append(self.id)
            self.next_state = str(self.id + 1)
            self.executed = True

        def done(self) -> bool:
            return self.executed

    # TODO let the initialization of a behaviour action from constructor
    a = SimpleOneShotBehaviour(0, skill_context=None)
    b = SimpleOneShotBehaviour(1, skill_context=None)
    c = SimpleOneShotBehaviour(2, skill_context=None)
    fsm = MyFSMBehaviour(skill_context=None)
    fsm.register_state(str(a.id), a, initial=True)
    fsm.register_state(str(b.id), b)
    fsm.register_state(str(c.id), c)

    max_iterations = 10
    i = 0
    while not fsm.done() and i < max_iterations:
        fsm.act()
        i += 1

    assert outputs == [0, 1, 2]
