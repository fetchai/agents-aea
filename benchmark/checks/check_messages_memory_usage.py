#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
import os
import sys
import time
from typing import Any, List, Tuple, Union

import click

from aea.protocols.base import Message
from benchmark.checks.utils import get_mem_usage_in_mb  # noqa: I100
from benchmark.checks.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
)

from packages.fetchai.protocols.default.message import DefaultMessage


ROOT_PATH = os.path.join(os.path.abspath(__file__), "..", "..")
sys.path.append(ROOT_PATH)


def make_message() -> Message:
    """Create a message."""
    return DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"",
    )


def run(messages_amount: int) -> List[Tuple[str, Union[int, float]]]:
    """Test messages generation and memory consumption."""
    messages: List[Any] = [
        0 for i in range(messages_amount)
    ]  # generate dummy list to count list structure memory
    mem_usage_on_start = get_mem_usage_in_mb()

    start_time = time.time()
    for i in range(messages_amount):
        messages[i] = make_message()
    mem_usage = get_mem_usage_in_mb()

    return [
        ("Mem usage(Mb)", mem_usage - mem_usage_on_start),
        ("Time (seconds)", time.time() - start_time),
    ]


@click.command()
@click.option("--messages", default=10**6, help="Amount of messages.")
@number_of_runs_deco
@output_format_deco
def main(messages: int, number_of_runs: int, output_format: str) -> Any:
    """Run test."""
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
