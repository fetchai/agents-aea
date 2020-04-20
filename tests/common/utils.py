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

from aea.aea import AEA

DEFAULT_SLEEP = 0.0001
DEFAULT_TIMEOUT = 3


class TimeItResult:
    """ class to store execution time for timeit_context """

    def __init__(self):
        self.time_passed = -1


@contextmanager
def timeit_context():
    """
    Context manager to measure execution time of code in context

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


class AeaTool:
    def __init__(self, aea: AEA):
        self.aea = aea

    def setup(self) -> "AeaTool":
        self.aea._start_setup()
        return self

    def spin_main_loop(self) -> "AeaTool":
        """
        Run one cycle of agent's main loop

        :return: AeaTool
        """
        old_timeout, self.aea._timeout = self.aea._timeout, 0
        self.aea._spin_main_loop()
        self.aea._timeout = old_timeout
        return self

    def wait_outbox_empty(
        self, sleep: float = DEFAULT_SLEEP, timeout: float = DEFAULT_TIMEOUT
    ) -> "AeaTool":
        """
        Wait till agent's outbox consumed completely

        :return: AeaTool
        """
        start_time = time.time()
        while not self.aea.outbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def wait_inbox(
        self, sleep: float = DEFAULT_SLEEP, timeout: float = DEFAULT_TIMEOUT
    ) -> "AeaTool":
        """
        Wait till something appears on agents inbox and spin loop

        :return: AeaTool
        """
        start_time = time.time()
        while self.aea.inbox.empty():
            time.sleep(sleep)
            if time.time() - start_time > timeout:
                raise Exception("timeout")
        return self

    def react_one(self) -> "AeaTool":
        """
        Run agent.react once to process inbox messages

        :return: AeaTool
        """
        self.aea._react_one()
        return self
