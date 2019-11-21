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

"""This module contains the tests of the messages module."""

import pytest

from packages.protocols.gym.message import GymMessage
# from packages.protocols.gym.serialization import GymSerializer


def test_gym_message_instantiation():
    """Test instantiation of the gym message."""
    assert GymMessage(performative=GymMessage.Performative.ACT, action='any_action', step_id=1)
    assert GymMessage(performative=GymMessage.Performative.PERCEPT, observation='any_observation', reward=0.0, info={'some_key': 'some_value'}, done=True, step_id=1)
    assert GymMessage(performative=GymMessage.Performative.RESET)
    assert GymMessage(performative=GymMessage.Performative.CLOSE)
    with pytest.raises(ValueError):
        GymMessage()
