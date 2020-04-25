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
"""Executor to run and measure resources consumed by python code."""
import datetime
import inspect
import multiprocessing
import time
from collections import namedtuple
from multiprocessing import Process
from operator import attrgetter
from statistics import mean
from typing import Callable, List, Tuple

from benchmark.framework.benchmark import BenchmarkControl

import memory_profiler  # type: ignore

import psutil  # type: ignore

from tests.common.utils import timeit_context


ResourceStats = namedtuple("ResourceStats", "time,cpu,mem")


class ExecReport:
    """Process execution report."""

    def __init__(
        self,
        args: tuple,
        time_passed: float,
        stats: List[ResourceStats],
        is_killed: bool,
        period: float,
    ):
        """Make an instance.

        :param args: tuple of arguments passed to function tested.
        :param time_passed: time test function was executed.
        :param stats: list of ResourceStats: cpu, mem.
        :param is_killed: was process terminated by timeout.
        :param period: what is measurement period length.
        """
        self.args = args
        self.report_created = datetime.datetime.now()
        self.time_passed = time_passed
        self.stats = stats
        self.is_killed = is_killed
        self.period = period

    @property
    def cpu(self) -> List[float]:
        """
        Return list of cpu usage records.

        :return: list of cpu usage values
        """
        return list(map(attrgetter("cpu"), self.stats))

    @property
    def mem(self) -> List[float]:
        """
        Return list of memory usage records.

        :return: list of memory usage values
        """
        return list(map(attrgetter("mem"), self.stats))

    def __str__(self) -> str:
        """
        Render report to string.

        :return: string representation of report.
        """
        return inspect.cleandoc(
            f"""
        == Report created {self.report_created} ==
        Arguments are `{self.args}`
        Time passed {self.time_passed}
        Terminated by timeout: {self.is_killed}
        Cpu(%) mean: {mean(self.cpu)}
        Cpu(%) min: {min(self.cpu)}
        Cpu(%) max: {max(self.cpu)}
        Mem(kb) mean: {mean(self.mem)}
        Mem(kb) min: {min(self.mem)}
        Mem(kb) max: {max(self.mem)}
        """
        )


class Executor:
    """Process execution and resources measurement."""

    def __init__(self, period: float = 0.1, timeout: float = 30):
        """
        Set executor with parameters.

        :param period: period to take resource measurement.
        :param timeout: time limit to perform test, test process will be killed after timeout.
        """
        self.period = period
        self.timeout = timeout

    def run(self, func: Callable, args: tuple) -> ExecReport:
        """
        Run function to be tested for performance.

        :param func: function or callable to be tested for performance.
        :param args: tuple of argument to pass to function tested.

        :return: execution report for single test run
        """
        process = self._prepare(func, args)
        time_usage, stats, killed = self._measure(process)
        return self._report(args, time_usage, stats, killed)

    def _prepare(self, func: Callable, args: tuple) -> Process:
        """
        Start process and wait process ready to be measured.

        :param func: function or callable to be tested for performance.
        :param args: tuple of argument to pass to function tested.

        :return: process with tested code
        """
        control: BenchmarkControl = BenchmarkControl()
        process = Process(target=func, args=(control, *args))
        process.start()
        msg = control.wait_msg()
        assert msg == control.START_MSG
        return process

    def _measure(
        self, process: multiprocessing.Process
    ) -> Tuple[float, List[ResourceStats], bool]:
        """
        Measure resources consumed by the process.

        :param process: process to measure resource consumption

        :return: time used, list of resource stats, was killed
        """
        started_time = time.time()
        is_killed = False
        proc_info = psutil.Process(process.pid)
        stats = []

        with timeit_context() as timeit:
            while process.is_alive():
                if time.time() - started_time > self.timeout:
                    is_killed = True
                    break
                stats.append(self._get_stats_record(proc_info))

                time.sleep(self.period)

        if is_killed:
            process.terminate()

        process.join()
        time_usage = timeit.time_passed

        return time_usage, stats, is_killed

    def _get_stats_record(self, proc_info: psutil.Process) -> ResourceStats:
        """
        Read resources usage and create record.

        :param proc_info: process information to get cpu usage and memory usage from.

        :return: one time resource stats record
        """
        return ResourceStats(
            time.time(),
            proc_info.cpu_percent(),
            memory_profiler.memory_usage(proc_info.pid, max_usage=True),
        )

    def _report(
        self,
        args: tuple,
        time_passed: float,
        stats: List[ResourceStats],
        is_killed: bool,
    ) -> ExecReport:
        """
        Create execution report.

        :param args: tuple of argument to pass to function tested.
        :param time_passed: time test function was executed.
        :param stats: list of ResourceStats: cpu, mem.
        :param is_killed: was process terminated by timeout.

        :return: test case one execution report
        """
        return ExecReport(args, time_passed, stats, is_killed, self.period)
