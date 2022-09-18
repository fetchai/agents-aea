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
"""Check amount of time and mem for agent setup."""
import os
import time
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from typing import List, Tuple, Union

from aea_cli_benchmark.utils import get_mem_usage_in_mb
from click.testing import CliRunner

from aea import AEA_DIR as _AEA_DIR
from aea.aea_builder import AEABuilder


AEA_DIR = Path(_AEA_DIR)
PACKAGES_DIR = AEA_DIR.parent / "packages"


def run(agents: int) -> List[Tuple[str, Union[int, float]]]:
    """Check construction time and memory usage."""
    from aea.cli.core import cli

    load_times = []
    full_times = []
    with TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        if (
            CliRunner()
            .invoke(
                cli,
                [
                    f"--registry-path={PACKAGES_DIR}",
                    "fetch",
                    "--local",
                    "fetchai/my_first_aea",
                    "--alias",
                    "agent",
                ],
                catch_exceptions=False,
            )
            .exit_code
            != 0
        ):
            raise Exception("fetch failed")
        agent_dir = Path(tmp_dir) / "agent"
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
