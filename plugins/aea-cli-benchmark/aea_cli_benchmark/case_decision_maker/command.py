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
    with_packages,
)


PACKAGES = [("protocol", "open_aea/signing")]


@click.command(name="decision_maker")
@click.option(
    "--ledger_id",
    type=click.Choice(["ethereum", "cosmos", "fetchai"]),
    default="fetchai",
    help="Ledger id",
    show_default=True,
)
@click.option(
    "--amount_of_tx", default=100, help="Amount of tx to sign", show_default=True
)
@number_of_runs_deco
@output_format_deco
def main(
    ledger_id: str, amount_of_tx: int, number_of_runs: int, output_format: str
) -> Any:
    """Check performance of decision maker on signature signing."""

    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_decision_maker.case import run

        parameters = {
            "Ledger id": ledger_id,
            "Amount of txs": amount_of_tx,
            "Number of runs": number_of_runs,
        }

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (
                    ledger_id,
                    amount_of_tx,
                ),
            )

        return print_results(output_format, parameters, result_fn)
