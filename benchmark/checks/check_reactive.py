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
"""Latency and throughput check."""
import time
from statistics import mean
from threading import Thread
from typing import Optional

from benchmark.checks.utils import (
    SyncedGeneratorConnection,
    make_agent,
    make_envelope,
    make_skill,
    wait_for_condition,
)

import click

from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler


class TestConnection(SyncedGeneratorConnection):
    """Test connection with messages timing."""

    def __init__(self, *args, **kwargs):
        """Init connection."""
        super().__init__(*args, **kwargs)
        self._sends = list()
        self._recvs = list()

    async def send(self, envelope: "Envelope") -> None:
        """Handle incoming envelope."""
        self._recvs.append(time.time())
        return await super().send(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Generate outgoing envelope."""
        envelope = await super().receive(*args, **kwargs)
        self._sends.append(time.time())
        return envelope


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
    """Test memory usage."""
    click.echo(f"Start test for {duration} seconds in runtime mode: {runtime_mode}")
    agent = make_agent(runtime_mode=runtime_mode)
    connection = TestConnection.make()
    agent.resources.add_connection(connection)
    agent.resources.add_skill(make_skill(agent, handlers={"test": TestHandler}))
    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)

    connection.enable()
    time.sleep(duration)
    connection.disable()
    agent.stop()
    t.join(5)

    latency = mean(
        map(lambda x: x[1] - x[0], zip(connection._sends, connection._recvs,))
    )
    total_amount = len(connection._recvs)
    rate = total_amount / duration
    click.echo(f"Test finished:")
    click.echo(f" * envelopes received: {len(connection._recvs)}")
    click.echo(f" * envelopes sent: {len(connection._sends)}")
    click.echo(f" * latency: {latency} second")
    click.echo(f" * rate: {rate} envelopes/second")


if __name__ == "__main__":
    main()
