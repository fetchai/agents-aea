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
"""Performance checks utils."""
import asyncio
import inspect
import multiprocessing
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from statistics import mean, stdev, variance
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from unittest.mock import MagicMock

import click
import psutil  # type: ignore

from aea.aea import AEA
from aea.cli.add import copy_package_directory
from aea.cli.utils.package_utils import get_package_path
from aea.configurations.base import ConnectionConfig, PublicId, SkillConfig
from aea.configurations.constants import (
    AEA_DIR,
    DEFAULT_LEDGER,
    PACKAGES,
    PROTOCOLS,
    SIGNING_PROTOCOL,
    SKILLS,
    _FETCHAI_IDENTIFIER,
)
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message, Protocol
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler, Skill, SkillContext


ERROR_SKILL_NAME = "error"
ROOT_DIR = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore
PACKAGES_DIR = Path(".", PACKAGES)


output_format_deco = click.option(
    "--output_format",
    type=click.Choice(["text"]),
    default="text",
    help="Output format",
    show_default=True,
)
number_of_runs_deco = click.option(
    "--number_of_runs", default=2, help="How many times run test.", show_default=True
)
runtime_mode_deco = click.option(
    "--runtime_mode",
    type=click.Choice(["async", "threaded"]),
    default="async",
    help="Runtime mode: async or threaded.",
    show_default=True,
)


def wait_for_condition(
    condition_checker: Callable, timeout: int = 2, error_msg: str = "Timeout"
) -> None:
    """Wait for condition occurs in selected timeout."""
    start_time = time.time()

    while not condition_checker():
        time.sleep(0.0001)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


def make_agent(
    agent_name: str = "my_agent",
    runtime_mode: str = "threaded",
    resources: Optional[Resources] = None,
    wallet: Optional[Wallet] = None,
    identity: Optional[Identity] = None,
    packages_dir=PACKAGES_DIR,
    default_ledger=None,
) -> AEA:
    """Make AEA instance."""
    if not wallet:
        wallet = Wallet({DEFAULT_LEDGER: None})

    if wallet and not identity:
        identity = make_identity_from_wallet(
            agent_name, wallet, default_ledger or list(wallet.addresses.keys())[0]
        )

    identity = identity or Identity(
        agent_name, address=agent_name, public_key="somekey"
    )
    resources = resources or Resources()
    datadir = os.getcwd()
    agent_context = MagicMock()
    agent_context.agent_name = agent_name
    agent_context.agent_address = agent_name

    resources.add_skill(
        Skill.from_dir(
            str(Path(packages_dir) / _FETCHAI_IDENTIFIER / SKILLS / ERROR_SKILL_NAME),
            agent_context=agent_context,
        )
    )
    resources.add_protocol(
        Protocol.from_dir(
            str(
                Path(packages_dir)
                / "open_aea"
                / PROTOCOLS
                / PublicId.from_str(SIGNING_PROTOCOL).name
            )
        )
    )
    return AEA(identity, wallet, resources, datadir, runtime_mode=runtime_mode)


def make_envelope(sender: str, to: str, message: Optional[Message] = None) -> Envelope:
    """Make an envelope."""
    from packages.fetchai.protocols.default.message import (  # noqa: E402  # pylint: disable=import-outside-toplevel,unused-import
        DefaultMessage,
    )

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
        to=to,
        sender=sender,
        message=message,
    )


class GeneratorConnection(Connection):
    """Generates messages and count."""

    connection_id = PublicId("fetchai", "generator", "0.1.0")
    ENABLED_WAIT_SLEEP = 0.00001

    def __init__(self, *args: Any, **kwargs: Any):
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

    async def disconnect(self) -> None:
        """Disconnect connection."""
        self._state.set(ConnectionStates.disconnected)

    async def send(self, envelope: "Envelope") -> None:
        """Handle incoming envelope."""
        self.count_in += 1

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """Generate an envelope."""
        while not self._enabled:
            await asyncio.sleep(self.ENABLED_WAIT_SLEEP)

        envelope = make_envelope(self.address, "echo_skill")
        self.count_out += 1
        return envelope

    @classmethod
    def make(
        cls,
    ) -> "GeneratorConnection":
        """Construct connection instance."""
        configuration = ConnectionConfig(
            connection_id=cls.connection_id,
        )
        test_connection = cls(
            configuration=configuration,
            identity=Identity("name", "address", "pubkey"),
            data_dir=".tmp",
        )
        return test_connection


