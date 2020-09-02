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
import time
from threading import Thread

from benchmark.checks.utils import SyncedGeneratorConnection, make_agent, make_envelope
from benchmark.checks.utils import make_skill, wait_for_condition

import click

from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Behaviour


class TestBehaviour(Behaviour):
    """Dummy handler to handle messages."""

    _tick_interval = 1

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self._count = 0

    def teardown(self) -> None:
        """Tear up behaviour."""

    def act(self):
        """Perform action on periodic basis."""
        s = time.time()
        while time.time() - s < self.tick_interval:
            self.context.outbox.put(make_envelope("1", "2"))
            self._count += 1


@click.command()
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
def main(duration, runtime_mode):
    """Test act message generate performance."""
    click.echo(f"Start test for {duration} seconds in runtime mode: {runtime_mode}")
    agent = make_agent(runtime_mode=runtime_mode)
    connection = SyncedGeneratorConnection.make()
    agent.resources.add_connection(connection)
    skill = make_skill(agent, behaviours={"test": TestBehaviour})
    agent.resources.add_skill(skill)
    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)

    time.sleep(duration)
    agent.stop()
    t.join(5)

    rate = connection._count_in / duration
    click.echo(f"Test finished:")
    click.echo(f' * envelopes sent: {skill.behaviours["test"]._count}')
    click.echo(f" * envelopes received: {connection._count_in}")
    click.echo(f" * rate: {rate} envelopes/second")


if __name__ == "__main__":
    main()
