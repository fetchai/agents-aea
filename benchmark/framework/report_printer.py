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
from .func_details import FuncDetails


class PerformanceReportPrinter:
    """Class to handle output of performance test."""

    def __init__(
        self,
        func_details: FuncDetails,
        exec_params: dict,
        exec_reports: List[ExecReport],
    ):
        """Make performance report printer instance."""
        self.func_details = func_details
        self.exec_reports = exec_reports
        self.exec_params = exec_params

    def print_(self) -> None:
        """Print report to stdout."""
        for i in self.exec_reports:
            print(i)
            print()
