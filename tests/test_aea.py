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
"""This module contains the tests for aea/aea.py."""

import os
import tempfile
import time
from pathlib import Path
from threading import Thread
from typing import cast

import pytest

import yaml

from aea import AEA_DIR
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import ProtocolConfig, PublicId, ConnectionConfig, ComponentType
from aea.configurations.components import Component
from aea.connections.base import Connection
from aea.connections.stub.connection import StubConnection
from aea.crypto.fetchai import FETCHAI
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.registries.base import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer

from .conftest import (
    CUR_PATH,
    DUMMY_SKILL_PUBLIC_ID,
    LOCAL_CONNECTION_PUBLIC_ID,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    ROOT_DIR)
from .data.dummy_aea.skills.dummy.tasks import DummyTask  # type: ignore
from .data.dummy_skill.behaviours import DummyBehaviour  # type: ignore


def test_initialise_aea():
    """Tests the initialisation of the AEA."""
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    builder = AEABuilder()
    builder.set_name("my_name").add_private_key(FETCHAI, private_key_path)
    my_AEA = builder.build()
    assert my_AEA.context == my_AEA._context, "Cannot access the Agent's Context"
    assert (
        not my_AEA.context.connection_status.is_connected
    ), "AEA should not be connected."
    my_AEA.setup()
    assert my_AEA.resources is not None, "Resources must not be None after setup"
    my_AEA.resources = Resources(str(Path(CUR_PATH, "aea")))
    assert my_AEA.resources is not None, "Resources must not be None after set"
    assert (
        my_AEA.context.shared_state is not None
    ), "Shared state must not be None after set"
    assert my_AEA.context.task_manager is not None
    assert my_AEA.context.identity is not None, "Identity must not be None after set."
    my_AEA.stop()


def test_act():
    """Tests the act function of the AEA."""
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)
    builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
    agent = builder.build()
    t = Thread(target=agent.start)
    try:
        t.start()
        time.sleep(1.0)

        behaviour = agent.resources.behaviour_registry.fetch(
            (DUMMY_SKILL_PUBLIC_ID, "dummy")
        )
        assert behaviour.nb_act_called > 0, "Act() wasn't called"
    finally:
        agent.stop()
        t.join()


def test_react():
    """Tests income messages."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(FETCHAI, private_key_path)
        builder.add_connection(Path(ROOT_DIR, "packages", "fetchai", "connections", "local"))
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        agent = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.1.0")])
        # This is a temporary workaround to feed the local node to the OEF Local connection
        # TODO remove it.
        list(agent._connections)[0]._local_node = node

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        msg.counterparty = agent.identity.address
        message_bytes = DefaultSerializer().encode(msg)

        envelope = Envelope(
            to=agent.identity.address,
            sender=agent.identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=message_bytes,
        )

        t = Thread(target=agent.start)
        try:
            t.start()
            time.sleep(1.0)
            agent.outbox.put(envelope)
            time.sleep(2.0)
            default_protocol_public_id = DefaultMessage.protocol_id
            dummy_skill_public_id = DUMMY_SKILL_PUBLIC_ID
            handler = agent.resources.handler_registry.fetch_by_protocol_and_skill(
                default_protocol_public_id, dummy_skill_public_id
            )
            assert handler is not None, "Handler is not set."
            assert (
                msg in handler.handled_messages
            ), "The message is not inside the handled_messages."
        except Exception:
            raise
        finally:
            agent.stop()
            t.join()


@pytest.mark.asyncio
async def test_handle():
    """Tests handle method of an agent."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(FETCHAI, private_key_path)
        builder.add_connection(Path(ROOT_DIR, "packages", "fetchai", "connections", "local"))
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        aea = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.1.0")])
        # This is a temporary workaround to feed the local node to the OEF Local connection
        # TODO remove it.
        list(aea._connections)[0]._local_node = node
        t = Thread(target=aea.start)

        try:
            t.start()
            time.sleep(2.0)
            dummy_skill = aea.resources.get_skill(DUMMY_SKILL_PUBLIC_ID)
            dummy_handler = dummy_skill.handlers["dummy"]

            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            message_bytes = DefaultSerializer().encode(msg)

            envelope = Envelope(
                to=aea.identity.address,
                sender=aea.identity.address,
                protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
                message=message_bytes,
            )
            # send envelope via localnode back to agent
            aea.outbox.put(envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 1

            #   DECODING ERROR
            envelope = Envelope(
                to=aea.identity.address,
                sender=aea.identity.address,
                protocol_id=DefaultMessage.protocol_id,
                message=b"",
            )
            # send envelope via localnode back to agent
            aea.outbox.put(envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 2

            #   UNSUPPORTED SKILL
            msg = FipaSerializer().encode(
                FipaMessage(
                    performative=FipaMessage.Performative.ACCEPT,
                    message_id=1,
                    dialogue_reference=(str(0), ""),
                    target=0,
                )
            )
            envelope = Envelope(
                to=aea.identity.address,
                sender=aea.identity.address,
                protocol_id=FipaMessage.protocol_id,
                message=msg,
            )
            # send envelope via localnode back to agent
            aea.outbox.put(envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 3

        finally:
            aea.stop()
            t.join()


class TestInitializeAEAProgrammaticallyFromResourcesDir:
    """Test that we can initialize the agent by providing the resource object loaded from dir."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.node = LocalNode()
        cls.node.start()
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(FETCHAI, private_key_path)
        builder.add_connection(Path(ROOT_DIR, "packages", "fetchai", "connections", "local"))
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        cls.aea = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.1.0")])
        list(cls.aea._connections)[0]._local_node = cls.node

        cls.expected_message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        cls.expected_message.counterparty = cls.aea.identity.address
        envelope = Envelope(
            to=cls.aea.identity.address,
            sender=cls.aea.identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(cls.expected_message),
        )

        cls.t = Thread(target=cls.aea.start)
        cls.t.start()

        time.sleep(0.5)
        cls.aea.outbox.put(envelope)
        time.sleep(0.5)

    def test_initialize_aea_programmatically(self):
        """Test that we can initialize an AEA programmatically."""
        dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
        dummy_behaviour_name = "dummy"
        dummy_behaviour = self.aea.resources.behaviour_registry.fetch(
            (dummy_skill_id, dummy_behaviour_name)
        )
        assert dummy_behaviour is not None
        assert dummy_behaviour.nb_act_called > 0

        # TODO the previous code caused an error:
        #      _pickle.PicklingError: Can't pickle <class 'tasks.DummyTask'>: import of module 'tasks' failed
        dummy_task = DummyTask()
        task_id = self.aea.task_manager.enqueue_task(dummy_task)
        async_result = self.aea.task_manager.get_task_result(task_id)
        expected_dummy_task = async_result.get(2.0)
        assert expected_dummy_task.nb_execute_called > 0

        dummy_handler = self.aea.resources.handler_registry.fetch_by_protocol_and_skill(
            DefaultMessage.protocol_id, dummy_skill_id
        )
        dummy_handler_alt = self.aea.resources.handler_registry.fetch(
            (dummy_skill_id, "dummy")
        )
        assert dummy_handler == dummy_handler_alt
        assert dummy_handler is not None
        assert len(dummy_handler.handled_messages) == 1
        assert dummy_handler.handled_messages[0] == self.expected_message

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.aea.stop()
        cls.t.join()
        cls.node.stop()


