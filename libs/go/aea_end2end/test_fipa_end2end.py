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
from libs.go.aea_end2end.pexpect_popen import PexpectWrapper
import sys
from pexpect.exceptions import EOF
from tests.conftest import _make_libp2p_connection
from tempfile import TemporaryDirectory
import asyncio
from packages.fetchai.connections.p2p_libp2p.connection import P2PLibp2pConnection

"""This module contains the end to end test for dialogues on python and golang."""
import os
from pathlib import Path
from threading import Thread
from typing import Optional, cast, Any

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
        print("MESSAGE SENT")

    def start(self, addr: Address) -> None:
        """Set counterpart address and start sending CFP."""
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
        print('GOT MESSAGE', message)
        dialogues = cast(FipaDialogues, self.context.dialogues)
        buyer_dialogue = dialogues.update(message)
        if not buyer_dialogue:
            return
        self.got_proposal = True


class Base(AEATestCaseEmpty):
    """Base class for test case."""

    package_registry_src_rel = Path(os.path.abspath("../../../packages"))

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


ROOT = Path(__file__).parent
ENV_FILE_NAME = "1.env"
exec_filename: Path = ROOT / Path("seller_agent")

ENV_TEMPLATE = """
export AEA_LEDGER_ID="fetchai"
export AEA_ADDRESS="fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"
export AEA_PUBLIC_KEY="02ac514ba70de60ed5c30f90e3acdfc958ecb416d9676706bf013228abfb2c2816"
export AEA_PRIVATE_KEY="6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e"
export AEA_P2P_POR_SERVICE_ID="acn"
export AEA_P2P_POR_LEDGER_ID="fetchai"
export AEA_P2P_POR_PEER_PUBKEY="{peer_pubkey}"
export AEA_P2P_POR_SIGNATURE="{signature}"
export AEA_P2P_DELEGATE_HOST="localhost"
export AEA_P2P_DELEGATE_PORT=11234
"""


from aea_ledger_fetchai import FetchAICrypto

class FipaSellerAgent:
    """Threaded FIPA Seller agent."""

    thread: Thread
    loop: asyncio.AbstractEventLoop
    proc: PexpectWrapper
    connection_node: P2PLibp2pConnection
    temp_dir: Any

    @classmethod
    def start(cls, multi_addr: Address):
        """Test build example, run, terminate."""
        """Run agent."""
        cls.loop = asyncio.new_event_loop()
        cls.temp_dir = TemporaryDirectory()

        cls.connection_node = _make_libp2p_connection(
            data_dir=cls.temp_dir.name, delegate=True, entry_peers=[str(multi_addr)]
        )

        cls.loop.run_until_complete(cls.connection_node.node.start())

        priv_key_file = Path(cls.temp_dir.name) / "priv_key.txt"
        priv_key_file.write_text("6d8d2b87d987641e2ca3f1991c1cccf08a118759e81fabdbf7e8484f27af015e")
        crypto = FetchAICrypto(str(priv_key_file))
        signature = crypto.sign_message(cls.connection_node.node.pub.encode())

        env_file = Path(cls.temp_dir.name) / "test.env"
        env_file.write_text(
            ENV_TEMPLATE.format(
                peer_pubkey=cls.connection_node.node.pub,
                signature=signature
            )
        )

        if exec_filename.exists():
            exec_filename.unlink()
        proc = PexpectWrapper(  # nosec
            ["go", "build"],
            cwd=str(ROOT),
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )
        proc.expect(pattern=EOF, timeout=30)
        assert proc.returncode == 0
        assert exec_filename.exists()

        cls.proc = PexpectWrapper(  # nosec
            [str(exec_filename), str(env_file)],
            cwd=str(ROOT),
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        cls.proc.expect("successfully initialized AEA!", timeout=20)
        cls.proc.expect("successfully started AEA!", timeout=20)

        return "fetch1x9v67meyfq4pkgy2n2yf6797cfkul327kpclqr"

    @classmethod
    def wait_for_envelope(cls):
        cls.proc.expect("got incoming envelope", timeout=20)

    @classmethod
    def stop(cls):
        """Stop agent and tear down."""
        node_log = Path(cls.temp_dir.name) / 'libp2p_node_10234.log'
        print(node_log.read_text())
        cls.loop.run_until_complete(cls.connection_node.node.stop())
        cls.proc.terminate()
        if exec_filename.exists():
            exec_filename.unlink()
        cls.temp_dir.cleanup()


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
                FipaSellerAgent.wait_for_envelope()
                wait_for_condition(lambda: handler.got_proposal, timeout=30)
        finally:
            FipaSellerAgent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
