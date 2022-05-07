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
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Tuple, Union

from aea_cli_benchmark.utils import get_mem_usage_in_mb
from click.testing import CliRunner

from aea.aea_builder import AEABuilder


def run() -> List[Tuple[str, Union[int, float]]]:
    """Check construction time and memory usage."""
    from aea.cli.core import cli

    with TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        if (
            CliRunner()
            .invoke(
                cli,
                ["fetch", "fetchai/my_first_aea", "--alias", "agent"],
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
        start_time = time.time()
        builder = AEABuilder.from_aea_project(agent_dir)
        load_time = time.time() - start_time
        agents_list.append(builder.build())
        full_time = time.time() - start_time
        build_time = time.time() - load_time
        mem_usage = get_mem_usage_in_mb()

    return [
        ("Average configuration load time", agents_list),
        ("Average full construction", full_time),
        ("Average build time", build_time),
        ("Agent memory usage (Mb)", mem_usage - env_mem_usage),
    ]
