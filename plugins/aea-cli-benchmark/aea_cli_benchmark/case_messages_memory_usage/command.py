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
"""Memory usage of huge amount of messages."""
from typing import Any, List, Tuple

import click
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    with_packages,
)


PACKAGES = [("protocol", "fetchai/default")]


@click.command(name="messages_mem_usage")
@click.option(
    "--messages",
    default=10**6,
    help="Amount of messages.",
    show_default=True,
)
@number_of_runs_deco
@output_format_deco
def main(messages: int, number_of_runs: int, output_format: str) -> Any:
    """Check messages memory usage."""
    with with_packages(PACKAGES):
        from aea_cli_benchmark.case_messages_memory_usage.case import run

        parameters = {"Messages": messages, "Number of runs": number_of_runs}

        def result_fn() -> List[Tuple[str, Any, Any, Any]]:
            return multi_run(
                int(number_of_runs),
                run,
                (int(messages),),
            )

        return print_results(output_format, parameters, result_fn)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
