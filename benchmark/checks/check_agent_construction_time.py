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
import os
import shutil
import time
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from typing import List, Tuple, Union

import click
from click.testing import CliRunner

from aea.aea_builder import AEABuilder
from aea.cli.core import cli
from benchmark.checks.utils import get_mem_usage_in_mb, multi_run, print_results


PACKAGES = Path(__file__).parent / "../../packages"
PROJECT_PATH = str(PACKAGES / "fetchai/agents/my_first_aea")


def run(agents: int) -> List[Tuple[str, Union[int, float]]]:
    """Check construction time and memory usage."""
    load_times = []
    full_times = []
    with TemporaryDirectory() as tmp_dir:
        agent_dir = Path(tmp_dir) / "agent"
        shutil.copytree(PROJECT_PATH, agent_dir)
        shutil.copytree(PACKAGES, agent_dir / "vendor")
        os.chdir(agent_dir)
        if (
            CliRunner()
            .invoke(cli, ["generate-key", "fetchai"], catch_exceptions=False)
            .exit_code
            != 0
        ):
            raise Exception("generate-key failed")
        if (
            CliRunner()
            .invoke(cli, ["add-key", "fetchai"], catch_exceptions=False)
            .exit_code
            != 0
        ):
            raise Exception("add-key failed")
        agents_list = []
        env_mem_usage = get_mem_usage_in_mb()
        for _ in range(agents):
            start_time = time.time()
            builder = AEABuilder.from_aea_project(agent_dir)
            load_times.append(time.time() - start_time)
            agents_list.append(builder.build())
            full_times.append(time.time() - start_time)
        mem_usage = get_mem_usage_in_mb()

    return [
        ("avg config load time", mean(load_times)),
        ("avg full construction", mean(full_times)),
        ("avg build time", mean(full_times) - mean(load_times)),
        ("agent mem usage (Mb)", mem_usage - env_mem_usage),
    ]


@click.command()
@click.option("--agents", default=25, help="Amount of agents to construct.")
@click.option("--number_of_runs", default=10, help="How many times run test.")
def main(agents: int, number_of_runs: int) -> None:
    """Check agents construction time and memory usage."""
    click.echo("Start test with options:")
    click.echo(f"* Agents: {agents}")
    click.echo(f"* Number of runs: {number_of_runs}")

    print_results(multi_run(int(number_of_runs), run, (agents,),))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
