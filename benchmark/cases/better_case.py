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
from benchmark.framework.agency import Agency
from benchmark.framework.cli import TestCli

from aea.configurations.base import SkillConfig


def make_agency_conf(name: str = "dummy_agent", skills_num: int = 1) -> dict:
    """Construct simple config for agency."""
    return {
        "name": "dummy_a",
        "skills": [
            {
                "config": SkillConfig(name=f"sc{i}"),  # type: ignore
                "handlers": {"dummy_handler": DummyHandler},
            }
            for i in range(skills_num)
        ],
    }


def react_speed_in_loop(
    control,
    agents_num: int = 2,
    skills_num: int = 1,
    inbox_num: int = 1000,
    agent_loop_timeout: float = 0.01,
):
    """Test inbox message processing in a loop."""
    agencies = []

    for i in range(agents_num):
        agency = Agency(**make_agency_conf(f"agent{i}", skills_num))
        agency.set_loop_timeout(agent_loop_timeout)
        agencies.append(agency)

        for _ in range(inbox_num):
            agency.put_inbox(agency.dummy_envelope())

    control.put("Go!")

    for agency in agencies:
        agency._start_loop()

    try:
        while sum([not i.is_inbox_empty() for i in agencies]):
            time.sleep(0.1)

    finally:
        # wait to start, Race condition in case no messages to process
        while sum([not i.is_running() for i in agencies]):
            pass
        for agency in agencies:
            agency._stop_loop()


if __name__ == "__main__":
    TestCli(react_speed_in_loop).run()
