# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Envelopes generation speed for Behaviour act test."""
from typing import Any, List, Tuple

import click
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    with_packages,
)


PACKAGES = [
    ("protocol", "open_aea/signing"),
    ("protocol", "fetchai/default"),
    ("protocol", "fetchai/http"),
    ("connection", "fetchai/local"),
    ("protocol", "fetchai/oef_search"),
]


@click.command(name="multiagent_message_exchange")
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@click.option("--runner_mode", default="async", help="Runtime mode: async or threaded.")
@click.option(
    "--start_messages", default=100, help="Amount of messages to prepopulate."
)
@click.option("--num_of_agents", default=2, help="Amount of agents to run.")
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
    """Test multiagent message exchange."""
    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_multiagent.case import run

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

        return print_results(output_format, parameters, result_fn)
