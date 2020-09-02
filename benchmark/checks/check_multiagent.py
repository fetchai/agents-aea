#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Envelopes generation speed for Behaviour act test."""
import os
import sys
import time

from benchmark.checks.utils import get_mem_usage_in_mb, make_agent, make_envelope
from benchmark.checks.utils import make_skill, wait_for_condition

import click

from aea.configurations.base import ConnectionConfig
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.runner import AEARunner
from aea.skills.base import Handler


ROOT_PATH = os.path.join(os.path.abspath(__file__), "..", "..")
sys.path.append(ROOT_PATH)

from packages.fetchai.connections.local.connection import (
    LocalNode,
    OEFLocalConnection,
)  # noqa:  E402


class TestHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""
        self._count = 0

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, message: Message) -> None:
        """Handle incoming message."""
        self._count += 1
        self.context.outbox.put(make_envelope(message.to, message.sender))


@click.command()
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@click.option("--runner_mode", default="async", help="Runtime mode: async or threaded.")
@click.option(
    "--start_messages", default=100, help="Amount of messages to prepopulate."
)
def main(duration, runtime_mode, runner_mode, start_messages):
    """Test multiagent message exchange."""
    click.echo(f"Start test with options:")
    click.echo(f"* Duration: {duration} seconds")
    click.echo(f"* Runtime mode: {runtime_mode}")
    click.echo(f"* Runner mode: {runner_mode}")
    click.echo(f"* Start messages: {start_messages}")
    local_node = LocalNode()
    agent1 = make_agent(agent_name="agent1", runtime_mode=runtime_mode)

    connection1 = OEFLocalConnection(
        local_node,
        configuration=ConnectionConfig(connection_id=OEFLocalConnection.connection_id,),
        identity=agent1.identity,
    )
    agent1.resources.add_connection(connection1)
    skill1 = make_skill(agent1, handlers={"test": TestHandler})
    agent1.resources.add_skill(skill1)

    agent2 = make_agent(agent_name="agent2", runtime_mode=runtime_mode)
    connection2 = OEFLocalConnection(
        local_node,
        configuration=ConnectionConfig(connection_id=OEFLocalConnection.connection_id,),
        identity=agent2.identity,
    )
    agent2.resources.add_connection(connection2)
    skill2 = make_skill(agent2, handlers={"test": TestHandler})
    agent2.resources.add_skill(skill2)

    local_node.start()

    runner = AEARunner([agent1, agent2], runner_mode)
    runner.start(threaded=True)

    wait_for_condition(lambda: runner.is_running, timeout=5)
    wait_for_condition(lambda: agent2.is_running, timeout=5)
    wait_for_condition(lambda: agent1.is_running, timeout=5)

    time.sleep(1)

    env1 = make_envelope(connection1.address, connection2.address)
    env2 = make_envelope(connection2.address, connection1.address)
    for _ in range(int(start_messages)):
        agent1.outbox.put(env1)
        agent2.outbox.put(env2)

    time.sleep(duration)

    mem_usage = get_mem_usage_in_mb()

    runner.stop()
    local_node.stop()

    total_messages = skill1.handlers["test"]._count + skill2.handlers["test"]._count
    rate = total_messages / duration
    click.echo(f"\nResults:")
    click.echo(f" * Total Messages handled1: {total_messages}")
    click.echo(f" * Messages handled by agent1: {skill1.handlers['test']._count}")
    click.echo(f" * Messages handled by agent2: {skill2.handlers['test']._count}")
    click.echo(f" * Messages rate: {rate}")
    click.echo(f" * mem usage: {mem_usage} mb")
    click.echo(f"Test finished.")


if __name__ == "__main__":
    main()
