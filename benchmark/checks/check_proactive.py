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
from typing import Any, List, Tuple, Union, cast

import click

from aea.registries.resources import Resources
from aea.skills.base import Behaviour
from benchmark.checks.utils import SyncedGeneratorConnection  # noqa: I100
from benchmark.checks.utils import (
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


class TestBehaviour(Behaviour):
    """Dummy handler to handle messages."""

    _tick_interval = 1

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self.count = 0  # pylint: disable=attribute-defined-outside-init

    def teardown(self) -> None:
        """Tear up behaviour."""

    def act(self) -> None:
        """Perform action on periodic basis."""
        s = time.time()
        while time.time() - s < self.tick_interval:
            self.context.outbox.put(make_envelope("1", "2"))
            self.count += 1


def run(duration: int, runtime_mode: str) -> List[Tuple[str, Union[int, float]]]:
    """Test act message generate performance."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    resources = Resources()
    connection = SyncedGeneratorConnection.make()
    resources.add_connection(connection)
    agent = make_agent(runtime_mode=runtime_mode, resources=resources)
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
        ("envelopes sent", cast(TestBehaviour, skill.behaviours["test"]).count),
        ("envelopes received", connection.count_in),
        ("rate(envelopes/second)", rate),
    ]


@click.command()
@click.option("--duration", default=3, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@number_of_runs_deco
@output_format_deco
def main(
    duration: int, runtime_mode: str, number_of_runs: int, output_format: str
) -> Any:
    """Run test."""
    parameters = {
        "Duration(seconds)": duration,
        "Runtime mode": runtime_mode,
        "Number of runs": number_of_runs,
    }

    def result_fn() -> List[Tuple[str, Any, Any, Any]]:
        return multi_run(
            int(number_of_runs),
            run,
            (duration, runtime_mode),
        )

    return print_results(output_format, parameters, result_fn)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
