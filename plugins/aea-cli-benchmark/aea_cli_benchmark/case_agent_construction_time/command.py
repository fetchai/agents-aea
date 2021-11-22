#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""Check amount of time and mem for agent setup."""

from typing import Any, List, Tuple

import click
from aea_cli_benchmark.utils import (
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
)


CASE_NAME = "agent_construction_time"


@click.command(name=CASE_NAME)
@number_of_runs_deco
@output_format_deco
def main(number_of_runs: int, output_format: str) -> Any:
    """Agent's construction time and memory usage."""
    from aea_cli_benchmark.case_agent_construction_time.case import run

    parameters = {"Number of runs": number_of_runs}

    def result_fn() -> List[Tuple[str, Any, Any, Any]]:
        return multi_run(int(number_of_runs), run, (),)

    return print_results(output_format, CASE_NAME, parameters, result_fn)
