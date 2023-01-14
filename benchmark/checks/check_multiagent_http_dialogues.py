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
"""Memory usage across the time."""
import itertools
import os
import struct
import sys
import time
from typing import Any, List, Tuple, Union, cast

import click

from aea.aea import AEA
from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.protocols.base import Message, Protocol
from aea.protocols.dialogue.base import Dialogue
from aea.registries.resources import Resources
from aea.runner import AEARunner
from aea.skills.base import Handler
from benchmark.checks.utils import get_mem_usage_in_mb  # noqa: I100
from benchmark.checks.utils import PACKAGES_DIR
from benchmark.checks.utils import make_agent as base_make_agent
from benchmark.checks.utils import (
    make_skill,
    multi_run,
    number_of_runs_deco,
    output_format_deco,
    print_results,
    wait_for_condition,
)

from packages.fetchai.connections.local.connection import (  # noqa: E402 # pylint: disable=C0413
    LocalNode,
    OEFLocalConnection,
)
from packages.valory.protocols.http.dialogues import HttpDialogue, HttpDialogues
from packages.valory.protocols.http.message import HttpMessage


ROOT_PATH = os.path.join(os.path.abspath(__file__), "..", "..")
sys.path.append(ROOT_PATH)


class HttpPingPongHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""
        # pylint: disable=attribute-defined-outside-init, unused-argument
        self.count: int = 0
        self.rtt_total_time: float = 0.0
        self.rtt_count: int = 0

        self.latency_total_time: float = 0.0
        self.latency_count: int = 0

        def role(m: Message, addr: Address) -> Dialogue.Role:
            return HttpDialogue.Role.CLIENT

        self.dialogues = HttpDialogues(
            self.context.agent_address, role_from_first_message=role
        )

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, message: Message) -> None:
        """Handle incoming message."""
        self.count += 1
        message = cast(HttpMessage, message)
        dialogue = self.dialogues.update(message)
        if not dialogue:
            raise Exception("something goes wrong")
        rtt_ts, latency_ts = struct.unpack("dd", message.body)  # type: ignore
        if message.performative == HttpMessage.Performative.REQUEST:
            self.latency_total_time += time.time() - latency_ts
            self.latency_count += 1
            self.make_response(cast(HttpDialogue, dialogue), message)
        elif message.performative == HttpMessage.Performative.RESPONSE:
            self.rtt_total_time += time.time() - rtt_ts
            self.rtt_count += 1

            # got response, make another request to the same agent
            self.make_request(message.sender)

    def make_response(self, dialogue: HttpDialogue, message: HttpMessage) -> None:
        """Construct and send a response for message received."""
        response_message = dialogue.reply(
            target_message=message,
            performative=HttpMessage.Performative.RESPONSE,
            version=message.version,
            headers="",
            status_code=200,
            status_text="Success",
            body=message.body,
        )
        self.context.outbox.put_message(response_message)

    def make_request(self, recipient_addr: str) -> None:
        """Make initial http request."""
        message, _ = self.dialogues.create(
            recipient_addr,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="some url",
            headers="",
            version="",
            body=struct.pack("dd", time.time(), time.time()),
        )
        self.context.outbox.put_message(message)


def make_agent(*args: Any, **kwargs: Any) -> AEA:
    """Make agent with http protocol support."""
    aea = base_make_agent(*args, **kwargs)
    aea.resources.add_protocol(
        Protocol.from_dir(str(PACKAGES_DIR / "fetchai" / "protocols" / "http"))
    )
    return aea


