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
"""Example performance test using benchmark framework. test react speed on amount of incoming messages."""

from benchmark.cases.helpers.dummy_handler import DummyHandler
from benchmark.framework.aea_test_wrapper import AEATestWrapper
from benchmark.framework.benchmark import BenchmarkControl
from benchmark.framework.cli import TestCli


DUMMMY_AGENT_CONF = {
    "name": "dummy_a",
    "skills": [{"handlers": {"dummy_handler": DummyHandler}}],
}


def react_speed(benchmark: BenchmarkControl, amount: int = 1000) -> None:
    """
    Test react only. Does not run full agent's loop.

    :param benchmark: benchmark special parameter to communicate with executor

    :return: None
    """
    aea_test_wrapper = AEATestWrapper(**DUMMMY_AGENT_CONF)  # type: ignore
    aea_test_wrapper.setup()

    for _ in range(amount):
        aea_test_wrapper.put_inbox(aea_test_wrapper.dummy_envelope())

    benchmark.start()
    while not aea_test_wrapper.is_inbox_empty():
        aea_test_wrapper.react()
    aea_test_wrapper.stop()


if __name__ == "__main__":
    TestCli(react_speed).run()
