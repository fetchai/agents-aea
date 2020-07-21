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
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from aea import AEA_DIR
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.protocols.fipa.message import FipaMessage

from tests.common.utils import run_in_thread, wait_for_condition

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
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    builder = AEABuilder()
    builder.set_name("my_name").add_private_key(DEFAULT_LEDGER, private_key_path)
    my_AEA = builder.build()
    assert my_AEA.context == my_AEA._context, "Cannot access the Agent's Context"
    assert (
        not my_AEA.context.connection_status.is_connected
    ), "AEA should not be connected."
    my_AEA.setup()
    assert my_AEA.resources is not None, "Resources must not be None after setup"
    my_AEA.resources = Resources()
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
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(DEFAULT_LEDGER, private_key_path)
    builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
    agent = builder.build()

    with run_in_thread(agent.start, timeout=20):
        wait_for_condition(
            lambda: agent._main_loop and agent._main_loop.is_running, timeout=10
        )
        behaviour = agent.resources.get_behaviour(DUMMY_SKILL_PUBLIC_ID, "dummy")
        import time

        time.sleep(1)
        wait_for_condition(lambda: behaviour.nb_act_called > 0, timeout=10)
        agent.stop()


def test_start_stop():
    """Tests the act function of the AEA."""
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(DEFAULT_LEDGER, private_key_path)
    builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
    agent = builder.build()

    with run_in_thread(agent.start, timeout=20):
        wait_for_condition(
            lambda: agent._main_loop and agent._main_loop.is_running, timeout=10
        )
        agent.stop()


def test_react():
    """Tests income messages."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        local_connection_id = PublicId.from_str("fetchai/local:0.4.0")
        builder.set_default_connection(local_connection_id)
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        agent = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.4.0")])
        # This is a temporary workaround to feed the local node to the OEF Local connection
        # TODO remove it.
        local_connection = agent.resources.get_connection(local_connection_id)
        local_connection._local_node = node

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        msg.counterparty = agent.identity.address
        envelope = Envelope(
            to=agent.identity.address,
            sender=agent.identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=msg,
        )

        with run_in_thread(agent.start, timeout=20, on_exit=agent.stop):
            wait_for_condition(
                lambda: agent._main_loop and agent._main_loop.is_running, timeout=10
            )
            agent.outbox.put(envelope)
            default_protocol_public_id = DefaultMessage.protocol_id
            dummy_skill_public_id = DUMMY_SKILL_PUBLIC_ID
            handler = agent.resources.get_handler(
                default_protocol_public_id, dummy_skill_public_id
            )
            assert handler is not None, "Handler is not set."
            wait_for_condition(
                lambda: msg in handler.handled_messages,
                timeout=10,
                error_msg="The message is not inside the handled_messages.",
            )
            agent.stop()


def test_handle():
    """Tests handle method of an agent."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        local_connection_id = PublicId.from_str("fetchai/local:0.4.0")
        builder.set_default_connection(local_connection_id)
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        aea = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.4.0")])
        # This is a temporary workaround to feed the local node to the OEF Local connection
        # TODO remove it.
        local_connection = aea.resources.get_connection(local_connection_id)
        local_connection._local_node = node

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        msg.counterparty = aea.identity.address
        envelope = Envelope(
            to=aea.identity.address,
            sender=aea.identity.address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=msg,
        )

        with run_in_thread(aea.start, timeout=5):
            wait_for_condition(
                lambda: aea._main_loop and aea._main_loop.is_running, timeout=10
            )
            dummy_skill = aea.resources.get_skill(DUMMY_SKILL_PUBLIC_ID)
            dummy_handler = dummy_skill.handlers["dummy"]

            aea.outbox.put(envelope)

            wait_for_condition(
                lambda: len(dummy_handler.handled_messages) == 1, timeout=1,
            )

            #   DECODING ERROR
            envelope = Envelope(
                to=aea.identity.address,
                sender=aea.identity.address,
                protocol_id=DefaultMessage.protocol_id,
                message=b"",
            )
            # send envelope via localnode back to agent/bypass `outbox` put consistency checks
            aea.outbox._multiplexer.put(envelope)
            """ inbox twice cause first message is invalid. generates error message and it accepted """
            wait_for_condition(
                lambda: len(dummy_handler.handled_messages) == 2, timeout=1,
            )
            #   UNSUPPORTED SKILL
            msg = FipaMessage(
                performative=FipaMessage.Performative.ACCEPT,
                message_id=1,
                dialogue_reference=(str(0), ""),
                target=0,
            )
            msg.counterparty = aea.identity.address
            envelope = Envelope(
                to=aea.identity.address,
                sender=aea.identity.address,
                protocol_id=FipaMessage.protocol_id,
                message=msg,
            )
            # send envelope via localnode back to agent
            aea.outbox.put(envelope)
            wait_for_condition(
                lambda: len(dummy_handler.handled_messages) == 3, timeout=2,
            )
            aea.stop()


