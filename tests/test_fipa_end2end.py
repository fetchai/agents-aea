# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This module contains the end to end test for dialogues on python and golang."""
import os
from pathlib import Path
from threading import Thread
from typing import Optional, cast

import pytest

from aea.aea_builder import AEABuilder
from aea.common import Address
from aea.configurations.base import SkillConfig
from aea.helpers.base import cd
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Handler, Skill, SkillContext
from aea.skills.behaviours import TickerBehaviour
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage

from tests.common.utils import run_in_thread, wait_for_condition


class SellerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.SELLER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )


class BuyerDialogues(FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.BUYER

        FipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )


class BuyerBehaviour(TickerBehaviour):
    """Test buyer behaviour."""

    addr: str

    def setup(self) -> None:
        """Set up behaviour."""
        self.is_started = False
        self.was_called = False

    def act(self) -> None:
        """Make an action."""
        dialogues = cast(FipaDialogues, self.context.dialogues)
        if not self.is_started or self.was_called:
            return

        cfp_msg, _ = dialogues.create(
            counterparty=self.addr,
            performative=FipaMessage.Performative.CFP,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        self.context.outbox.put_message(cfp_msg)
        self.was_called = True

    def start(self, addr: Address) -> None:
        """Set counterpart addrtess and start sending CFP."""
        self.addr = addr
        self.is_started = True


class BuyerHandler(Handler):
    """Test BuyerHandler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self.got_proposal = False

    def teardown(self) -> None:
        """Tear down handler."""

    def handle(self, message) -> None:
        """Handle an evelope."""
        dialogues = cast(FipaDialogues, self.context.dialogues)
        buyer_dialogue = dialogues.update(message)
        if not buyer_dialogue:
            return
        self.got_proposal = True


class SellerHandler(Handler):
    """Simple behaviour to count how many acts were called."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self.dialogues: Optional[FipaDialogues] = None

    def teardown(self) -> None:
        """Tear down handler."""

    def handle(self, message) -> None:
        """Handle an evelope."""
        if not self.dialogues:
            self.dialogues = SellerDialogues(self.context.agent_address)

        seller_dialogue = self.dialogues.update(message)
        if not seller_dialogue:
            return
        proposal_msg = seller_dialogue.reply(
            target_message=message,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=Description({"foo1": 1, "bar1": 2}),
        )
        self.context.outbox.put_message(proposal_msg)


class Base(AEATestCaseEmpty):
    """Base class for test case."""

    package_registry_src_rel = Path(os.path.abspath("../packages"))

    @classmethod
    def setup_class(cls) -> None:
        """Setup agent."""
        super(Base, cls).setup_class()
        cls.add_item("connection", "fetchai/p2p_libp2p:0.21.0")
        cls.add_item("protocol", "fetchai/fipa:1.0.0")
        cls.generate_private_key()
        cls.add_private_key()
        cls.add_private_key(connection=True)
        cls.run_cli_command("build", cwd=cls._get_cwd())
        cls.run_cli_command("issue-certificates", cwd=cls._get_cwd())


class FipaSellerAgent(Base):
    """Threaded FIPA Seller agent."""

    thread: Thread

    @classmethod
    def start(cls, multi_addr: Address):
        """Configure agent and start it."""
        cls.setup_class()

        result = cls.invoke(
            "config",
            "set",
            "--type",
            "dict",
            "vendor.fetchai.connections.p2p_libp2p.config",
            f"""{{
          "delegate_uri": "127.0.0.1:11001",
          "entry_peers": ["{multi_addr}"],
          "local_uri": "127.0.0.1:9001",
          "log_file": "libp2p_node.log",
          "public_uri": "127.0.0.1:9001"
        }}""",
        )
        assert result.exit_code == 0

        result = cls.invoke("get-address", "fetchai",)
        assert result.exit_code == 0
        addr = result.stdout.strip()
        cls._run()
        return addr

    @classmethod
    def _run(cls):
        """Run agent."""
        builder = AEABuilder.from_aea_project(cls._get_cwd())
        skill_context = SkillContext()
        handler = SellerHandler(name="handler", skill_context=skill_context)
        test_skill = Skill(
            SkillConfig(name="test_skill", author="fetchai"),
            skill_context=skill_context,
            handlers={"handler": handler},
            behaviours={},
        )
        builder.add_component_instance(test_skill)
        with cd(cls._get_cwd()):
            cls.agent = builder.build()
            skill_context.set_agent_context(cls.agent.context)

        cls.thread = Thread(target=cls.agent.start, daemon=True)
        cls.thread.start()
        wait_for_condition(lambda: cls.agent.is_running, timeout=20)

    @classmethod
    def stop(cls):
        """Stop agent and tear down."""
        cls.agent.stop()
        cls.thread.join(20)
        cls.teardown_class()


class TestFipaEnd2End(Base):
    """Test that echo skill works."""

    def test_run(self):
        """Run the echo skill sequence."""
        result = self.invoke(
            "get-multiaddress",
            "fetchai",
            "-c",
            "-i",
            "fetchai/p2p_libp2p:0.21.0",
            "-u",
            "public_uri",
        )
        assert result.exit_code == 0
        multi_addr = result.stdout.strip()
        result = self.invoke("get-address", "fetchai",)
        assert result.exit_code == 0
        my_addr = result.stdout.strip()
        builder = AEABuilder.from_aea_project(self._get_cwd())
        skill_context = SkillContext()
        skill_context.dialogues = BuyerDialogues(my_addr)  # type: ignore
        behaviour = BuyerBehaviour(name="behaviour", skill_context=skill_context)
        handler = BuyerHandler(name="handler", skill_context=skill_context)
        test_skill = Skill(
            SkillConfig(name="test_skill", author="fetchai"),
            skill_context=skill_context,
            handlers={"handler": handler},
            behaviours={"behaviour": behaviour},
        )
        builder.add_component_instance(test_skill)
        with cd(self._get_cwd()):
            agent = builder.build()
            skill_context.set_agent_context(agent.context)

        try:
            with run_in_thread(agent.start, timeout=120, on_exit=agent.stop):
                wait_for_condition(lambda: agent.is_running, timeout=30)
                addr = FipaSellerAgent.start(multi_addr)
                behaviour.start(addr)
                wait_for_condition(lambda: behaviour.was_called, timeout=30)
                wait_for_condition(lambda: handler.got_proposal, timeout=30)
        finally:
            FipaSellerAgent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
