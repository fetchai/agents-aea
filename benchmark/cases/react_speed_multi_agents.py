#!/usr/bin/ev python3
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
"""Example performance test using benchmark framework. Test react speed on amount of incoming messages using normal agent operating."""
import time

from benchmark.cases.helpers.dummy_handler import DummyHandler
from benchmark.framework.aea_test_wrapper import AEATestWrapper
from benchmark.framework.benchmark import BenchmarkControl
from benchmark.framework.cli import TestCli

from aea.configurations.base import SkillConfig


def _make_custom_config(name: str = "dummy_agent", skills_num: int = 1) -> dict:
    """
    Construct config for test wrapper.

    :param name: agent's name
    :param skills_num: number of skills to add to agent

    :return: dict to be used in AEATestWrapper(**result)
    """
    # noqa
    def _make_skill(id):
        return AEATestWrapper.make_skill(
            config=SkillConfig(name=f"sc{id}"), handlers={"dummy_handler": DummyHandler}
        )

    return {
        "name": "dummy_a",
        "components": [_make_skill(i) for i in range(skills_num)],
    }


def react_speed_in_loop(
    benchmark: BenchmarkControl,
    agents_num: int = 2,
    skills_num: int = 1,
    inbox_num: int = 1000,
    agent_loop_timeout: float = 0.01,
) -> None:
    """
    Test inbox message processing in a loop.

    :param benchmark: benchmark special parameter to communicate with executor
    :param agents_num: number of agents to start
    :param skills_num: number of skills to add to each agent
    :param inbox_num: num of inbox messages for every agent
    :param agent_loop_timeout: idle sleep time for agent's loop

    :return: None
    """
    aea_test_wrappers = []

    for i in range(agents_num):
        aea_test_wrapper = AEATestWrapper(
            **_make_custom_config(f"agent{i}", skills_num)
        )
        aea_test_wrapper.set_loop_timeout(agent_loop_timeout)
        aea_test_wrappers.append(aea_test_wrapper)

        for _ in range(inbox_num):
            aea_test_wrapper.put_inbox(aea_test_wrapper.dummy_envelope())

    benchmark.start()

    for aea_test_wrapper in aea_test_wrappers:
        aea_test_wrapper.start_loop()

    try:
        while sum([not i.is_inbox_empty() for i in aea_test_wrappers]):
            time.sleep(0.1)

    finally:
        # wait to start, Race condition in case no messages to process
        while sum([not i.is_running() for i in aea_test_wrappers]):
            pass
        for aea_test_wrapper in aea_test_wrappers:
            aea_test_wrapper.stop_loop()


if __name__ == "__main__":
    TestCli(react_speed_in_loop).run()