class SyncedGeneratorConnection(GeneratorConnection):
    """Synchronized message generator."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init connection."""
        super().__init__(*args, **kwargs)
        self._condition: Optional[asyncio.Event] = None

    @property
    def condition(self) -> asyncio.Event:
        """Get condition."""
        if self._condition is None:
            raise ValueError("Event not set.")
        return self._condition

    async def connect(self) -> None:
        """Connect connection."""
        await super().connect()
        self._condition = asyncio.Event()
        self.condition.set()

    async def send(self, envelope: "Envelope") -> None:
        """Handle incoming envelope."""
        await super().send(envelope)
        self.condition.set()

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """Generate an envelope."""
        await self.condition.wait()
        self.condition.clear()
        return await super().receive(*args, **kwargs)


def make_skill(
    agent: AEA,
    handlers: Optional[Dict[str, Type[Handler]]] = None,
    behaviours: Optional[Dict[str, Type[Behaviour]]] = None,
    skill_id: Optional[PublicId] = None,
) -> Skill:
    """Construct skill instance for agent from behaviours."""
    skill_id = skill_id or PublicId.from_str("fetchai/benchmark:0.1.0")
    handlers = handlers or {}
    behaviours = behaviours or {}
    config = SkillConfig(
        name=skill_id.name, author=skill_id.author, version=skill_id.version
    )
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
    return 1.0 * psutil.Process(os.getpid()).memory_info().rss / 1024**2


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
    context = multiprocessing.get_context("spawn")
    results = []
    for _ in range(num_runs):
        p = context.Pool(1)
        results.append(p.apply(fn, tuple(args)))
        p.terminate()
        del p

    data = list(zip(*(map(lambda x: x[1], i) for i in results)))
    mean_values = map(mean, data)
    stdev_values = map(stdev, data)
    variance_values = map(variance, data)
    return list(
        zip(map(lambda x: x[0], results[0]), mean_values, stdev_values, variance_values)
    )


def print_results(
    output_format: str,
    parameters: Dict,
    result_fn: Callable[..., List[Tuple[str, Any, Any, Any]]],
) -> Any:
    """Print result for multi_run response."""
    if output_format != "text":
        raise ValueError(f"Bad output format {output_format}")

    click.echo("Start test with options:")
    for name, value in parameters.items():
        click.echo(f"* {name}: {value}")
    click.echo("\nResults:")
    for msg, *values_set in result_fn():
        mean_, stdev_, variance_ = map(lambda x: round(x, 6), values_set)
        click.echo(f" * {msg}: mean: {mean_} stdev: {stdev_} variance: {variance_} ")
    click.echo("Test finished.")


def _make_init_py(path: str) -> None:
    """Make init.py file in a directory."""
    (Path(path) / "__init__.py").write_text("")


def make_identity_from_wallet(name, wallet, default_ledger):
    """Make indentity for ledger id and wallet specified."""
    return Identity(
        name,
        address=wallet.addresses[default_ledger],
        public_key=wallet.public_keys[default_ledger],
        default_address_key=default_ledger,
    )


@contextmanager
def with_packages(packages: List[Tuple[str, str]], packages_dir: Optional[Path] = None):
    """Download and install packages context manager."""

    if packages_dir is None:
        packages_dir = AEA_DIR.parent / PACKAGES

    with TemporaryDirectory() as dir_name:
        temp_packages_dir = Path(dir_name) / PACKAGES
        os.mkdir(temp_packages_dir)
        _make_init_py(dir_name)
        _make_init_py(temp_packages_dir)

        for package_type, package in packages:
            public_id = PublicId.from_str(package)
            dest = get_package_path(
                str(dir_name), package_type, public_id, vendor_dirname=PACKAGES
            )
            source = (
                packages_dir / public_id.author / f"{package_type}s" / public_id.name
            )
            copy_package_directory(source, dest)
            _make_init_py(temp_packages_dir / public_id.author)
            _make_init_py(temp_packages_dir / public_id.author / f"{package_type}s")

        sys.path.append(dir_name)
        yield
        sys.path.remove(dir_name)
        for k in list(sys.modules.keys()):
            if k.startswith(PACKAGES):
                sys.modules.pop(k)
