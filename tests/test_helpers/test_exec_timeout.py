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
"""This module contains the tests for the helpers.exec_timout."""
import os
import time
import unittest
from functools import partial
from threading import Thread
from unittest.case import TestCase

import pytest

from aea.helpers.exec_timeout import (
    BaseExecTimeout,
    ExecTimeoutSigAlarm,
    ExecTimeoutThreadGuard,
    TimeoutException,
)

from tests.common.utils import timeit_context
from tests.conftest import MAX_FLAKY_RERUNS


if os.name == "nt":
    pytest.skip("signal.settimer non available on Windows.", allow_module_level=True)


class BaseTestExecTimeout(TestCase):
    """Base test case for code execution timeout."""

    EXEC_TIMEOUT_CLASS = BaseExecTimeout

    @classmethod
    def setUpClass(cls):
        """Set up."""
        if cls is BaseTestExecTimeout:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")

    def test_cancel_by_timeout(self):
        """Test function interrupted by timeout."""
        slow_function_time = 0.4
        timeout = 0.1

        assert timeout < slow_function_time

        with timeit_context() as timeit_result:
            with pytest.raises(TimeoutException):
                with self.EXEC_TIMEOUT_CLASS(timeout) as exec_timeout:
                    self.slow_function(slow_function_time)

            assert exec_timeout.is_cancelled_by_timeout()

        assert (
            timeit_result.time_passed >= timeout
            and timeit_result.time_passed < slow_function_time
        )

    def test_limit_is_0_do_not_limit_execution(self):
        """Test function will not be interrupted cause timeout is 0 or None."""
        slow_function_time = 0.1
        timeout = 0
        assert timeout < slow_function_time

        with timeit_context() as timeit_result:
            with self.EXEC_TIMEOUT_CLASS(timeout) as exec_timeout:
                self.slow_function(slow_function_time)

            assert not exec_timeout.is_cancelled_by_timeout()

        assert timeit_result.time_passed >= slow_function_time

    def test_timeout_bigger_than_execution_time(self):
        """Test function interrupted by timeout."""
        slow_function_time = 0.1
        timeout = 1

        assert timeout > slow_function_time

        with timeit_context() as timeit_result:
            with self.EXEC_TIMEOUT_CLASS(timeout) as exec_timeout:
                self.slow_function(slow_function_time)

            assert not exec_timeout.is_cancelled_by_timeout()

        assert (
            timeit_result.time_passed <= timeout
            and timeit_result.time_passed >= slow_function_time
        )

    @classmethod
    def slow_function(cls, sleep):
        """Sleep some time to test timeout applied."""
        time.sleep(sleep)


class TestSigAlarm(BaseTestExecTimeout):
    """Test code execution timeout using unix signals."""

    EXEC_TIMEOUT_CLASS = ExecTimeoutSigAlarm


class TestThreadGuard(BaseTestExecTimeout):
    """Test code execution timeout using. thread set execption."""

    EXEC_TIMEOUT_CLASS = ExecTimeoutThreadGuard

    def setUp(self):
        """Set up."""
        self.EXEC_TIMEOUT_CLASS.start()

    def tearDown(self):
        """Tear down."""
        self.EXEC_TIMEOUT_CLASS.stop(force=True)

    @classmethod
    def slow_function(cls, sleep):
        """Sleep in cycle to be perfect interrupted."""
        fractions = 10
        for _ in range(fractions):
            time.sleep(sleep / fractions)

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_execution_limit_in_threads(self):
        """Test two threads with different timeouts same time."""
        # pydocstyle: ignore # conflict with black # noqa: E800
        def make_test_function(slow_function_time, timeout):
            assert timeout < slow_function_time

            with timeit_context() as timeit_result:
                with pytest.raises(TimeoutException):
                    with self.EXEC_TIMEOUT_CLASS(timeout) as exec_limit:
                        self.slow_function(slow_function_time)

            assert exec_limit.is_cancelled_by_timeout()
            assert (
                timeit_result.time_passed >= timeout
                and timeit_result.time_passed < slow_function_time
            )

        t1_sleep, t1_timeout = 1, 0.6
        t2_sleep, t2_timeout = 0.45, 0.1

        t1 = Thread(target=partial(make_test_function, t1_sleep, t1_timeout))
        t2 = Thread(target=partial(make_test_function, t2_sleep, t2_timeout))

        with timeit_context() as time_t1:
            t1.start()
            with timeit_context() as time_t2:
                t2.start()
                t2.join()
            t1.join()

        assert t2_timeout <= time_t2.time_passed <= t2_sleep
        assert t1_timeout <= time_t1.time_passed < t1_sleep


def test_supervisor_not_started():
    """Test that TestThreadGuard supervisor thread not started."""
    timeout = 0.1
    sleep_time = 0.5

    exec_limiter = ExecTimeoutThreadGuard(timeout)

    with exec_limiter as exec_limit:
        assert not exec_limiter._future_guard_task
        TestThreadGuard.slow_function(sleep_time)

    assert not exec_limit.is_cancelled_by_timeout()
