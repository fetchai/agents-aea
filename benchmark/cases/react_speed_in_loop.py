#!/usr/bin/ev python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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


def react_speed_in_loop(benchmark: BenchmarkControl, inbox_amount: int = 1000) -> None:
    """
    Test inbox message processing in a loop.

    :param benchmark: benchmark special parameter to communicate with executor
    :param inbox_amount: number of inbox messages for every agent
    """
    aea_test_wrapper = AEATestWrapper(
        name="dummy agent",
        components=[
            AEATestWrapper.make_skill(handlers={"dummy_handler": DummyHandler})
        ],
    )

    for _ in range(inbox_amount):
        aea_test_wrapper.put_inbox(aea_test_wrapper.dummy_envelope())

    aea_test_wrapper.set_loop_timeout(0.0)

    benchmark.start()

    aea_test_wrapper.start_loop()

    while not aea_test_wrapper.is_inbox_empty():
        time.sleep(0.1)

    aea_test_wrapper.stop_loop()


if __name__ == "__main__":
    TestCli(react_speed_in_loop).run()
