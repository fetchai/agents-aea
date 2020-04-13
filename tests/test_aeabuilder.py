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
""" This module contains tests for aea/aea_builder.py """
import os

from aea.aea_builder import AEABuilder
from aea.crypto.fetchai import FETCHAI

from tests.common.utils import timeit_context

from .conftest import CUR_PATH


def test_default_timeout_for_agent():
    """
    Tests agents loop sleep timeout
    set by AEABuilder.DEFAULT_AGENT_LOOP_TIMEOUT
    """
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)
    builder.DEFAULT_AGENT_LOOP_TIMEOUT = 0.05

    """ Default timeout == 0.05 """
    agent = builder.build()
    assert agent._timeout == builder.DEFAULT_AGENT_LOOP_TIMEOUT

    with timeit_context() as time_result:
        agent._spin_main_loop()

    assert time_result.time_passed > builder.DEFAULT_AGENT_LOOP_TIMEOUT
    time_0_05 = time_result.time_passed

    """ Timeout == 0.001 """
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)
    builder.DEFAULT_AGENT_LOOP_TIMEOUT = 0.001

    agent = builder.build()
    assert agent._timeout == builder.DEFAULT_AGENT_LOOP_TIMEOUT

    with timeit_context() as time_result:
        agent._spin_main_loop()

    assert time_result.time_passed > builder.DEFAULT_AGENT_LOOP_TIMEOUT
    time_0_001 = time_result.time_passed

    """ Timeout == 0.0 """
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)
    builder.DEFAULT_AGENT_LOOP_TIMEOUT = 0.0

    agent = builder.build()
    assert agent._timeout == builder.DEFAULT_AGENT_LOOP_TIMEOUT

    with timeit_context() as time_result:
        agent._spin_main_loop()

    assert time_result.time_passed > builder.DEFAULT_AGENT_LOOP_TIMEOUT
    time_0 = time_result.time_passed

    assert time_0 < time_0_001 and time_0_001 < time_0_05
