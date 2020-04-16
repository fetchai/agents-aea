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
from typing import Any, Callable, Dict, List, Optional

import click
from click.core import Argument, Command, Context, Option, Parameter

from .executor import Executor
from .func_details import FuncDetails
from .report_printer import PerformanceReportPrinter


class DefaultArgumentsMultiple(Argument):
    """Multiple arguments with default value."""

    def __init__(self, *args, **kwargs):
        """Create MultipleArguments instance."""
        kwargs["nargs"] = -1
        default = kwargs.pop("default", tuple())
        super().__init__(*args, **kwargs)
        self.default = default

    def full_process_value(self, ctx: Context, value: Any) -> Any:
        """Given a value and context this runs the logic to convert the value as necessary."""
        return super().process_value(ctx, value or self.default)


class TestCli:
    """Performance test client."""

    def __init__(
        self,
        func: Callable,
        executor_class=Executor,
        report_printer_class=PerformanceReportPrinter,
    ):
        """
        Make performance client.

        func - should be function with first parameter multithreading.Queue.
        func  - should have docstring, and default values for every extra argument.
        """
        self.func_details = FuncDetails(func)
        self.func_details.check()
        self.func = func
        self.executor_class = Executor
        self.report_printer_class = report_printer_class

    def _make_command(self) -> Command:
        """Make  cli.core.Command."""
        return Command(
            None,  # type: ignore
            params=self._make_command_params(),
            callback=self._callback,
            help=self._make_help(),
        )

    def _make_command_params(self) -> Optional[List[Parameter]]:
        """Make parameters and arguments for cli.Command."""
        return list(self.executor_params().values()) + [self._function_args()]

    def _make_help(self) -> str:
        """Make help for command."""
        return inspect.cleandoc(
            f"""
        {self.func_details.doc}

        ARGS is function arguments in format: `{','.join(self.func_details.argument_names)}`

        default ARGS is `{self.func_details.default_argument_values_as_string}`
        """
        )

    def executor_params(self) -> Dict[str, Parameter]:
        """Get parameters used by Executor."""
        return {
            "timeout": Option(
                ["--timeout"],
                default=10,
                show_default=True,
                help="Executor timeout in seconds",
            ),
            "period": Option(
                ["--period"],
                default=0.1,
                show_default=True,
                help="Period for measurement",
            ),
        }

    def _function_args(self) -> Parameter:
        """Get arguments requireed by test function."""
        return DefaultArgumentsMultiple(
            ["args"], default=[self.func_details.default_argument_values_as_string],
        )

    def run(self) -> None:
        """Run performance test."""
        command = self._make_command()
        command()

    def _callback(self, **exec_params) -> None:
        """Run test on command."""
        args_list = exec_params.pop("args")

        executor = self.executor_class(**exec_params)
        exec_reports = []

        for args in args_list:
            exec_report = executor.run(self.func, self._parse_arg_str(args))
            exec_reports.append(exec_report)
            report_printer = self.report_printer_class(
                self.func_details, exec_params, [exec_report]
            )
            report_printer.print_()

    def _parse_arg_str(self, args: str) -> tuple:
        """Parse arguments string to tuple."""
        parsed = ast.literal_eval(args)

        if not isinstance(parsed, tuple):
            parsed = (parsed,)

        return parsed

    def print_help(self) -> None:
        """Print help for command. can be invoked with --help option."""
        command = self._make_command()
        with click.Context(command) as ctx:  # type: ignore
            click.echo(command.get_help(ctx))
