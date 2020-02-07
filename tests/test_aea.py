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

import pytest

import yaml

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ProtocolConfig, PublicId
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
from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer

from .conftest import (
    CUR_PATH,
    DUMMY_SKILL_PUBLIC_ID,
    LOCAL_CONNECTION_PUBLIC_ID,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
)
from .data.dummy_aea.skills.dummy.tasks import DummyTask  # type: ignore
from .data.dummy_skill.behaviours import DummyBehaviour  # type: ignore


def test_initialise_aea():
    """Tests the initialisation of the AEA."""
    node = LocalNode()
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    wallet = Wallet({FETCHAI: private_key_path})
    identity = Identity("my_name", address=wallet.addresses[FETCHAI])
    connections1 = [
        OEFLocalConnection(
            identity.address, node, connection_id=OEFLocalConnection.connection_id
        )
    ]
    ledger_apis = LedgerApis({}, FETCHAI)
    my_AEA = AEA(
        identity,
        connections1,
        wallet,
        ledger_apis,
        resources=Resources(str(Path(CUR_PATH, "aea"))),
    )
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
    assert my_AEA.context.identity is not None, "Identity must not be None after set."
    my_AEA.stop()


def test_act():
    """Tests the act function of the AEA."""
    with LocalNode() as node:
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        wallet = Wallet({FETCHAI: private_key_path})
        identity = Identity(agent_name, address=wallet.addresses[FETCHAI])
        ledger_apis = LedgerApis({}, FETCHAI)
        connections = [
            OEFLocalConnection(
                identity.address, node, connection_id=LOCAL_CONNECTION_PUBLIC_ID
            )
        ]
        resources = Resources(str(Path(CUR_PATH, "data", "dummy_aea")))

        agent = AEA(
            identity, connections, wallet, ledger_apis, resources, is_programmatic=False
        )
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
        wallet = Wallet({FETCHAI: private_key_path})
        identity = Identity(agent_name, address=wallet.addresses[FETCHAI])
        ledger_apis = LedgerApis({}, FETCHAI)
        connection = OEFLocalConnection(
            identity.address, node, connection_id=LOCAL_CONNECTION_PUBLIC_ID
        )
        connections = [connection]
        resources = Resources(str(Path(CUR_PATH, "data", "dummy_aea")))

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg.counterparty = identity.address
        message_bytes = DefaultSerializer().encode(msg)

        envelope = Envelope(
            to=identity.address,
            sender=identity.address,
            protocol_id=DefaultMessage.protocol_id,
            message=message_bytes,
        )

        agent = AEA(
            identity, connections, wallet, ledger_apis, resources, is_programmatic=False
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
        wallet = Wallet({FETCHAI: private_key_path})
        ledger_apis = LedgerApis({}, FETCHAI)
        identity = Identity(agent_name, address=wallet.addresses[FETCHAI])
        connection = OEFLocalConnection(
            identity.address, node, connection_id=DUMMY_SKILL_PUBLIC_ID
        )
        connections = [connection]
        resources = Resources(str(Path(CUR_PATH, "data", "dummy_aea")))

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg.counterparty = agent_name
        message_bytes = DefaultSerializer().encode(msg)

        envelope = Envelope(
            to=identity.address,
            sender=identity.address,
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )

        agent = AEA(
            identity, connections, wallet, ledger_apis, resources, is_programmatic=False
        )
        t = Thread(target=agent.start)
        try:
            t.start()
            time.sleep(2.0)
            dummy_skill = agent.resources.get_skill(DUMMY_SKILL_PUBLIC_ID)
            dummy_handler = dummy_skill.handlers["dummy"]

            expected_envelope = envelope
            agent.outbox.put(expected_envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 1

            #   DECODING ERROR
            msg = "hello".encode("utf-8")
            envelope = Envelope(
                to=identity.address,
                sender=identity.address,
                protocol_id=DefaultMessage.protocol_id,
                message=msg,
            )
            expected_envelope = envelope
            agent.outbox.put(expected_envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 2

            #   UNSUPPORTED SKILL
            msg = FIPASerializer().encode(
                FIPAMessage(
                    performative=FIPAMessage.Performative.ACCEPT,
                    message_id=0,
                    dialogue_reference=(str(0), ""),
                    target=1,
                )
            )
            envelope = Envelope(
                to=identity.address,
                sender=identity.address,
                protocol_id=FIPAMessage.protocol_id,
                message=msg,
            )
            expected_envelope = envelope
            agent.outbox.put(expected_envelope)
            time.sleep(2.0)
            assert len(dummy_handler.handled_messages) == 3

        finally:
            agent.stop()
            t.join()


class TestInitializeAEAProgrammaticallyFromResourcesDir:
    """Test that we can initialize the agent by providing the resource object loaded from dir."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.node = LocalNode()
        cls.node.start()
        cls.agent_name = "MyAgent"
        cls.private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FETCHAI: cls.private_key_path})
        cls.ledger_apis = LedgerApis({}, FETCHAI)
        cls.identity = Identity(cls.agent_name, address=cls.wallet.addresses[FETCHAI])
        cls.connection = OEFLocalConnection(
            cls.agent_name, cls.node, connection_id=LOCAL_CONNECTION_PUBLIC_ID,
        )
        cls.connections = [cls.connection]

        cls.resources = Resources(os.path.join(CUR_PATH, "data", "dummy_aea"))
        cls.aea = AEA(
            cls.identity,
            cls.connections,
            cls.wallet,
            cls.ledger_apis,
            cls.resources,
            is_programmatic=False,
        )

        cls.expected_message = DefaultMessage(
            type=DefaultMessage.Type.BYTES, content=b"hello"
        )
        cls.expected_message.counterparty = cls.agent_name
        envelope = Envelope(
            to=cls.agent_name,
            sender=cls.agent_name,
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


class TestInitializeAEAProgrammaticallyBuildResources:
    """Test that we can initialize the agent by building the resource object."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.node = LocalNode()
        cls.node.start()
        cls.agent_name = "MyAgent"
        cls.private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FETCHAI: cls.private_key_path})
        cls.ledger_apis = LedgerApis({}, FETCHAI)
        cls.identity = Identity(cls.agent_name, address=cls.wallet.addresses[FETCHAI])
        cls.connection = OEFLocalConnection(
            cls.agent_name, cls.node, connection_id=LOCAL_CONNECTION_PUBLIC_ID
        )
        cls.connections = [cls.connection]

        cls.temp = tempfile.mkdtemp(prefix="test_aea_resources")
        cls.resources = Resources(cls.temp)
        cls.aea = AEA(
            cls.identity,
            cls.connections,
            cls.wallet,
            cls.ledger_apis,
            resources=cls.resources,
        )

        default_protocol_id = DefaultMessage.protocol_id

        cls.default_protocol_configuration = ProtocolConfig.from_json(
            yaml.safe_load(open(Path(AEA_DIR, "protocols", "default", "protocol.yaml")))
        )
        cls.default_protocol = Protocol(
            default_protocol_id, DefaultSerializer(), cls.default_protocol_configuration
        )
        cls.resources.protocol_registry.register(
            default_protocol_id, cls.default_protocol
        )

        cls.error_skill = Skill.from_dir(
            Path(AEA_DIR, "skills", "error"), cls.aea.context
        )
        cls.dummy_skill = Skill.from_dir(
            Path(CUR_PATH, "data", "dummy_skill"), cls.aea.context
        )
        cls.resources.add_skill(cls.dummy_skill)
        cls.resources.add_skill(cls.error_skill)

        cls.expected_message = DefaultMessage(
            type=DefaultMessage.Type.BYTES, content=b"hello"
        )
        cls.expected_message.counterparty = cls.agent_name

        cls.t = Thread(target=cls.aea.start)
        cls.t.start()
        time.sleep(0.5)

        cls.aea.outbox.put(
            Envelope(
                to=cls.agent_name,
                sender=cls.agent_name,
                protocol_id=default_protocol_id,
                message=DefaultSerializer().encode(cls.expected_message),
            )
        )

    def test_initialize_aea_programmatically(self):
        """Test that we can initialize an AEA programmatically."""
        time.sleep(0.5)

        dummy_skill_id = DUMMY_SKILL_PUBLIC_ID
        dummy_behaviour_name = "dummy"
        dummy_behaviour = self.aea.resources.behaviour_registry.fetch(
            (dummy_skill_id, dummy_behaviour_name)
        )
        assert dummy_behaviour is not None
        assert dummy_behaviour.nb_act_called > 0

        dummy_task = DummyTask()
        task_id = self.aea.task_manager.enqueue_task(dummy_task)
        async_result = self.aea.task_manager.get_task_result(task_id)
        expected_dummy_task = async_result.get(2.0)
        assert expected_dummy_task.nb_execute_called > 0

        dummy_handler_name = "dummy"
        dummy_handler = self.aea.resources.handler_registry.fetch(
            (dummy_skill_id, dummy_handler_name)
        )
        dummy_handler_alt = self.aea.resources.handler_registry.fetch_by_protocol_and_skill(
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
        cls.t.join()
        cls.node.stop()
        Path(cls.temp).rmdir()


class TestAddBehaviourDynamically:
    """Test that we can add a behaviour dynamically."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        wallet = Wallet({FETCHAI: private_key_path})
        ledger_apis = LedgerApis({}, FETCHAI)
        resources = Resources(str(Path(CUR_PATH, "data", "dummy_aea")))
        identity = Identity(agent_name, address=wallet.addresses[FETCHAI])
        input_file = tempfile.mktemp()
        output_file = tempfile.mktemp()
        cls.agent = AEA(
            identity,
            [StubConnection(input_file, output_file)],
            wallet,
            ledger_apis,
            resources,
            is_programmatic=False,
        )

        cls.t = Thread(target=cls.agent.start)
        cls.t.start()
        time.sleep(1.0)

    def test_add_behaviour_dynamically(self):
        """Test the dynamic registration of a behaviour."""
        dummy_skill_id = PublicId("dummy_author", "dummy", "0.1.0")
        dummy_skill = self.agent.resources.get_skill(dummy_skill_id)
        assert dummy_skill is not None
        new_behaviour = DummyBehaviour(
            name="dummy2", skill_context=dummy_skill.skill_context
        )
        dummy_skill.skill_context.new_behaviours.put(new_behaviour)
        time.sleep(1.0)
        assert new_behaviour.nb_act_called > 0
        assert (
            len(self.agent.resources.behaviour_registry.fetch_by_skill(dummy_skill_id))
            == 2
        )

    @classmethod
    def teardown_class(cls):
        """Tear the class down."""
        cls.agent.stop()
        cls.t.join()
