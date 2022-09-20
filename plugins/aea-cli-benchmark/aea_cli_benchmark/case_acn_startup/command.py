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
"""Check amount of time for acn connection start."""

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
    ("protocol", "valory/acn"),
    ("connection", "valory/p2p_libp2p"),
    ("connection", "valory/p2p_libp2p_client"),
    ("connection", "valory/p2p_libp2p_mailbox"),
]


@click.command(name="acn_startup")
@click.option(
    "--connection",
    default="p2pnode",
    help="Connection to use.",
    show_default=True,
    type=click.Choice(["p2pnode", "mailbox", "client"]),
)
@click.option(
    "--connect-times",
    default=10,
    help="How many time perform connection.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(
    connection: str, connect_times: int, number_of_runs: int, output_format: str
) -> Any:
    """Check connection connect time."""
    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_acn_startup.case import run

        parameters = {
            "Connection": connection,
            "Number of connects": connect_times,
            "Number of runs": number_of_runs,
        }

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (
                    connection,
                    connect_times,
                ),
            )

        return print_results(output_format, parameters, result_fn)
