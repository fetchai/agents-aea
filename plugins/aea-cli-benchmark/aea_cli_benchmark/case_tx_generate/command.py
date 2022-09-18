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
"""Ledger TX generation and processing benchmark."""
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
    ("protocol", "fetchai/fipa"),
    ("protocol", "fetchai/ledger_api"),
    ("connection", "fetchai/ledger"),
]


@click.command(name="tx_generate")
@click.option(
    "--ledger_id",
    type=click.Choice(["ethereum", "fetchai"]),
    default="fetchai",
    help="Ledger id",
    show_default=True,
)
@click.option(
    "--test-time",
    default=30,
    help="Time to generate txs in seconds",
    show_default=True,
    type=float,
)
@number_of_runs_deco
@output_format_deco
def main(
    ledger_id: str, test_time: float, number_of_runs: int, output_format: str
) -> Any:
    """Check performance of decision maker on signature signing."""
    with with_packages(PACKAGES):
        import sys

        sys.path.insert(0, "/home/solarw/fetchai/agents-aea")

        from aea_cli_benchmark.case_tx_generate.case import run

        parameters = {
            "Ledger id": ledger_id,
            "Test time": test_time,
            "Number of runs": number_of_runs,
        }

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (
                    ledger_id,
                    test_time,
                ),
            )

        return print_results(output_format, parameters, result_fn)
