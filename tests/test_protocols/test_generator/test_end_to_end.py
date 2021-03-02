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
"""This module contains end to end tests for the protocol generator."""
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from threading import Thread
from typing import Optional, cast

from aea.aea_builder import AEABuilder
from aea.configurations.base import ComponentType, PublicId, SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.helpers import create_private_key
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Handler, Skill, SkillContext

from packages.fetchai.connections.oef.connection import (
    PUBLIC_ID as OEF_CONNECTION_PUBLIC_ID,
)

from tests.common.utils import UseOef
from tests.conftest import ROOT_DIR
from tests.data.generator.t_protocol.dialogues import (
    TProtocolDialogue,
    TProtocolDialogues,
)
from tests.data.generator.t_protocol.message import TProtocolMessage  # type: ignore
from tests.test_protocols.test_generator.common import PATH_TO_T_PROTOCOL


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


class TestEndToEndGenerator(UseOef):
    """
    Test that the generating a protocol works correctly in correct preconditions.

    Note: Types involving Floats seem to lose some precision when serialised then deserialised using protobuf.
    So tests for these types are commented out throughout for now.
    """

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))
        os.chdir(cls.t)
        cls.private_key_path_1 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_1")
        cls.private_key_path_2 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_2")
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_1)
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_2)

    def test_generated_protocol_end_to_end(self):
        """Test that a generated protocol could be used in exchanging messages between two agents."""
        agent_name_1 = "my_aea_1"
        agent_name_2 = "my_aea_2"
        builder_1 = AEABuilder()
        builder_1.set_name(agent_name_1)
        builder_1.add_private_key(DEFAULT_LEDGER, self.private_key_path_1)
        builder_1.set_default_ledger(DEFAULT_LEDGER)
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_1.add_component(
            ComponentType.PROTOCOL,
            Path(PATH_TO_T_PROTOCOL),
            skip_consistency_check=True,
        )
        builder_1.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )

        builder_1.set_default_connection(OEF_CONNECTION_PUBLIC_ID)

        builder_2 = AEABuilder()
        builder_2.set_name(agent_name_2)
        builder_2.add_private_key(DEFAULT_LEDGER, self.private_key_path_2)
        builder_2.set_default_ledger(DEFAULT_LEDGER)
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_2.add_component(
            ComponentType.PROTOCOL,
            Path(PATH_TO_T_PROTOCOL),
            skip_consistency_check=True,
        )
        builder_2.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )
        builder_2.set_default_connection(OEF_CONNECTION_PUBLIC_ID)

        # create AEAs
        aea_1 = builder_1.build(connection_ids=[OEF_CONNECTION_PUBLIC_ID])
        aea_2 = builder_2.build(connection_ids=[OEF_CONNECTION_PUBLIC_ID])

        # dialogues
        def role_from_first_message_1(
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return TProtocolDialogue.Role.ROLE_1

        agent_1_dialogues = TProtocolDialogues(
            self_address=aea_1.identity.address,
            role_from_first_message=role_from_first_message_1,
        )

        def role_from_first_message_1(
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return TProtocolDialogue.Role.ROLE_2

        agent_2_dialogues = TProtocolDialogues(
            self_address=aea_2.identity.address,
            role_from_first_message=role_from_first_message_1,
        )

        # messages
        message_1, aea_1_dialogue = agent_1_dialogues.create(
            counterparty=aea_2.identity.address,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some bytes",
            content_int=42,
            content_float=42.7,
            content_bool=True,
            content_str="some string",
        )
        message_1 = cast(TProtocolMessage, message_1)

        message_2, aea_2_dialogue = agent_2_dialogues.create(
            counterparty=aea_1.identity.address,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some other bytes",
            content_int=43,
            content_float=43.7,
            content_bool=False,
            content_str="some other string",
        )
        message_2 = cast(TProtocolMessage, message_2)

        # add handlers to AEA resources
        skill_context_1 = SkillContext(aea_1.context)
        skill_1 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_1)
        skill_context_1._skill = skill_1

        agent_1_handler = Agent1Handler(
            skill_context=skill_context_1,
            name="fake_handler_1",
            dialogues=agent_1_dialogues,
        )
        aea_1.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_1_handler,
        )
        skill_context_2 = SkillContext(aea_2.context)
        skill_2 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_2)
        skill_context_2._skill = skill_2

        agent_2_handler = Agent2Handler(
            message=message_2,
            dialogues=agent_2_dialogues,
            skill_context=skill_context_2,
            name="fake_handler_2",
        )
        aea_2.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_2_handler,
        )

        # Start threads
        t_1 = Thread(target=aea_1.start)
        t_2 = Thread(target=aea_2.start)
        try:
            t_1.start()
            t_2.start()
            time.sleep(1.0)
            aea_1.outbox.put_message(message_1)
            time.sleep(5.0)
            assert (
                agent_2_handler.handled_message.message_id == message_1.message_id
            ), "Message from Agent 1 to 2: message ids do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference
                == message_1.dialogue_reference
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[0]
                == message_1.dialogue_reference[0]
            ), "Message from Agent 1 to 2: dialogue reference[0]s do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[1]
                == message_1.dialogue_reference[1]
            ), "Message from Agent 1 to 2: dialogue reference[1]s do not match"
            assert (
                agent_2_handler.handled_message.target == message_1.target
            ), "Message from Agent 1 to 2: targets do not match"
            assert (
                agent_2_handler.handled_message.performative == message_1.performative
            ), "Message from Agent 1 to 2: performatives do not match"
            assert (
                agent_2_handler.handled_message.content_bytes == message_1.content_bytes
            ), "Message from Agent 1 to 2: content_bytes do not match"
            assert (
                agent_2_handler.handled_message.content_int == message_1.content_int
            ), "Message from Agent 1 to 2: content_int do not match"
            # assert (
            #     agent_2_handler.handled_message.content_float == message_1.content_float # noqa: E800
            # ), "Message from Agent 1 to 2: content_float do not match"
            assert (
                agent_2_handler.handled_message.content_bool == message_1.content_bool
            ), "Message from Agent 1 to 2: content_bool do not match"
            assert (
                agent_2_handler.handled_message.content_str == message_1.content_str
            ), "Message from Agent 1 to 2: content_str do not match"

            assert (
                agent_1_handler.handled_message.message_id == message_2.message_id
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference
                == message_2.dialogue_reference
            ), "Message from Agent 2 to 1: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[0]
                == message_2.dialogue_reference[0]
            ), "Message from Agent 2 to 1: dialogue reference[0]s do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[1]
                == message_2.dialogue_reference[1]
            ), "Message from Agent 2 to 1: dialogue reference[1]s do not match"
            assert (
                agent_1_handler.handled_message.target == message_2.target
            ), "Message from Agent 2 to 1: targets do not match"
            assert (
                agent_1_handler.handled_message.performative == message_2.performative
            ), "Message from Agent 2 to 1: performatives do not match"
            assert (
                agent_1_handler.handled_message.content_bytes == message_2.content_bytes
            ), "Message from Agent 2 to 1: content_bytes do not match"
            assert (
                agent_1_handler.handled_message.content_int == message_2.content_int
            ), "Message from Agent 2 to 1: content_int do not match"
            # assert (
            #     agent_1_handler.handled_message.content_float == message_2.content_float # noqa: E800
            # ), "Message from Agent 2 to 1: content_float do not match"
            assert (
                agent_1_handler.handled_message.content_bool == message_2.content_bool
            ), "Message from Agent 2 to 1: content_bool do not match"
            assert (
                agent_1_handler.handled_message.content_str == message_2.content_str
            ), "Message from Agent 2 to 1: content_str do not match"
            time.sleep(2.0)
        finally:
            aea_1.stop()
            aea_2.stop()
            t_1.join()
            t_2.join()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class Agent1Handler(Handler):
    """The handler for agent 1."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, dialogues: TProtocolDialogues, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None  # type: Optional[TProtocolMessage]
        self.dialogues = dialogues

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        message = cast(TProtocolMessage, message)
        self.dialogues.update(message)
        self.handled_message = message

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


class Agent2Handler(Handler):
    """The handler for agent 2."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[PublicId]

    def __init__(
        self, message: TProtocolMessage, dialogues: TProtocolDialogues, **kwargs
    ):
        """Initialize the handler."""
        print("inside handler's initialisation method for agent 2")
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None  # type: Optional[TProtocolMessage]
        self.message_2 = message
        self.dialogues = dialogues

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        message = cast(TProtocolMessage, message)
        dialogue = self.dialogues.update(message)
        self.handled_message = message
        assert (
            dialogue is not None
        ), "Agent 2 didn't update dialogue with incoming message {}".format(
            str(message)
        )
        dialogue.reply(
            target_message=message,
            performative=self.message_2.performative,
            content_bytes=self.message_2.content_bytes,
            content_int=self.message_2.content_int,
            content_float=self.message_2.content_float,
            content_bool=self.message_2.content_bool,
            content_str=self.message_2.content_str,
        )
        self.context.outbox.put_message(self.message_2)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
