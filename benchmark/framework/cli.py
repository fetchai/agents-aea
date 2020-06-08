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
"""Cli implementation for performance tests suits."""
import ast
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
from click.core import Argument, Command, Context, Option, Parameter

from .executor import Executor
from .func_details import BenchmarkFuncDetails
from .report_printer import PerformanceReport, ReportPrinter


class DefaultArgumentsMultiple(Argument):
    """Multiple arguments with default value."""

    def __init__(self, *args, **kwargs):
        """Create MultipleArguments instance."""
        kwargs["nargs"] = -1
        default = kwargs.pop("default", tuple())
        super().__init__(*args, **kwargs)
        self.default = default

    def full_process_value(self, ctx: Context, value: Any) -> Any:
        """
        Given a value and context this runs the logic to convert the value as necessary.

        :param ctx: command context
        :param value: value for option parsed from command line

        :return: value for option
        """
        if not value:
            value = self.default
        else:
            value = [self._parse_arg_str(i) for i in value]
        return super().process_value(ctx, value)

    def _parse_arg_str(self, args: str) -> Tuple[Any]:
        """
        Parse arguments string to tuple.

        :param args: arguments string sperated by comma

        :return: tuple of parsed arguments
        """
        parsed = ast.literal_eval(args)

        if not isinstance(parsed, tuple):
            parsed = (parsed,)

        return parsed


