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
"""Memory usage check."""
import time
from threading import Thread

import click

from aea.protocols.base import Message
from aea.skills.base import Handler
from benchmark.checks.utils import SyncedGeneratorConnection  # noqa: I100
from benchmark.checks.utils import (
    get_mem_usage_in_mb,
    make_agent,
    make_envelope,
    make_skill,
    multi_run,
    print_results,
    wait_for_condition,
)

from packages.fetchai.protocols.default.message import DefaultMessage


class TestHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, message: Message) -> None:
        """Handle incoming message."""
        self.context.outbox.put(make_envelope(message.to, message.sender))


def run(duration, runtime_mode):
    """Check memory usage."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    agent = make_agent(runtime_mode=runtime_mode)
    connection = SyncedGeneratorConnection.make()
    agent.resources.add_connection(connection)
    agent.resources.add_skill(make_skill(agent, handlers={"test": TestHandler}))
    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)

    connection.enable()
    time.sleep(duration)
    connection.disable()
    mem_usage = get_mem_usage_in_mb()
    agent.stop()
    t.join(5)
    rate = connection.count_in / duration

    return [
        ("envelopes received", connection.count_in),
        ("envelopes sent", connection.count_out),
        ("rate (envelopes/second)", rate),
        ("mem usage (Mb)", mem_usage),
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
