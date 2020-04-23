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
import inspect
from collections import namedtuple
from datetime import datetime
from statistics import mean, stdev
from typing import Any, List, Optional, Tuple


from .executor import ExecReport
from .func_details import BaseFuncDetails


class ContextPrinter:
    """Printer for test execution context: function, arguments, execution aprameters."""

    def __init__(self, func_details: BaseFuncDetails, executor_params: dict):
        """
        Make performance report printer instance.

        :param func_details: details about function being tested
        :param exec_params: executor parameters: timeout, interval
        """
        self.func_details = func_details
        self.executor_params = executor_params

    def print_context_information(self):
        """Print details about tested function and execution parameters."""
        self._print_executor_details()
        self._print_func_details()
        print()

    def _print_executor_details(self) -> None:
        """Print details about timeout and period timer of executor."""
        topic = "Test execution"
        print(f"{topic} timeout: {self.executor_params['timeout']}")
        print(f"{topic} measure period: {self.executor_params['period']}")

    def _print_func_details(self) -> None:
        """Print details about function to be tested."""
        topic = "Tested function"
        print(f"{topic} name: {self.func_details.name}")
        print(f"{topic} description: {self.func_details.doc}")
        print(f"{topic} argument names: {self.func_details.argument_names}")
        print(
            f"{topic} argument default values: {self.func_details.default_argument_values}"
        )


ResourceRecord = namedtuple("ResourceRecord", "name,unit,value,std_dev")


class PerformanceReport:
    """Class represents performance report over multiple exec reports."""

    def __init__(self, exec_reports: List[ExecReport]):
        """
        Init performance report with exec reports.

        :param exec_reports: tested function execution reports with measurements
        """
        assert exec_reports
        self.exec_reports = exec_reports

    @property
    def arguments(self) -> Tuple[Any, ...]:
        """
        Return list of arguments for tested function.

        :return: tuple of arguments
        """
        return self.exec_reports[-1].args

    @property
    def report_time(self) -> datetime:
        """
        Return time report was created.

        :return: datetime
        """
        return self.exec_reports[-1].report_created

    @property
    def number_of_runs(self) -> int:
        """
        Return number of executions for this case.

        :return: int
        """
        return len(self.exec_reports)

    @property
    def number_of_terminates(self) -> int:
        """
        Return amount how many times execution was terminated by timeout.

        :return: int
        """
        return sum((i.is_killed for i in self.exec_reports), 0)

    @property
    def resources(self) -> List[ResourceRecord]:
        """
        Return resources values used during execution.

        :return: List of ResourceRecord
        """
        resources: List[ResourceRecord] = []

        resources.append(
            self._make_resource("Time passed", "seconds", "time_passed", None)
        )

        for name, unit in [("cpu", "%"), ("mem", "kb")]:
            for func in [min, max, mean]:
                resources.append(
                    self._make_resource(f"{name} {func.__name__}", unit, name, func)
                )

        return resources

    def _make_resource(
        self, name: str, unit: str, attr_name: str, aggr_function: Optional["function"]
    ) -> ResourceRecord:
        """
        Make ResourceRecord.

        :param name: str. name of the resource (time, cpu, mem,...)
        :param unit: str. measure unit (seconds, kb, %)
        :param attr_name: name of the attribute of execreport to count resource.
        :param aggr_function:  function to process value of execreport.

        :return: ResourceRecord
        """
        return ResourceRecord(
            name, unit, *self._count_resource(attr_name, aggr_function)
        )

    def _count_resource(self, attr_name, aggr_function=None) -> Tuple[float, float]:
        """
        Calculate resources from exec reports.

        :param attr_name: name of the attribute of execreport to count resource.
        :param aggr_function:  function to process value of execreport.

        :return: (mean_value, standart_deviation)
        """
        if not aggr_function:
            aggr_function = lambda x: x  # noqa: E731

        values = [aggr_function(getattr(i, attr_name)) for i in self.exec_reports]
        mean_value = mean(values)
        std_dev = stdev(values) if len(values) > 1 else 0

        return (mean_value, std_dev)


class ReportPrinter(ContextPrinter):
    """Class to handle output of performance test."""

    def _print_header(self, report: PerformanceReport) -> None:
        """
        Print header for performance report.

        Prints arguments, number of runs and number of terminates.

        :param report: performance report to print header for

        :return: None
        """
        text = inspect.cleandoc(
            f"""
            == Report created {report.report_time} ==
            Arguments are `{report.arguments}`
            Number of runs: {report.number_of_runs}
            Number of time terminated: {report.number_of_terminates}
            """
        )
        print(text)

    def _print_resources(self, report: PerformanceReport) -> None:
        """
        Print resources details for performance report.

        :param report: performance report to print header for

        :return: None
        """
        for resource in report.resources:
            print(
                f"{resource.name} ({resource.unit}): {resource.value} ± {resource.std_dev}"
            )

    def print_report(self, report: PerformanceReport) -> None:
        """
        Print full performance report for case.

        :param report: performance report to print header for

        :return: None
        """
        self._print_header(report)
        self._print_resources(report)
