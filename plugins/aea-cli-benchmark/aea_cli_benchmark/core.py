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
"""This module contains the implementation of `benchmark` cli command."""
import collections
import sys
from collections import namedtuple
from copy import deepcopy
from typing import Dict, List, Optional

import click
from aea_cli_benchmark.case_acn_communication.command import (
    main as case_acn_communication,
)
from aea_cli_benchmark.case_acn_startup.command import main as case_acn_startup
from aea_cli_benchmark.case_agent_construction_time.command import (
    main as case_agent_construction_time,
)
from aea_cli_benchmark.case_decision_maker.command import main as case_decision_maker
from aea_cli_benchmark.case_dialogues_memory_usage.command import (
    main as case_dialogues_memory_usage,
)
from aea_cli_benchmark.case_mem_usage.command import main as case_mem_usage
from aea_cli_benchmark.case_messages_memory_usage.command import (
    main as case_messages_memory_usage,
)
from aea_cli_benchmark.case_multiagent.command import main as case_mulltiagent
from aea_cli_benchmark.case_multiagent_http_dialogues.command import (
    main as case_multiagent_http_dialogues,
)
from aea_cli_benchmark.case_proactive.command import main as case_proactive
from aea_cli_benchmark.case_reactive.command import main as case_reactive
from aea_cli_benchmark.case_tx_generate.command import main as case_tx_generate

from aea.helpers.yaml_utils import yaml_dump_all, yaml_load_all


@click.group()
@click.pass_context
def benchmark(click_context: click.Context) -> None:  # pylint: disable=unused-argument
    """Run one of performance benchmark."""


benchmark.add_command(case_agent_construction_time)

benchmark.add_command(case_decision_maker)

benchmark.add_command(case_dialogues_memory_usage)

benchmark.add_command(case_mem_usage)

benchmark.add_command(case_messages_memory_usage)

benchmark.add_command(case_multiagent_http_dialogues)

benchmark.add_command(case_mulltiagent)

benchmark.add_command(case_proactive)

benchmark.add_command(case_reactive)
benchmark.add_command(case_tx_generate)
benchmark.add_command(case_acn_startup)
benchmark.add_command(case_acn_communication)

INTERNAL_COMMANDS = ["make-config", "run"]


BenchmarkCase = namedtuple("BenchmarkCase", ["command", "params", "name"])


@click.command(name="run")
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
def run(file: Optional[str]):
    """Run benchmarks."""
    if file is not None:
        with open(file, "r") as f:
            cases = _make_cases_from_dicts(yaml_load_all(f))
    else:
        cases = _enlist_cases()
    for case in cases.values():
        click.echo(f"Run case: {case.name}")
        case.command.callback(**case.params)
        click.echo("\n")


def _make_cases_from_dicts(case_definitions: List[Dict]) -> List[BenchmarkCase]:
    base_cases = _enlist_cases()
    case_definitions = deepcopy(case_definitions)
    cases = {}

    for case_def in case_definitions:
        case_name = case_def.pop("name")
        if case_name not in base_cases:
            raise ValueError(f"Unknown case named: {case_name}")
        cases[case_name] = BenchmarkCase(
            name=case_name, params=case_def, command=base_cases[case_name].command
        )
    return cases


def _enlist_cases() -> Dict[str, BenchmarkCase]:
    cases = {}
    for name, command in benchmark.commands.items():
        if name in INTERNAL_COMMANDS:
            continue
        cases[name] = BenchmarkCase(
            command=command,
            name=name,
            params={i.name: i.default for i in command.params},
        )

    return cases


@click.command(name="make-config")
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(file_okay=True, dir_okay=False),
    required=False,
)
def make_config(file: Optional[str]):
    """Make an example config."""

    def make_section(case: BenchmarkCase) -> Dict:
        result = collections.OrderedDict()
        result["name"] = case.name
        for k, v in sorted(case.params.items(), key=lambda x: x[0]):
            result[k] = v
        return result

    configs = [make_section(case) for case in _enlist_cases().values()]

    if file is not None:
        with open(file, "w") as f:
            yaml_dump_all(configs, stream=f)
    else:
        yaml_dump_all(
            configs,
            stream=sys.stdout,
        )


benchmark.add_command(run)
benchmark.add_command(make_config)
