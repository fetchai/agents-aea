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

import click

from aea.skills.base import Behaviour
from benchmark.checks.utils import SyncedGeneratorConnection  # noqa: I100
from benchmark.checks.utils import (
    make_agent,
    make_envelope,
    make_skill,
    multi_run,
    print_results,
    wait_for_condition,
)

from packages.fetchai.protocols.default.message import DefaultMessage


class TestBehaviour(Behaviour):
    """Dummy handler to handle messages."""

    _tick_interval = 1

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self.count = 0  # pylint: disable=attribute-defined-outside-init

    def teardown(self) -> None:
        """Tear up behaviour."""

    def act(self):
        """Perform action on periodic basis."""
        s = time.time()
        while time.time() - s < self.tick_interval:
            self.context.outbox.put(make_envelope("1", "2"))
            self.count += 1


def run(duration, runtime_mode):
    """Test act message generate performance."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

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

    rate = connection.count_in / duration
    return [
        ("envelopes sent", skill.behaviours["test"].count),
        ("envelopes received", connection.count_in),
        ("rate(envelopes/second)", rate),
    ]


@click.command()
@click.option("--duration", default=3, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@click.option("--number_of_runs", default=10, help="How many times run test.")
def main(duration, runtime_mode, number_of_runs):
    """Run test."""
    click.echo("Start test with options:")
    click.echo(f"* Duration: {duration} seconds")
    click.echo(f"* Runtime mode: {runtime_mode}")
    click.echo(f"* Number of runs: {number_of_runs}")

    print_results(multi_run(int(number_of_runs), run, (duration, runtime_mode),))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
