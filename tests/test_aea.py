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
from pathlib import Path

import pytest

from aea import AEA_DIR
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import PublicId
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer

from .common.utils import AeaTool
from .conftest import (
    CUR_PATH,
    DUMMY_SKILL_PUBLIC_ID,
    ROOT_DIR,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    _make_local_connection,
)
from .data.dummy_aea.skills.dummy.tasks import DummyTask  # type: ignore
from .data.dummy_skill.behaviours import DummyBehaviour  # type: ignore


def test_initialise_aea():
    """Tests the initialisation of the AEA."""
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    builder = AEABuilder()
    builder.set_name("my_name").add_private_key(
        FetchAICrypto.identifier, private_key_path
    )
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
    builder.add_private_key(FetchAICrypto.identifier, private_key_path)
    builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
    agent = builder.build()

    AeaTool(agent).spin_main_loop()

    behaviour = agent.resources.get_behaviour(DUMMY_SKILL_PUBLIC_ID, "dummy")
    assert behaviour.nb_act_called > 0, "Act() wasn't called"


def test_react():
    """Tests income messages."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(FetchAICrypto.identifier, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        builder.set_default_connection(PublicId.from_str("fetchai/local:0.1.0"))
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

        try:
            tool = AeaTool(agent).setup()

            agent.outbox.put(envelope)

            tool.wait_inbox().spin_main_loop()

            default_protocol_public_id = DefaultMessage.protocol_id
            dummy_skill_public_id = DUMMY_SKILL_PUBLIC_ID
            handler = agent.resources.get_handler(
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


@pytest.mark.asyncio
async def test_handle():
    """Tests handle method of an agent."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(FetchAICrypto.identifier, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        builder.set_default_connection(PublicId.from_str("fetchai/local:0.1.0"))
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        aea = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.1.0")])
        # This is a temporary workaround to feed the local node to the OEF Local connection
        # TODO remove it.
        list(aea._connections)[0]._local_node = node

        tool = AeaTool(aea)

        try:
            tool.setup().spin_main_loop()

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
            """ inbox twice cause first message is invalid. generates error message and it accepted """
            tool.wait_inbox().react_one()
            tool.wait_inbox().react_one()
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
            """ inbox twice cause first message is invalid. generates error message and it accepted """
            tool.wait_inbox().react_one()
            tool.wait_inbox().react_one()
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
            """ inbox twice cause first message is invalid. generates error message and it accepted """
            tool.wait_inbox().react_one()
            tool.wait_inbox().react_one()
            assert len(dummy_handler.handled_messages) == 3

        finally:
            aea.stop()


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
        builder.add_private_key(FetchAICrypto.identifier, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        builder.set_default_connection(PublicId.from_str("fetchai/local:0.1.0"))
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        cls.aea = builder.build(
            connection_ids=[PublicId.from_str("fetchai/local:0.1.0")]
        )
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
        cls.aea._start_setup()
        cls.aea.outbox.put(envelope)
        AeaTool(cls.aea).wait_inbox().spin_main_loop()

    def test_initialize_aea_programmatically(self):
        """Test that we can initialize an AEA programmatically."""
        dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
        dummy_behaviour_name = "dummy"
        dummy_behaviour = self.aea.resources.get_behaviour(
            dummy_skill_id, dummy_behaviour_name
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

        dummy_handler = self.aea.resources.get_handler(
            DefaultMessage.protocol_id, dummy_skill_id
        )
        dummy_handler_alt = self.aea.resources._handler_registry.fetch(
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
        cls.node.stop()


class TestInitializeAEAProgrammaticallyBuildResources:
    """Test that we can initialize the agent by building the resource object."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.node = LocalNode()
        cls.node.start()
        cls.agent_name = "MyAgent"
        cls.private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FetchAICrypto.identifier: cls.private_key_path})
        cls.ledger_apis = LedgerApis({}, FetchAICrypto.identifier)
        cls.identity = Identity(
            cls.agent_name, address=cls.wallet.addresses[FetchAICrypto.identifier]
        )
        cls.connection = _make_local_connection(cls.agent_name, cls.node)
        cls.connections = [cls.connection]
        cls.temp = tempfile.mkdtemp(prefix="test_aea_resources")
        cls.resources = Resources(cls.temp)

        cls.default_protocol = Protocol.from_dir(
            str(Path(AEA_DIR, "protocols", "default"))
        )
        cls.resources.add_protocol(cls.default_protocol)

        cls.error_skill = Skill.from_dir(str(Path(AEA_DIR, "skills", "error")))
        cls.dummy_skill = Skill.from_dir(str(Path(CUR_PATH, "data", "dummy_skill")))
        cls.resources.add_skill(cls.dummy_skill)
        cls.resources.add_skill(cls.error_skill)

        cls.aea = AEA(
            cls.identity,
            cls.connections,
            cls.wallet,
            cls.ledger_apis,
            resources=cls.resources,
        )

        cls.error_skill.skill_context.set_agent_context(cls.aea.context)
        cls.dummy_skill.skill_context.set_agent_context(cls.aea.context)

        default_protocol_id = DefaultMessage.protocol_id

        cls.expected_message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        cls.expected_message.counterparty = cls.agent_name

        tool = AeaTool(cls.aea).setup()

        cls.aea.outbox.put(
            Envelope(
                to=cls.agent_name,
                sender=cls.agent_name,
                protocol_id=default_protocol_id,
                message=DefaultSerializer().encode(cls.expected_message),
            )
        )

        tool.wait_inbox().spin_main_loop()

    def test_initialize_aea_programmatically(self):
        """Test that we can initialize an AEA programmatically."""

        dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
        dummy_behaviour_name = "dummy"
        dummy_behaviour = self.aea.resources.get_behaviour(
            dummy_skill_id, dummy_behaviour_name
        )
        assert dummy_behaviour is not None
        assert dummy_behaviour.nb_act_called > 0

        dummy_task = DummyTask()
        task_id = self.aea.task_manager.enqueue_task(dummy_task)
        async_result = self.aea.task_manager.get_task_result(task_id)
        expected_dummy_task = async_result.get(2.0)
        assert expected_dummy_task.nb_execute_called > 0

        dummy_handler_name = "dummy"
        dummy_handler = self.aea.resources._handler_registry.fetch(
            (dummy_skill_id, dummy_handler_name)
        )
        dummy_handler_alt = self.aea.resources.get_handler(
            DefaultMessage.protocol_id, dummy_skill_id
        )
        assert dummy_handler == dummy_handler_alt
        assert dummy_handler is not None
        assert len(dummy_handler.handled_messages) == 1
        assert dummy_handler.handled_messages[0] == self.expected_message

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.aea.stop()
        cls.node.stop()
        Path(cls.temp).rmdir()


class TestAddBehaviourDynamically:
    """Test that we can add a behaviour dynamically."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        wallet = Wallet({FetchAICrypto.identifier: private_key_path})
        ledger_apis = LedgerApis({}, FetchAICrypto.identifier)
        resources = Resources()
        resources.add_component(Skill.from_dir(Path(CUR_PATH, "data", "dummy_skill")))
        identity = Identity(
            agent_name, address=wallet.addresses[FetchAICrypto.identifier]
        )
        cls.agent = AEA(
            identity,
            [_make_local_connection(identity.address, LocalNode())],
            wallet,
            ledger_apis,
            resources,
        )
        for skill in resources.get_all_skills():
            skill.skill_context.set_agent_context(cls.agent.context)

        AeaTool(cls.agent).setup().spin_main_loop()

    def test_add_behaviour_dynamically(self):
        """Test the dynamic registration of a behaviour."""
        dummy_skill_id = PublicId("dummy_author", "dummy", "0.1.0")
        dummy_skill = self.agent.resources.get_skill(dummy_skill_id)
        assert dummy_skill is not None
        new_behaviour = DummyBehaviour(
            name="dummy2", skill_context=dummy_skill.skill_context
        )
        dummy_skill.skill_context.new_behaviours.put(new_behaviour)

        """
        doule loop spin!!!
        cause new behaviour added using internal message
        internal message processed after act.

        first spin adds new behaviour to skill using update(internal messages)
        second runs act for new behaviour
        """
        AeaTool(self.agent).spin_main_loop().spin_main_loop()

        assert new_behaviour.nb_act_called > 0
        assert len(self.agent.resources.get_behaviours(dummy_skill_id)) == 2

    @classmethod
    def teardown_class(cls):
        """Tear the class down."""
        cls.agent.stop()


class TestContextNamespace:
    """
    Test that the keyword arguments to AEA constructor
    can be accessible from the skill context.
    """

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        agent_name = "my_agent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        wallet = Wallet({FetchAICrypto.identifier: private_key_path})
        ledger_apis = LedgerApis({}, FetchAICrypto.identifier)
        resources = Resources()
        resources.add_component(Skill.from_dir(Path(CUR_PATH, "data", "dummy_skill")))
        identity = Identity(
            agent_name, address=wallet.addresses[FetchAICrypto.identifier]
        )
        cls.context_namespace = {"key1": 1, "key2": 2}
        cls.agent = AEA(
            identity,
            [_make_local_connection(identity.address, LocalNode())],
            wallet,
            ledger_apis,
            resources,
            **cls.context_namespace
        )
        for skill in resources.get_all_skills():
            skill.skill_context.set_agent_context(cls.agent.context)

    def test_access_context_namespace(self):
        """Test that we can access the context namespace."""
        assert self.agent.context.namespace.key1 == 1
        assert self.agent.context.namespace.key2 == 2

        for skill in self.agent.resources.get_all_skills():
            assert skill.skill_context.namespace.key1 == 1
            assert skill.skill_context.namespace.key2 == 2
