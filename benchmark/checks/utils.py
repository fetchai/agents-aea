# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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
"""Performance checks utils."""
import asyncio
import inspect
import multiprocessing
import os
import time
from multiprocessing import Pool
from pathlib import Path
from statistics import mean, stdev, variance
from typing import Any, Callable, List, Optional, Tuple
from unittest.mock import MagicMock

import click
import psutil  # type: ignore

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ConnectionConfig, PublicId, SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PROTOCOL, DEFAULT_SKILL
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill, SkillContext

from packages.fetchai.protocols.default.message import DefaultMessage


ROOT_DIR = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore
PACKAGES_DIR = Path(AEA_DIR, "..", "packages")


def wait_for_condition(condition_checker, timeout=2, error_msg="Timeout") -> None:
    """Wait for condition occures in selected timeout."""
    start_time = time.time()

    while not condition_checker():
        time.sleep(0.0001)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


def make_agent(agent_name="my_agent", runtime_mode="threaded") -> AEA:
    """Make AEA instance."""
    wallet = Wallet({DEFAULT_LEDGER: None})
    identity = Identity(agent_name, address=agent_name)
    resources = Resources()
    agent_context = MagicMock()
    agent_context.agent_name = agent_name
    agent_context.agent_address = agent_name

    resources.add_skill(
        Skill.from_dir(
            str(PACKAGES_DIR / "fetchai" / "skills" / DEFAULT_SKILL.name),
            agent_context=agent_context,
        )
    )
    resources.add_protocol(
        Protocol.from_dir(
            str(PACKAGES_DIR / "fetchai" / "protocols" / DEFAULT_PROTOCOL.name)
        )
    )
    return AEA(identity, wallet, resources, runtime_mode=runtime_mode)


def make_envelope(
    sender: str, to: str, message: Optional[DefaultMessage] = None
) -> Envelope:
    """Make an envelope."""
    if message is None:
        message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"content",
        )
    message.sender = sender
    message.to = to
    return Envelope(
        to=to, sender=sender, protocol_id=DefaultMessage.protocol_id, message=message,
    )


class GeneratorConnection(Connection):
    """Generates messages and count."""

    connection_id = PublicId("fetchai", "generator", "0.1.0")
    ENABLED_WAIT_SLEEP = 0.00001

    def __init__(self, *args, **kwargs):
        """Init connection."""
        super().__init__(*args, **kwargs)
        self._enabled = False
        self.count_in = 0
        self.count_out = 0

    def enable(self) -> None:
        """Enable message generation."""
        self._enabled = True

    def disable(self) -> None:
        """Disable message generation."""
        self._enabled = False

    async def connect(self) -> None:
        """Connect connection."""
        self._state.set(ConnectionStates.connected)

    async def disconnect(self):
        """Disonnect connection."""
        self._state.set(ConnectionStates.disconnected)

    async def send(self, envelope: "Envelope") -> None:
        """Handle incoming envelope."""
        self.count_in += 1

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Generate an envelope."""
        while not self._enabled:
            await asyncio.sleep(self.ENABLED_WAIT_SLEEP)

        envelope = make_envelope(self.address, "echo_skill")
        self.count_out += 1
        return envelope

    @classmethod
    def make(cls):
        """Construct connection instance."""
        configuration = ConnectionConfig(connection_id=cls.connection_id,)
        test_connection = cls(
            configuration=configuration, identity=Identity("name", "address")
        )
        return test_connection


class SyncedGeneratorConnection(GeneratorConnection):
    """Synchronized message generator."""

    def __init__(self, *args, **kwargs):
        """Init connection."""
        super().__init__(*args, **kwargs)
        self._condition = None

    async def connect(self):
        """Connect connection."""
        await super().connect()
        self._condition = asyncio.Event()
        self._condition.set()

    async def send(self, envelope: "Envelope") -> None:
        """Handle incoming envelope."""
        await super().send(envelope)
        self._condition.set()

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Generate an envelope."""
        await self._condition.wait()
        self._condition.clear()
        return await super().receive(*args, **kwargs)


def make_skill(agent, handlers=None, behaviours=None) -> Skill:
    """Construct skill instance for agent from behaviours."""
    handlers = handlers or {}
    behaviours = behaviours or {}
    config = SkillConfig(name="test_skill", author="fetchai")
    skill_context = SkillContext(agent.context)
    skill = Skill(configuration=config, skill_context=skill_context)
    for name, handler_cls in handlers.items():
        handler = handler_cls(name=name, skill_context=skill_context)
        skill.handlers.update({handler.name: handler})

    for name, behaviour_cls in behaviours.items():
        behaviour = behaviour_cls(name=name, skill_context=skill_context)
        skill.behaviours.update({behaviour.name: behaviour})
    return skill


def get_mem_usage_in_mb() -> float:
    """Get memory usage of the current process in megabytes."""
    return 1.0 * psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2


def print_results(result: List[Tuple[str, Any, Any, Any]]) -> None:
    """Print result for multi_run response."""
    click.echo("\nResults:")
    for msg, *values_set in result:
        mean_, stdev_, variance_ = map(lambda x: round(x, 6), values_set)
        click.echo(f" * {msg}: mean: {mean_} stdev: {stdev_} variance: {variance_} ")
    click.echo("Test finished.")


def multi_run(
    num_runs: int, fn: Callable, args: Tuple
) -> List[Tuple[str, Any, Any, Any]]:
    """
    Perform multiple test runs.

    :param num_runs: host many times to run
    :param fn: callable  that returns list of tuples with result
    :param args: args to pass to callable

    :return: list of tuples of results
    """
    multiprocessing.set_start_method("spawn")
    results = []
    for _ in range(num_runs):
        p = Pool(1)
        results.append(p.apply(fn, tuple(args)))
        p.terminate()
        del p

    mean_values = map(mean, zip(*(map(lambda x: x[1], i) for i in results)))
    stdev_values = map(stdev, zip(*(map(lambda x: x[1], i) for i in results)))
    variance_values = map(variance, zip(*(map(lambda x: x[1], i) for i in results)))
    return list(
        zip(map(lambda x: x[0], results[0]), mean_values, stdev_values, variance_values)
    )
