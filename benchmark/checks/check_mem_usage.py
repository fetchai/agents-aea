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

from benchmark.checks.utils import (
    SyncedGeneratorConnection,
    get_mem_usage_in_mb,
    make_agent,
    make_envelope,
    make_skill,
    wait_for_condition,
)

import click

from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler


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


@click.command()
@click.option("--duration", default=3, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
def main(duration, runtime_mode):
    """Check memory usage."""
    click.echo(f"Start test for {duration} seconds in runtime mode: {runtime_mode}")
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
    rate = connection._count_in / duration
    click.echo(f"Test finished:")
    click.echo(f" * envelopes received: {connection._count_in}")
    click.echo(f" * envelopes sent: {connection._count_out}")
    click.echo(f" * rate: {rate} envelopes/second")
    click.echo(f" * mem usage: {mem_usage} mb")


if __name__ == "__main__":
    main()
