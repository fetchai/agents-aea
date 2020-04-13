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
"""This module contains some utils for testing purposes"""

import time
from contextlib import contextmanager

DEFAULT_SLEEP = 0.0001
DEFAULT_TIMEOUT = 3


class TimeItResult:
    """ class to store execution time for timeit_context """

    def __init__(self):
        self.time_passed = -1


@contextmanager
def timeit_context():
    """
    context manager to measure execution time of code in context

    :return TimeItResult

    example:
    with timeit_context() as result:
        do_long_code()
    print("Long code takes ", result.time_passed)
    """

    result = TimeItResult()
    started_time = time.time()
    try:
        yield result
    finally:
        result.time_passed = time.time() - started_time


class AgentTool:
    def __init__(self, agent):
        self.agent = agent

    def setup(self) -> "AgentTool":
        self.agent._start_setup()
        return self

    def spin(self) -> "AgentTool":
        old_timeout, self.agent._timeout = self.agent._timeout, 0
        self.agent._spin_main_loop()
        self.agent._timeout = old_timeout
        return self

    def wait_outbox_empty(
        self, sleep=DEFAULT_SLEEP, timeout=DEFAULT_TIMEOUT
    ) -> "AgentTool":
        """ wait till agent's outbox consumed completely """
        start_time = time.time()
        while not self.agent.outbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def wait_inbox(self, sleep=DEFAULT_SLEEP, timeout=DEFAULT_TIMEOUT) -> "AgentTool":
        """ wait till something appears on agents inbox and spin loop """
        start_time = time.time()
        while self.agent.inbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def react_one(self) -> "AgentTool":
        self.agent._react_one()
        return self
