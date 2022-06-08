# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""Envelopes generation speed for Behaviour act test."""
import itertools
import struct
import time
from typing import List, Tuple, Union, cast

from aea_cli_benchmark.utils import get_mem_usage_in_mb  # noqa: I100
from aea_cli_benchmark.utils import (
    make_agent,
    make_envelope,
    make_skill,
    wait_for_condition,
)

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.registries.resources import Resources
from aea.runner import AEARunner
from aea.skills.base import Handler

from packages.fetchai.connections.local.connection import (  # noqa: E402 # pylint: disable=C0413
    LocalNode,
    OEFLocalConnection,
)
from packages.fetchai.protocols.default.message import DefaultMessage


class TestHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""
        self.count: int = 0  # pylint: disable=attribute-defined-outside-init
        self.rtt_total_time: float = (
            0.0  # pylint: disable=attribute-defined-outside-init
        )
        self.rtt_count: int = 0  # pylint: disable=attribute-defined-outside-init

        self.latency_total_time: float = (
            0.0  # pylint: disable=attribute-defined-outside-init
        )
        self.latency_count: int = 0  # pylint: disable=attribute-defined-outside-init

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, message: Message) -> None:
        """Handle incoming message."""
        self.count += 1

        if message.dialogue_reference[0] != "":
            rtt_ts, latency_ts = struct.unpack("dd", message.content)  # type: ignore
            if message.dialogue_reference[0] == self.context.agent_address:
                self.rtt_total_time += time.time() - rtt_ts
                self.rtt_count += 1

            self.latency_total_time += time.time() - latency_ts
            self.latency_count += 1

        if message.dialogue_reference[0] in ["", self.context.agent_address]:
            # create new
            response_msg = DefaultMessage(
                dialogue_reference=(self.context.agent_address, ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=struct.pack("dd", time.time(), time.time()),
            )
        else:
            # update ttfb copy rtt
            response_msg = DefaultMessage(
                dialogue_reference=message.dialogue_reference,
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=struct.pack("dd", rtt_ts, time.time()),  # type: ignore
            )

        self.context.outbox.put(make_envelope(message.to, message.sender, response_msg))


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
    skills = []

    for i in range(num_of_agents):
        resources = Resources()
        agent_name = f"agent{i}"
        identity = Identity(agent_name, address=agent_name, public_key="somekey")
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
        skill = make_skill(agent, handlers={"test": TestHandler})
        agent.resources.add_skill(skill)
        agents.append(agent)
        skills.append(skill)

    runner = AEARunner(agents, runner_mode)
    runner.start(threaded=True)

    for agent in agents:
        wait_for_condition(lambda: agent.is_running, timeout=5)
    wait_for_condition(lambda: runner.is_running, timeout=5)
    time.sleep(1)

    for agent1, agent2 in itertools.permutations(agents, 2):
        env = make_envelope(agent1.identity.address, agent2.identity.address)

        for _ in range(int(start_messages)):
            agent1.outbox.put(env)

    time.sleep(duration)

    mem_usage = get_mem_usage_in_mb()

    local_node.stop()
    runner.stop(timeout=5)

    total_messages = sum(
        [cast(TestHandler, skill.handlers["test"]).count for skill in skills]
    )
    rate = total_messages / duration

    rtt_total_time = sum(
        [cast(TestHandler, skill.handlers["test"]).rtt_total_time for skill in skills]
    )
    rtt_count = sum(
        [cast(TestHandler, skill.handlers["test"]).rtt_count for skill in skills]
    )

    if rtt_count == 0:
        rtt_count = -1

    latency_total_time = sum(
        [
            cast(TestHandler, skill.handlers["test"]).latency_total_time
            for skill in skills
        ]
    )
    latency_count = sum(
        [cast(TestHandler, skill.handlers["test"]).latency_count for skill in skills]
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
