# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Latency and throughput check."""
from typing import Any, List, Tuple

import click
from aea_cli_benchmark.case_reactive.readme import README
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    runtime_mode_deco,
    with_packages,
)


CASE_NAME = "reactive"
PACKAGES = [("protocol", "fetchai/signing"), ("protocol", "fetchai/default")]


@click.command(name=CASE_NAME, help=README)
@click.option(
    "--duration",
    default=1,
    type=click.IntRange(1,),
    help="Run time in seconds.",
    show_default=True,
)
@runtime_mode_deco
@click.option(
    "--connection_mode",
    type=click.Choice(["sync", "nonsync"]),
    default="sync",
    help="Connection mode: sync or nonsync.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(
    duration: int,
    runtime_mode: str,
    connection_mode: str,
    number_of_runs: int,
    output_format: str,
) -> Any:
    """Check envelopes send/received rate within connection."""
    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_reactive.case import run

        parameters = {
            "Duration(seconds)": duration,
            "Runtime mode": runtime_mode,
            "Connection mode": connection_mode,
            "Number of runs": number_of_runs,
        }

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs), run, (duration, runtime_mode, connection_mode),
            )

        return print_results(output_format, CASE_NAME, parameters, result_fn)
