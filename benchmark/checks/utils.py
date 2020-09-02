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
import os
import time
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock


from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ConnectionConfig, PublicId, SkillConfig
from aea.configurations.constants import (
    DEFAULT_LEDGER,
    DEFAULT_PRIVATE_KEY_FILE,
    DEFAULT_PROTOCOL,
    DEFAULT_SKILL,
)
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.registries.resources import Resources
from aea.skills.base import Skill, SkillContext

ROOT_DIR = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore


def wait_for_condition(condition_checker, timeout=2, error_msg="Timeout") -> None:
    """Wait for condition occures in selected timeout."""
    start_time = time.time()

    while not condition_checker():
        time.sleep(0.0001)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


def make_agent(runtime_mode="threaded") -> AEA:
    """Make AEA instance."""
    agent_name = "my_agent"
    private_key_path = os.path.join(ROOT_DIR, DEFAULT_PRIVATE_KEY_FILE)
    wallet = Wallet({DEFAULT_LEDGER: private_key_path})
    identity = Identity(agent_name, address=wallet.addresses[DEFAULT_LEDGER])
    resources = Resources()
    resources.add_skill(
        Skill.from_dir(
            str(Path(AEA_DIR, "skills", DEFAULT_SKILL.name)), agent_context=MagicMock()
        )
    )
    resources.add_protocol(
        Protocol.from_dir(str(Path(AEA_DIR, "protocols", DEFAULT_PROTOCOL.name)))
    )
    return AEA(identity, wallet, resources, runtime_mode=runtime_mode)


def make_envelope(sender: str, to: str) -> Envelope:
    """Make an envelope."""
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

    def __init__(self, *args, **kwargs):
        """Init connection."""
        super().__init__(*args, **kwargs)
        self._enabled = False
        self._count_in = 0
        self._count_out = 0

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
        self._count_in += 1

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Generate an envelope."""
        while not self._enabled:
            await asyncio.sleep(0.0001)

        envelope = make_envelope(self.address, "echo_skill")
        self._count_out += 1
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
