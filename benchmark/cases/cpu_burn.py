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
"""Example performance test using benchmark framework. Just test CPU usage with empty while loop."""
import time

from benchmark.framework.benchmark import BenchmarkControl
from benchmark.framework.cli import TestCli


def cpu_burn(
    benchmark: BenchmarkControl, run_time: int = 10, sleep: float = 0.0001
) -> None:
    """
    Do nothing, just burn cpu to check cpu load changed on sleep.

    :param benchmark: benchmark special parameter to communicate with executor
    :param run_time: time limit to run this function
    :param sleep: time to sleep in loop
    """
    benchmark.start()
    start_time = time.time()

    while True:
        time.sleep(sleep)
        if time.time() - start_time >= run_time:
            break


if __name__ == "__main__":
    TestCli(cpu_burn).run()
