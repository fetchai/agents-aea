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
"""This module contains the implementation of `benchmark` cli command."""

import click
from aea_cli_benchmark import (
    check_agent_construction_time,
    check_decision_maker,
    check_dialogues_memory_usage,
    check_mem_usage,
    check_messages_memory_usage,
    check_multiagent,
    check_multiagent_http_dialogues,
    check_proactive,
    check_reactive,
)


@click.group()
@click.pass_context
def benchmark(click_context: click.Context) -> None:  # pylint: disable=unused-argument
    """Run one of performance benchmark."""


benchmark.add_command(check_agent_construction_time.main)

benchmark.add_command(check_decision_maker.main)

benchmark.add_command(check_dialogues_memory_usage.main)

benchmark.add_command(check_mem_usage.main)

benchmark.add_command(check_messages_memory_usage.main)

benchmark.add_command(check_multiagent_http_dialogues.main)

benchmark.add_command(check_multiagent.main)

benchmark.add_command(check_proactive.main)

benchmark.add_command(check_reactive.main)