def run(
    duration: int,
    runtime_mode: str,
    runner_mode: str,
    start_messages: int,
    num_of_agents: int,
) -> List[Tuple[str, Union[int, float]]]:
    """Test multiagent message exchange."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    local_node = LocalNode()
    local_node.start()
    agents = []
    skills = {}
    handler_name = "httpingpong"

    for i in range(num_of_agents):
        agent_name = f"agent{i}"
        public_key = f"public_key{i}"
        identity = Identity(agent_name, address=agent_name, public_key=public_key)
        resources = Resources()
        connection = OEFLocalConnection(
            local_node,
            configuration=ConnectionConfig(
                connection_id=OEFLocalConnection.connection_id,
            ),
            identity=identity,
            data_dir="tmp",
        )
        resources.add_connection(connection)
        agent = make_agent(
            agent_name=agent_name,
            runtime_mode=runtime_mode,
            resources=resources,
            identity=identity,
        )
        skill = make_skill(agent, handlers={handler_name: HttpPingPongHandler})
        agent.resources.add_skill(skill)
        agents.append(agent)
        skills[agent_name] = skill

    runner = AEARunner(agents, runner_mode)
    runner.start(threaded=True)
    for agent_ in agents:
        wait_for_condition(lambda a=agent_: a.is_running, timeout=5)
    wait_for_condition(lambda: runner.is_running, timeout=5)
    time.sleep(1)

    for agent1, agent2 in itertools.permutations(agents, 2):
        for _ in range(int(start_messages)):
            cast(
                HttpPingPongHandler,
                skills[agent1.identity.address].handlers[handler_name],
            ).make_request(agent2.identity.address)
    time.sleep(duration)

    mem_usage = get_mem_usage_in_mb()
    local_node.stop()
    runner.stop(timeout=5)
    total_messages = sum(
        [
            cast(HttpPingPongHandler, skill.handlers[handler_name]).count
            for skill in skills.values()
        ]
    )
    rate = total_messages / duration

    rtt_total_time = sum(
        [
            cast(HttpPingPongHandler, skill.handlers[handler_name]).rtt_total_time
            for skill in skills.values()
        ]
    )
    rtt_count = sum(
        [
            cast(HttpPingPongHandler, skill.handlers[handler_name]).rtt_count
            for skill in skills.values()
        ]
    )

    if rtt_count == 0:
        rtt_count = -1

    latency_total_time = sum(
        [
            cast(HttpPingPongHandler, skill.handlers[handler_name]).latency_total_time
            for skill in skills.values()
        ]
    )
    latency_count = sum(
        [
            cast(HttpPingPongHandler, skill.handlers[handler_name]).latency_count
            for skill in skills.values()
        ]
    )

    if latency_count == 0:
        latency_count = -1

    return [
        ("Total Messages handled", total_messages),
        ("Messages rate(envelopes/second)", rate),
        ("Mem usage(Mb)", mem_usage),
        ("RTT (ms)", rtt_total_time / rtt_count),
        ("Latency (ms)", latency_total_time / latency_count),
    ]


@click.command()
@click.option("--duration", default=1, help="Run time in seconds.")
@click.option(
    "--runtime_mode", default="async", help="Runtime mode: async or threaded."
)
@click.option("--runner_mode", default="async", help="Runtime mode: async or threaded.")
@click.option(
    "--start_messages", default=100, help="Amount of messages to prepopulate."
)
@click.option("--num_of_agents", default=2, help="Amount of agents to run.")
@number_of_runs_deco
@output_format_deco
def main(
    duration: int,
    runtime_mode: str,
    runner_mode: str,
    start_messages: int,
    num_of_agents: int,
    number_of_runs: int,
    output_format: str,
) -> Any:
    """Run test."""
    parameters = {
        "Duration(seconds)": duration,
        "Runtime mode": runtime_mode,
        "Runner mode": runner_mode,
        "Start messages": start_messages,
        "Number of agents": num_of_agents,
        "Number of runs": number_of_runs,
    }

    def result_fn() -> List[Tuple[str, Any, Any, Any]]:
        return multi_run(
            int(number_of_runs),
            run,
            (duration, runtime_mode, runner_mode, start_messages, num_of_agents),
        )

    return print_results(output_format, parameters, result_fn)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
