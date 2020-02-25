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
"""This module contains the tests for the protocol generator."""

import inspect
import logging
import os
import pytest
import shutil
import tempfile
import time
import yaml
from threading import Thread
from typing import Optional

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ProtocolConfig, PublicId, ProtocolId
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Protocol, Message
from aea.registries.base import Resources
from aea.skills.base import Handler, Skill, SkillContext

from packages.fetchai.connections.oef.connection import OEFConnection

from tests.data.generator.two_party_negotiation.message import TwoPartyNegotiationMessage
from tests.data.generator.two_party_negotiation.serialization import TwoPartyNegotiationSerializer

from ..common.click_testing import CliRunner

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
HOST = "127.0.0.1"
PORT = 10000


class TestGenerateProtocol:
    """Test that the generating a protocol works correctly in correct preconditions."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "agent_1"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_generated_protocol_serialisation(self):
        """Test that a generated protocol's serialisation + deserialisation work correctly."""
        # create a message
        message = TwoPartyNegotiationMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TwoPartyNegotiationMessage.Performative.ACCEPT,
        )

        # serialise the message
        encoded_message_in_bytes = TwoPartyNegotiationSerializer().encode(message)

        # deserialise the message
        decoded_message = TwoPartyNegotiationSerializer().decode(encoded_message_in_bytes)

        # Compare the original message with the serialised+deserialised message
        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative

    def test_generated_protocol_end_to_end(self):
        """Test that a generated protocol could be used in exchanging messages between two agents."""
        # AEA components
        ledger_apis = LedgerApis({}, FETCHAI)

        wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
        wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})

        identity_1 = Identity(
            name="my_aea_1",
            address=wallet_1.addresses.get(FETCHAI),
            default_address_key=FETCHAI,
        )
        identity_2 = Identity(
            name="my_aea_2",
            address=wallet_2.addresses.get(FETCHAI),
            default_address_key=FETCHAI,
        )

        oef_connection_1 = OEFConnection(
            address=identity_1.address, oef_addr=HOST, oef_port=PORT
        )
        oef_connection_2 = OEFConnection(
            address=identity_2.address, oef_addr=HOST, oef_port=PORT
        )

        resources_1 = Resources()
        resources_2 = Resources()

        # add generated protocols to resources
        generated_protocol_configuration = ProtocolConfig.from_json(
            yaml.safe_load(
                open(os.path.join(self.cwd, "tests", "data", "generator", "two_party_negotiation", "protocol.yaml"))
            )
        )
        generated_protocol = Protocol(
            TwoPartyNegotiationMessage.protocol_id,
            TwoPartyNegotiationSerializer(),
            generated_protocol_configuration,
        )
        resources_1.protocol_registry.register(
            TwoPartyNegotiationMessage.protocol_id, generated_protocol
        )
        resources_2.protocol_registry.register(
            TwoPartyNegotiationMessage.protocol_id, generated_protocol
        )

        # create AEAs
        aea_1 = AEA(identity_1, [oef_connection_1], wallet_1, ledger_apis, resources_1)
        aea_2 = AEA(identity_2, [oef_connection_2], wallet_2, ledger_apis, resources_2)

        # message 1
        message = TwoPartyNegotiationMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TwoPartyNegotiationMessage.Performative.ACCEPT,
        )
        encoded_message_in_bytes = TwoPartyNegotiationSerializer().encode(message)
        envelope = Envelope(
            to=identity_2.address,
            sender=identity_1.address,
            protocol_id=TwoPartyNegotiationMessage.protocol_id,
            message=encoded_message_in_bytes,
        )
        # message 2
        message_2 = TwoPartyNegotiationMessage(
            message_id=2,
            dialogue_reference=(str(0), ""),
            target=1,
            performative=TwoPartyNegotiationMessage.Performative.DECLINE,
        )
        encoded_message_2_in_bytes = TwoPartyNegotiationSerializer().encode(message_2)

        # add handlers to AEA resources
        agent_1_handler = Agent1Handler(skill_context=SkillContext(aea_1.context), name="fake_skill")
        resources_1.handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TwoPartyNegotiationMessage.protocol_id,
            ),
            agent_1_handler,
        )
        agent_2_handler = Agent2Handler(encoded_messsage=encoded_message_2_in_bytes, skill_context=SkillContext(aea_2.context), name="fake_skill")
        resources_2.handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TwoPartyNegotiationMessage.protocol_id,
            ),
            agent_2_handler,
        )

        # add error skill to AEAs
        error_skill_1 = Skill.from_dir(
            os.path.join(AEA_DIR, "skills", "error"), aea_1.context
        )
        resources_1.add_skill(error_skill_1)

        error_skill_2 = Skill.from_dir(
            os.path.join(AEA_DIR, "skills", "error"), aea_2.context
        )
        resources_2.add_skill(error_skill_2)

        # Start threads
        t_1 = Thread(target=aea_1.start)
        t_2 = Thread(target=aea_2.start)
        try:
            t_1.start()
            t_2.start()
            time.sleep(1.0)
            aea_1.outbox.put(envelope)
            time.sleep(5.0)
            assert agent_2_handler.handled_message.message_id == message.message_id, "Message from Agent 1 to 2: message ids do not match"
            assert agent_2_handler.handled_message.dialogue_reference == message.dialogue_reference, "Message from Agent 1 to 2: dialogue references do not match"
            assert agent_2_handler.handled_message.dialogue_reference[0] == message.dialogue_reference[0], "Message from Agent 1 to 2: dialogue reference[0]s do not match"
            assert agent_2_handler.handled_message.dialogue_reference[1] == message.dialogue_reference[1], "Message from Agent 1 to 2: dialogue reference[1]s do not match"
            assert agent_2_handler.handled_message.target == message.target, "Message from Agent 1 to 2: targets do not match"
            assert agent_2_handler.handled_message.performative == message.performative, "Message from Agent 1 to 2: performatives do not match"

            assert agent_1_handler.handled_message.message_id == message_2.message_id, "Message from Agent 1 to 2: dialogue references do not match"
            assert agent_1_handler.handled_message.dialogue_reference == message_2.dialogue_reference, "Message from Agent 2 to 1: dialogue references do not match"
            assert agent_1_handler.handled_message.dialogue_reference[0] == message_2.dialogue_reference[0], "Message from Agent 2 to 1: dialogue reference[0]s do not match"
            assert agent_1_handler.handled_message.dialogue_reference[1] == message_2.dialogue_reference[1], "Message from Agent 2 to 1: dialogue reference[1]s do not match"
            assert agent_1_handler.handled_message.target == message_2.target, "Message from Agent 2 to 1: targets do not match"
            assert agent_1_handler.handled_message.performative == message_2.performative, "Message from Agent 2 to 1: performatives do not match"
            time.sleep(2.0)
        finally:
            aea_1.stop()
            aea_2.stop()
            t_1.join()
            t_2.join()

    # def test_generated_protocol_1_agent(self):
    #     """Test that a generated protocol could be used in exchanging messages between two agents."""
    #     # create agent
    #     result = self.runner.invoke(
    #         cli, [*CLI_LOG_OPTION, "create", self.agent_name], standalone_mode=False
    #     )
    #     assert result.exit_code == 0
    #     agent_dir_path = os.path.join(self.t, self.agent_name)
    #     os.chdir(agent_dir_path)
    #
    #     # copy protocol to the agent
    #     packages_src = os.path.join(self.cwd, "tests", "data", "generator", "two_party_negotiation")
    #     packages_dst = os.path.join(agent_dir_path, "protocols", "two_party_negotiation")
    #     shutil.copytree(packages_src, packages_dst)
    #
    #     # add protocol to the agent's config
    #     aea_config_path = Path(self.t, self.agent_name, DEFAULT_AEA_CONFIG_FILE)
    #     aea_config = AgentConfig.from_json(yaml.safe_load(open(aea_config_path)))
    #     aea_config.protocols = [
    #         "fetchai/default:0.1.0",
    #         "fetchai/two_party_negotiation:0.1.0",
    #     ]
    #     yaml.safe_dump(aea_config.json, open(aea_config_path, "w"))
    #
    #     try:
    #         # run the agent
    #         process = subprocess.Popen(  # nosec
    #             [sys.executable, "-m", "aea.cli", "run"],
    #             stdout=subprocess.PIPE,
    #             env=os.environ.copy(),
    #         )
    #         time.sleep(2.0)
    #
    #         # create a message
    #         message = TwoPartyNegotiationMessage(
    #             message_id=1,
    #             dialogue_reference=(str(0), ""),
    #             target=0,
    #             performative=TwoPartyNegotiationMessage.Performative.ACCEPT,
    #         )
    #
    #         # serialise the message
    #         encoded_message_in_bytes = TwoPartyNegotiationSerializer().encode(message)
    #
    #         # deserialise the message
    #         decoded_message = TwoPartyNegotiationSerializer().decode(encoded_message_in_bytes)
    #
    #         # Compare the original message with the serialised+deserialised message
    #         assert decoded_message.message_id == message.message_id
    #         assert decoded_message.dialogue_reference == message.dialogue_reference
    #         assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
    #         assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
    #         assert decoded_message.target == message.target
    #         assert decoded_message.performative == message.performative
    #
    #         time.sleep(2.0)
    #     finally:
    #         process.send_signal(signal.SIGINT)
    #         process.wait(timeout=20)
    #         if not process.returncode == 0:
    #             poll = process.poll()
    #             if poll is None:
    #                 process.terminate()
    #                 process.wait(2)
    #
    #         os.chdir(self.t)
    #         result = self.runner.invoke(
    #             cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False
    #         )
    #         assert result.exit_code == 0
    #
    # def test_generated_protocol_2_agents(self):
    #     """Test that a generated protocol could be used in exchanging messages between two agents."""
    #     # add packages folder
    #     packages_src = os.path.join(self.cwd, "tests", "data", "generator", "two_party_negotiation")
    #     packages_dst = os.path.join(self.t, "packages", "fetchai", "protocols", "two_party_negotiation")
    #     shutil.copytree(packages_src, packages_dst)
    #
    #     # create agent
    #     result = self.runner.invoke(
    #         cli, [*CLI_LOG_OPTION, "create", self.agent_name], standalone_mode=False
    #     )
    #     assert result.exit_code == 0
    #     agent_dir_path = os.path.join(self.t, self.agent_name)
    #     os.chdir(agent_dir_path)
    #
    #     # add protocol
    #     result = self.runner.invoke(
    #         cli,
    #         [*CLI_LOG_OPTION, "add", "protocol", "fetchai/two_party_negotiation:0.1.0"],
    #         standalone_mode=False,
    #     )
    #     assert result.exit_code == 0
    #
    #     # import pdb; pdb.set_trace()
    #
    #     try:
    #         # run the agent
    #         process = subprocess.Popen(  # nosec
    #             [sys.executable, "-m", "aea.cli", "run"],
    #             stdout=subprocess.PIPE,
    #             env=os.environ.copy(),
    #         )
    #         time.sleep(2.0)
    #
    #         # create a message
    #         message = TwoPartyNegotiationMessage(
    #             message_id=1,
    #             dialogue_reference=(str(0), ""),
    #             target=0,
    #             performative=TwoPartyNegotiationMessage.Performative.ACCEPT,
    #         )
    #
    #         # serialise the message
    #         encoded_message_in_bytes = TwoPartyNegotiationSerializer().encode(message)
    #
    #         # deserialise the message
    #         decoded_message = TwoPartyNegotiationSerializer().decode(encoded_message_in_bytes)
    #
    #         # Compare the original message with the serialised+deserialised message
    #         assert decoded_message.message_id == message.message_id
    #         assert decoded_message.dialogue_reference == message.dialogue_reference
    #         assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
    #         assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
    #         assert decoded_message.target == message.target
    #         assert decoded_message.performative == message.performative
    #
    #         time.sleep(2.0)
    #     finally:
    #         process.send_signal(signal.SIGINT)
    #         process.wait(timeout=20)
    #         if not process.returncode == 0:
    #             poll = process.poll()
    #             if poll is None:
    #                 process.terminate()
    #                 process.wait(2)
    #
    #         os.chdir(self.t)
    #         result = self.runner.invoke(
    #             cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False
    #         )
    #         assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            pass
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class Agent1Handler(Handler):
    """The handler for agent 1."""

    SUPPORTED_PROTOCOL = TwoPartyNegotiationMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


class Agent2Handler(Handler):
    """The handler for agent 2."""

    SUPPORTED_PROTOCOL = TwoPartyNegotiationMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, encoded_messsage, **kwargs):
        """Initialize the handler."""
        print("inside handler's initialisation method for agent 2")
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None
        self.encoded_message_2_in_bytes = encoded_messsage

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message
        envelope = Envelope(
            to=message.counterparty,
            sender=self.context.agent_address,
            protocol_id=TwoPartyNegotiationMessage.protocol_id,
            message=self.encoded_message_2_in_bytes,
        )
        self.context.outbox.put(envelope)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """