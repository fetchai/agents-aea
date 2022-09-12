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
"""Memory usage check."""
from typing import Any, List, Tuple

import click
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    runtime_mode_deco,
    with_packages,
)


PACKAGES = [("protocol", "fetchai/default"), ("protocol", "open_aea/signing")]


@click.command(name="mem_usage")
@click.option("--duration", default=3, help="Run time in seconds.", show_default=True)
@runtime_mode_deco
@number_of_runs_deco
@output_format_deco
def main(
    duration: int, runtime_mode: str, number_of_runs: int, output_format: str
) -> Any:
    """Run memory usage benchmark."""
    parameters = {
        "Duration(seconds)": duration,
        "Runtime mode": runtime_mode,
        "Number of runs": number_of_runs,
    }

    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_mem_usage.case import run

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (duration, runtime_mode),
            )

        return print_results(output_format, parameters, result_fn)
