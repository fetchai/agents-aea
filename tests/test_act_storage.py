# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains tests behaviour storage access."""
import json
import os
from typing import List, Set

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import ComponentType, SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.mail.base import Envelope
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import (
    BasicDialoguesStorage,
    Dialogue,
    DialogueLabel,
    PersistDialoguesStorage,
)
from aea.skills.base import Handler, Skill, SkillContext
from aea.skills.behaviours import TickerBehaviour
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo import PUBLIC_ID

from tests.common.utils import wait_for_condition
from tests.conftest import ROOT_DIR


class TBehaviour(TickerBehaviour):
    """Simple behaviour to count how many acts were called."""

    OBJ_ID = "some"
    OBJ_BODY = {"data": 12}
    COL_NAME = "test"

    def setup(self) -> None:
        """Set up behaviour."""
        self.counter = 0

    def act(self) -> None:
        """Make an action."""
        if self.context.storage and self.context.storage.is_connected:
            col = self.context.storage.get_sync_collection(self.COL_NAME)
            col.put(self.OBJ_ID, self.OBJ_BODY)
        self.counter += 1


class THandler(Handler):
    """Simple behaviour to count how many acts were called."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    OBJ_ID = "some"
    OBJ_BODY = {"data": 12}
    COL_NAME = "test"

    def setup(self) -> None:
        """Set up behaviour."""
        self.counter = 0

    def teardown(self) -> None:
        """Tear down handler."""

    def handle(self, *args, **kwargs) -> None:
        """Handle an evelope."""
        if self.context.storage and self.context.storage.is_connected:
            col = self.context.storage.get_sync_collection(self.COL_NAME)
            col.put(self.OBJ_ID, self.OBJ_BODY)

        self.counter += 1


def test_storage_access_from_behaviour():
    """Test storage access from behaviour component."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER)

    skill_context = SkillContext()
    behaviour = TBehaviour(name="behaviour", skill_context=skill_context)
    test_skill = Skill(
        SkillConfig(name="test_skill", author="fetchai"),
        skill_context=skill_context,
        handlers={},
        behaviours={"behaviour": behaviour},
    )

    builder.add_component_instance(test_skill)
    builder.set_storage_uri("sqlite://:memory:")
    aea = builder.build()
    skill_context.set_agent_context(aea.context)

    aea.runtime._threaded = True
    aea.runtime.start()

    try:
        wait_for_condition(lambda: aea.is_running, timeout=10)
        wait_for_condition(lambda: behaviour.counter > 0, timeout=10)

        col = skill_context.storage.get_sync_collection(behaviour.COL_NAME)
        assert col.get(behaviour.OBJ_ID) == behaviour.OBJ_BODY
    finally:
        aea.runtime.stop()
        aea.runtime.wait_completed(sync=True, timeout=10)


def test_storage_access_from_handler():
    """Test storage access from handler component."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER)
    protocol = os.path.join(ROOT_DIR, "packages", "fetchai", "protocols", "default")
    builder.add_component(ComponentType.PROTOCOL, protocol)

    skill_context = SkillContext()
    handler = THandler(name="behaviour", skill_context=skill_context)
    test_skill = Skill(
        SkillConfig(name="test_skill", author="fetchai"),
        skill_context=skill_context,
        handlers={"handler": handler},
        behaviours={},
    )

    builder.add_component_instance(test_skill)
    builder.set_storage_uri("sqlite://:memory:")
    aea = builder.build()
    skill_context.set_agent_context(aea.context)

    aea.runtime._threaded = True
    aea.runtime.start()

    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.to = aea.identity.address
    msg.sender = aea.identity.address
    envelope = Envelope(
        to=msg.to,
        sender=msg.sender,
        message=msg,
    )
    try:
        wait_for_condition(lambda: aea.is_running, timeout=10)

        aea.runtime.multiplexer.in_queue.put(envelope)

        wait_for_condition(lambda: handler.counter > 0, timeout=10)

        col = skill_context.storage.get_sync_collection(handler.COL_NAME)
        assert col.get(handler.OBJ_ID) == handler.OBJ_BODY
    finally:
        aea.runtime.stop()
        aea.runtime.wait_completed(sync=True, timeout=10)


def _get_labels(dialogues: List[Dialogue]) -> Set[DialogueLabel]:
    return set([i.dialogue_label for i in dialogues])


def _storage_all_dialogues_labels(storage: BasicDialoguesStorage) -> Set[DialogueLabel]:
    return _get_labels(
        storage.dialogues_in_active_state + storage.dialogues_in_terminal_state
    )


class TestDialogueModelSaveLoad(AEATestCaseEmpty):
    """Test dialogues sved and loaded on agent restart."""

    def setup(self):
        """Set up the test case."""
        self.add_item("skill", "fetchai/echo:latest", local=True)
        pkey_file = os.path.join(self._get_cwd(), "privkey")
        self.generate_private_key("fetchai", pkey_file)
        self.add_private_key("fetchai", pkey_file, False)
        self.add_private_key("fetchai", pkey_file, True)
        self.set_config("agent.default_ledger", FetchAICrypto.identifier)
        self.set_config(
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            type_="list",
        )

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        self.dialogues = DefaultDialogues(
            self_address="another_agent",
            role_from_first_message=role_from_first_message,
        )

    def _build_aea(self) -> AEA:
        """Build an AEA."""
        builder = AEABuilder.from_aea_project(self._get_cwd())
        builder.set_storage_uri("sqlite://some_file.db")
        aea = builder.build()
        aea.runtime._threaded = True
        return aea

    def test_dialogues_dumped_and_restored_properly(self):
        """Test dialogues restored during restart of agent."""
        aea = self._build_aea()
        aea.runtime.start()
        try:
            wait_for_condition(lambda: aea.is_running, timeout=10)
            echo_skill = aea.resources.get_skill(PUBLIC_ID)
            assert (
                not echo_skill.skill_context.default_dialogues._dialogues_storage._dialogues_by_dialogue_label
            )
            msg, dialogue = self.dialogues.create(
                aea.name,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            envelope = Envelope(
                to=msg.to,
                sender=msg.sender,
                message=msg,
            )
            aea.runtime.multiplexer.in_queue.put(envelope)

            dialogue_storage: PersistDialoguesStorage = (
                echo_skill.skill_context.default_dialogues._dialogues_storage
            )
            wait_for_condition(
                lambda: _storage_all_dialogues_labels(dialogue_storage),
                timeout=3,
            )
            dialogues_for_check = _storage_all_dialogues_labels(dialogue_storage)
        finally:
            aea.runtime.stop()
            aea.runtime.wait_completed(sync=True, timeout=10)

        aea = self._build_aea()
        aea.runtime.start()
        try:
            wait_for_condition(lambda: aea.is_running, timeout=10)
            echo_skill = aea.resources.get_skill(PUBLIC_ID)

            dialogue_storage: PersistDialoguesStorage = (
                echo_skill.skill_context.default_dialogues._dialogues_storage
            )
            wait_for_condition(
                lambda: _storage_all_dialogues_labels(dialogue_storage),
                timeout=3,
            )
            assert (
                _storage_all_dialogues_labels(dialogue_storage) == dialogues_for_check
            )
        finally:
            aea.runtime.stop()
            aea.runtime.wait_completed(sync=True, timeout=10)


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
