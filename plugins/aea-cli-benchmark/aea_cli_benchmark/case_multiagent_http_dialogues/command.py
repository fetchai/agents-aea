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
"""Memory usage across the time."""
from typing import Any, List, Tuple

import click
from aea_cli_benchmark.case_multiagent_http_dialogues.readme import README
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    runtime_mode_deco,
    with_packages,
)


CASE_NAME = "multiagent_http_dialogues"
PACKAGES = [
    ("protocol", "fetchai/signing"),
    ("protocol", "fetchai/default"),
    ("protocol", "fetchai/http"),
    ("connection", "fetchai/local"),
    ("protocol", "fetchai/oef_search"),
]


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
    "--runner_mode",
    type=click.Choice(["async", "threaded"]),
    default="async",
    help="Runtime mode: async or threaded.",
    show_default=True,
)
@click.option(
    "--start_messages",
    default=100,
    type=click.IntRange(1,),
    help="Amount of messages to prepopulate.",
    show_default=True,
)
@click.option(
    "--num_of_agents",
    type=click.IntRange(2,),
    default=2,
    help="Amount of agents to run.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(
    duration: int,
    runtime_mode: str,
    runner_mode: str,
    start_messages: int,
    num_of_agents: int,
    number_of_runs: int,
    output_format: str,
) -> Any:
    """Check http dialogues memory usage for multiple agents set."""
    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_multiagent_http_dialogues.case import run

        parameters = {
            "Duration(seconds)": duration,
            "Runtime mode": runtime_mode,
            "Runner mode": runner_mode,
            "Start messages": start_messages,
            "Number of agents": num_of_agents,
            "Number of runs": number_of_runs,
        }

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (duration, runtime_mode, runner_mode, start_messages, num_of_agents),
            )

        return print_results(output_format, CASE_NAME, parameters, result_fn)