def test_initialize_aea_programmatically():
    """Test that we can initialize an AEA programmatically."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, private_key_path)
        builder.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "local")
        )
        local_connection_id = PublicId.from_str("fetchai/local:0.4.0")
        builder.set_default_connection(local_connection_id)
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        aea = builder.build(connection_ids=[PublicId.from_str("fetchai/local:0.4.0")])
        local_connection = aea.resources.get_connection(local_connection_id)
        local_connection._local_node = node

        expected_message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_message.counterparty = aea.identity.address
        envelope = Envelope(
            to=aea.identity.address,
            sender=aea.identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=expected_message,
        )

        with run_in_thread(aea.start, timeout=5, on_exit=aea.stop):
            wait_for_condition(
                lambda: aea._main_loop and aea._main_loop.is_running, timeout=10
            )
            aea.outbox.put(envelope)

            dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
            dummy_behaviour_name = "dummy"
            dummy_behaviour = aea.resources.get_behaviour(
                dummy_skill_id, dummy_behaviour_name
            )
            wait_for_condition(lambda: dummy_behaviour is not None, timeout=10)
            wait_for_condition(lambda: dummy_behaviour.nb_act_called > 0, timeout=10)

            # TODO the previous code caused an error:
            #      _pickle.PicklingError: Can't pickle <class 'tasks.DummyTask'>: import of module 'tasks' failed
            dummy_task = DummyTask()
            task_id = aea.task_manager.enqueue_task(dummy_task)
            async_result = aea.task_manager.get_task_result(task_id)
            expected_dummy_task = async_result.get(10.0)
            wait_for_condition(
                lambda: expected_dummy_task.nb_execute_called > 0, timeout=10
            )

            dummy_handler = aea.resources.get_handler(
                DefaultMessage.protocol_id, dummy_skill_id
            )
            dummy_handler_alt = aea.resources._handler_registry.fetch(
                (dummy_skill_id, "dummy")
            )
            wait_for_condition(lambda: dummy_handler == dummy_handler_alt, timeout=10)
            wait_for_condition(lambda: dummy_handler is not None, timeout=10)
            wait_for_condition(
                lambda: len(dummy_handler.handled_messages) == 1, timeout=10
            )
            wait_for_condition(
                lambda: dummy_handler.handled_messages[0] == expected_message,
                timeout=10,
            )


def test_initialize_aea_programmatically_build_resources():
    """Test that we can initialize the agent by building the resource object."""
    try:
        temp = tempfile.mkdtemp(prefix="test_aea_resources")
        with LocalNode() as node:
            agent_name = "MyAgent"
            private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
            wallet = Wallet({DEFAULT_LEDGER: private_key_path})
            identity = Identity(agent_name, address=wallet.addresses[DEFAULT_LEDGER])
            connection = _make_local_connection(agent_name, node)

            resources = Resources()
            aea = AEA(
                identity,
                wallet,
                resources=resources,
                default_connection=connection.public_id,
            )

            default_protocol = Protocol.from_dir(
                str(Path(AEA_DIR, "protocols", "default"))
            )
            resources.add_protocol(default_protocol)
            resources.add_connection(connection)

            error_skill = Skill.from_dir(
                str(Path(AEA_DIR, "skills", "error")), agent_context=aea.context
            )
            dummy_skill = Skill.from_dir(
                str(Path(CUR_PATH, "data", "dummy_skill")), agent_context=aea.context
            )
            resources.add_skill(dummy_skill)
            resources.add_skill(error_skill)

            default_protocol_id = DefaultMessage.protocol_id

            expected_message = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            expected_message.counterparty = agent_name

            with run_in_thread(aea.start, timeout=5, on_exit=aea.stop):
                wait_for_condition(
                    lambda: aea._main_loop and aea._main_loop.is_running, timeout=10
                )
                aea.outbox.put(
                    Envelope(
                        to=agent_name,
                        sender=agent_name,
                        protocol_id=default_protocol_id,
                        message=expected_message,
                    )
                )

                dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
                dummy_behaviour_name = "dummy"
                dummy_behaviour = aea.resources.get_behaviour(
                    dummy_skill_id, dummy_behaviour_name
                )
                wait_for_condition(lambda: dummy_behaviour is not None, timeout=10)
                wait_for_condition(
                    lambda: dummy_behaviour.nb_act_called > 0, timeout=10
                )

                dummy_task = DummyTask()
                task_id = aea.task_manager.enqueue_task(dummy_task)
                async_result = aea.task_manager.get_task_result(task_id)
                expected_dummy_task = async_result.get(10.0)
                wait_for_condition(
                    lambda: expected_dummy_task.nb_execute_called > 0, timeout=10
                )
                dummy_handler_name = "dummy"
                dummy_handler = aea.resources._handler_registry.fetch(
                    (dummy_skill_id, dummy_handler_name)
                )
                dummy_handler_alt = aea.resources.get_handler(
                    DefaultMessage.protocol_id, dummy_skill_id
                )
                wait_for_condition(
                    lambda: dummy_handler == dummy_handler_alt, timeout=10
                )
                wait_for_condition(lambda: dummy_handler is not None, timeout=10)
                wait_for_condition(
                    lambda: len(dummy_handler.handled_messages) == 1, timeout=10
                )
                wait_for_condition(
                    lambda: dummy_handler.handled_messages[0] == expected_message,
                    timeout=10,
                )
    finally:
        Path(temp).rmdir()


def test_add_behaviour_dynamically():
    """Test that we can add a behaviour dynamically."""
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    wallet = Wallet({DEFAULT_LEDGER: private_key_path})
    resources = Resources()
    identity = Identity(agent_name, address=wallet.addresses[DEFAULT_LEDGER])
    connection = _make_local_connection(identity.address, LocalNode())
    agent = AEA(identity, wallet, resources, default_connection=connection.public_id,)
    resources.add_connection(connection)
    resources.add_component(
        Skill.from_dir(
            Path(CUR_PATH, "data", "dummy_skill"), agent_context=agent.context
        )
    )
    for skill in resources.get_all_skills():
        skill.skill_context.set_agent_context(agent.context)

    with run_in_thread(agent.start, timeout=5, on_exit=agent.stop):
        wait_for_condition(
            lambda: agent._main_loop and agent._main_loop.is_running, timeout=10
        )

        dummy_skill_id = PublicId("dummy_author", "dummy", "0.1.0")
        dummy_skill = agent.resources.get_skill(dummy_skill_id)

        wait_for_condition(lambda: dummy_skill is not None, timeout=10)

        new_behaviour = DummyBehaviour(
            name="dummy2", skill_context=dummy_skill.skill_context
        )
        dummy_skill.skill_context.new_behaviours.put(new_behaviour)

        wait_for_condition(lambda: new_behaviour.nb_act_called > 0, timeout=10)
        wait_for_condition(
            lambda: len(agent.resources.get_behaviours(dummy_skill_id)) == 2, timeout=10
        )


def test_error_handler_is_not_set():
    """Test stop on no error handler presents."""
    agent_name = "my_agent"
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    wallet = Wallet({DEFAULT_LEDGER: private_key_path})
    identity = Identity(agent_name, address=wallet.addresses[DEFAULT_LEDGER])
    resources = Resources()
    context_namespace = {"key1": 1, "key2": 2}
    agent = AEA(identity, wallet, resources, **context_namespace)

    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.counterparty = agent.identity.address
    envelope = Envelope(
        to=agent.identity.address,
        sender=agent.identity.address,
        protocol_id=DefaultMessage.protocol_id,
        message=msg,
    )

    with patch.object(agent, "stop") as mocked_stop:
        agent._handle(envelope)

    mocked_stop.assert_called()


def test_no_handlers_registered(caplog):
    """Test no handlers are registered for message processing."""
    agent_name = "MyAgent"
    builder = AEABuilder()
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    builder.set_name(agent_name)
    builder.add_private_key(DEFAULT_LEDGER, private_key_path)
    # local_connection_id = PublicId.from_str("fetchai/stub:0.4.0")
    # builder.set_default_connection(local_connection_id)
    aea = builder.build()

    with caplog.at_level(
        logging.WARNING, logger=aea._get_error_handler().context.logger.name
    ):
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        msg.counterparty = aea.identity.address
        envelope = Envelope(
            to=aea.identity.address,
            sender=aea.identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=msg,
        )
        with patch.object(aea.filter, "get_active_handlers", return_value=[]):
            aea._handle(envelope)

        assert "Cannot handle envelope: no active handler registered" in caplog.text


class TestContextNamespace:
    """Test that the keyword arguments to AEA constructor can be accessible from the skill context."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        agent_name = "my_agent"
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        wallet = Wallet({DEFAULT_LEDGER: private_key_path})
        identity = Identity(agent_name, address=wallet.addresses[DEFAULT_LEDGER])
        connection = _make_local_connection(identity.address, LocalNode())
        resources = Resources()
        cls.context_namespace = {"key1": 1, "key2": 2}
        cls.agent = AEA(identity, wallet, resources, **cls.context_namespace)

        resources.add_connection(connection)
        resources.add_component(
            Skill.from_dir(
                Path(CUR_PATH, "data", "dummy_skill"), agent_context=cls.agent.context
            )
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
