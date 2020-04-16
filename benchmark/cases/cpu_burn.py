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

"""Example performance test using benchmark framework. Just test CPU usage with empty while loop."""
import time

from benchmark.framework.cli import TestCli


def cpu_burn(control, run_time=10, sleep=0.0001):
    """Do nothin, just burn cpu to check cpu load changed on sleep."""
    control.put("go")
    a = 0
    start_time = time.time()
    while True:
        a += 1
        for i in range(10000):
            i ** 2
        time.sleep(sleep)
        if time.time() - start_time >= run_time:
            break


if __name__ == "__main__":
    TestCli(cpu_burn).run()