class TestCli:
    """Performance test client."""

    def __init__(
        self,
        func: Callable,
        executor_class=Executor,
        report_printer_class=ReportPrinter,
    ):
        """
        Make performance client.

        :param func: function to be tested.
        :param executor_class: executor to be used for testing
        :param report_printer_class: report printer to print results


        func - should be function with first parameter multithreading.Queue
        func  - should have docstring, and default values for every extra argument.

        Exmple of usage:

        def test_fn(benchmark: BenchmarkControl, list_size: int = 1000000):
            # test list iteration
            # prepare some data:
            big_list = list(range(list_size))

            # ready for test
            benchmark.start()

            for i in range(big_list):
                i ** 2  # actually do nothing

        TestCli(test_fn).run()
        """
        self.func_details = BenchmarkFuncDetails(func)
        self.func_details.check()
        self.func = func
        self.executor_class = Executor
        self.report_printer_class = report_printer_class

    def _make_command(self) -> Command:
        """
        Make  cli.core.Command.

        :return: a cli command
        """
        return Command(
            None,  # type: ignore
            params=self._make_command_params(),
            callback=self._command_callback,
            help=self._make_help(),
        )

    def _make_command_params(self) -> Optional[List[Parameter]]:
        """
        Make parameters and arguments for cli.Command.

        :return: list of options and arguments for cli Command
        """
        return list(self._executor_params().values()) + self._call_params()

    def _make_help(self) -> str:
        """
        Make help for command.

        :return: str.
        """
        doc_str = inspect.cleandoc(
            f"""
        {self.func_details.doc}

        ARGS is function arguments in format: `{','.join(self.func_details.argument_names)}`

        default ARGS is `{self.func_details.default_argument_values_as_string}`
        """
        )
        return doc_str

    def _executor_params(self) -> Dict[str, Parameter]:
        """
        Get parameters used by Executor.

        :return: dict of executor's parameters for cli Command
        """
        parameters = {
            "timeout": Option(
                ["--timeout"],
                default=10.0,
                show_default=True,
                help="Executor timeout in seconds",
                type=float,
            ),
            "period": Option(
                ["--period"],
                default=0.1,
                show_default=True,
                help="Period for measurement",
                type=float,
            ),
        }
        return (
            parameters  # type: ignore # for some reason mypy does not follow superclass
        )

    def _call_params(self) -> List[Parameter]:
        """
        Make command option and parameters for test cases.

        :return: function args set, number of executions option, plot option
        """
        argument = DefaultArgumentsMultiple(
            ["args"], default=[self.func_details.default_argument_values]
        )
        num_executions = Option(
            ["--num-executions", "-N"],
            default=1,
            show_default=True,
            help="Number of runs for each case",
            type=int,
        )

        plot = Option(
            ["--plot", "-P"],
            default=None,
            show_default=True,
            help="X axis parameter idx",
            type=int,
        )
        return [argument, num_executions, plot]

    def run(self) -> None:
        """
        Run performance test.

        :return: None
        """
        command = self._make_command()
        command()

    def _command_callback(self, **params) -> None:
        """
        Run test on command.

        :params params: dictionary of options and arguments of cli Command

        :return: None
        """
        arguments_list = params.pop("args")

        executor_params = {
            k: v for k, v in params.items() if k in self._executor_params()
        }
        executor = self.executor_class(**executor_params)

        num_executions = params["num_executions"]

        self.report_printer = self.report_printer_class(
            self.func_details, executor_params
        )

        self.report_printer.print_context_information()

        reports = []

        for arguments in arguments_list:
            report = self._execute_num_times(arguments, executor, num_executions)
            self.report_printer.print_report(report)
            reports.append(report)

        self._draw_plot(params, reports)

    def _draw_plot(
        self, params: Dict[str, Parameter], reports: List[PerformanceReport]
    ) -> None:
        """
        Draw a plot with case resources if param enabled by command option.

        Block by plot window shown!

        :params params: dict of command options passed
        :params reports: list of performance reports to draw charts for

        :return: None
        """
        xparam_idx = params.get("plot")

        if xparam_idx is None:
            return

        import matplotlib.pyplot as plt  # type: ignore # pylint: disable=import-outside-toplevel

        reports_sorted_by_arg = sorted(reports, key=lambda x: x.arguments[xparam_idx])  # type: ignore

        xaxis = [i.arguments[xparam_idx] for i in reports_sorted_by_arg]  # type: ignore

        _, ax = plt.subplots(3)

        # time
        self._draw_resource(ax[0], xaxis, reports_sorted_by_arg, [0], "Time")

        # cpu
        self._draw_resource(ax[1], xaxis, reports_sorted_by_arg, [1, 2, 3], "cpu")

        # mem
        self._draw_resource(ax[2], xaxis, reports_sorted_by_arg, [4, 5, 6], "mem")
        plt.show()

    def _draw_resource(
        self,
        plt: "matplotpib.axes.Axes",  # type: ignore  # noqa: F821
        xaxis: List[float],
        reports: List[PerformanceReport],
        resources_range: List[int],
        title: str,
    ) -> None:
        """
        Draw a plot for specific resource.

        :param plt: a subplot to draw on
        :param xaxis: list of values for x axis
        :param reports: performance reports to get values from
        :param resources_range: list of resource ids in performance.resource list to draw values for
        :param title: title for chart.

        :return: None
        """
        for r in resources_range:
            res = reports[0].resources[r]
            label = res.name
            plt.plot(xaxis, [i.resources[r].value for i in reports], label=label)
            plt.set_ylabel(res.unit)
            plt.set_title(title)
            plt.legend()

    def _execute_num_times(
        self, arguments: Tuple[Any], executor: Executor, num_executions: int
    ) -> PerformanceReport:
        """
        Execute case several times and provide a performance report.

        :param arguments: list of arguments for function tested.
        :param executor: executor to run tests.
        :param num_executions: how may times repeat test for arguments set.

        :return: performance report with mean values for every resource counted for multiple runs
        """
        exec_reports = [
            executor.run(self.func, arguments) for _ in range(num_executions)
        ]

        return PerformanceReport(exec_reports)

    def print_help(self) -> None:
        """
        Print help for command. can be invoked with --help option.

        :return: None
        """
        command = self._make_command()
        with click.Context(command) as ctx:  # type: ignore
            click.echo(command.get_help(ctx))
