#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
from typing import Any, List, Optional, Tuple, Union

import click

from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.registries.resources import Resources
from aea.skills.base import Handler
from benchmark.checks.utils import GeneratorConnection  # noqa: I100
from benchmark.checks.utils import (
    SyncedGeneratorConnection,
    make_agent,
    make_envelope,
    make_skill,
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    wait_for_condition,
)

from packages.fetchai.protocols.default.message import DefaultMessage


class TestConnectionMixIn:
    """Test connection with messages timing."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Init connection."""
        super().__init__(*args, **kwargs)  # type: ignore
        self.sends: List[float] = list()
        self.recvs: List[float] = list()

    async def send(self, envelope: Envelope) -> None:
        """Handle incoming envelope."""
        self.recvs.append(time.time())
        return await super().send(envelope)  # type: ignore

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """Generate outgoing envelope."""
        envelope = await super().receive(*args, **kwargs)  # type: ignore
        self.sends.append(time.time())
        return envelope


CONNECTION_MODES = {"sync": SyncedGeneratorConnection, "nonsync": GeneratorConnection}


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


def run(
    duration: int, runtime_mode: str, connection_mode: str
) -> List[Tuple[str, Union[int, float]]]:
    """Test memory usage."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    resources = Resources()
    if connection_mode not in CONNECTION_MODES:
        raise ValueError(
            f"bad connection mode {connection_mode}. valid is one of {list(CONNECTION_MODES.keys())}"
        )

    base_cls = CONNECTION_MODES[connection_mode]

    conn_cls = type("conn_cls", (TestConnectionMixIn, base_cls), {})
    connection = conn_cls.make()  # type: ignore # pylint: disable=no-member
    resources.add_connection(connection)

    agent = make_agent(runtime_mode=runtime_mode, resources=resources)
    agent.resources.add_skill(make_skill(agent, handlers={"test": TestHandler}))
    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)

    connection.enable()
    time.sleep(duration)
    connection.disable()
    time.sleep(0.2)  # possible race condition in stop?
    agent.stop()
    t.join(5)

    latency = mean(
        map(
            lambda x: x[1] - x[0],
            zip(
                connection.sends,
                connection.recvs,
            ),
        )
    )
    total_amount = len(connection.recvs)
    rate = total_amount / duration
    return [
        ("envelopes received", len(connection.recvs)),
        ("envelopes sent", len(connection.sends)),
        ("latency(ms)", 10 ** 6 * latency),
        ("rate(envelopes/second)", rate),
    ]


@click.command()
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@click.option(
    "--connection_mode", default="sync", help="Connection mode: sync or nonsync."
)
@number_of_runs_deco
@output_format_deco
def main(
    duration: int,
    runtime_mode: str,
    connection_mode: str,
    number_of_runs: int,
    output_format: str,
) -> Any:
    """Run test."""
    parameters = {
        "Duration(seconds)": duration,
        "Runtime mode": runtime_mode,
        "Connection mode": connection_mode,
        "Number of runs": number_of_runs,
    }

    def result_fn() -> List[Tuple[str, Any, Any, Any]]:
        return multi_run(
            int(number_of_runs),
            run,
            (duration, runtime_mode, connection_mode),
        )

    return print_results(output_format, parameters, result_fn)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
