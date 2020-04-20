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
"""Performance report printer for performance tool."""
from typing import List

from .executor import ExecReport
from .func_details import BaseFuncDetails


class PerformanceReportPrinter:
    """Class to handle output of performance test."""

    def __init__(
        self,
        func_details: BaseFuncDetails,
        exec_params: dict,
        exec_reports: List[ExecReport],
    ):
        """
        Make performance report printer instance.

        :param func_details: details about function being tested
        :param exec_params: executor parameters: timeout, interval
        :param exec_reports: tested function execution reports with measurements
        """
        self.func_details = func_details
        self.exec_reports = exec_reports
        self.exec_params = exec_params

    def _print_executor_details(self) -> None:
        """Print details about timeout and period timer of executor."""
        topic = "Test execution"
        print(f"{topic} timeout: {self.exec_params['timeout']}")
        print(f"{topic} measure period: {self.exec_params['period']}")

    def _print_func_details(self) -> None:
        """Print details about function to be tested."""
        topic = "Tested function"
        print(f"{topic} name: {self.func_details.name}")
        print(f"{topic} description: {self.func_details.doc}")
        print(f"{topic} argument names: {self.func_details.argument_names}")
        print(
            f"{topic} argument default values: {self.func_details.default_argument_values}"
        )

    def print_header(self) -> None:
        """Print details about tested function and execution parameters."""
        self._print_executor_details()
        self._print_func_details()
        print()

    def print_(self) -> None:
        """Print report of test performed."""
        for i in self.exec_reports:
            print(i, "\n")
