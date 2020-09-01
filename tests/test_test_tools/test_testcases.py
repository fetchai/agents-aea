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
"""This module contains a test for aea.test_tools.test_cases."""

import os
import time
from pathlib import Path

import pytest

from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue, DefaultDialogues
from aea.protocols.default.message import DefaultMessage
from aea.protocols.dialogue.base import Dialogue
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.test_cases import AEATestCase, AEATestCaseEmpty

from tests.conftest import FETCHAI
from tests.test_cli import test_generate_wealth, test_interact


TestWealthCommandsPositive = test_generate_wealth.TestWealthCommandsPositive
TestInteractCommand = test_interact.TestInteractCommand


class TestConfigCases(AEATestCaseEmpty):
    """Test config set/get."""

    def test_agent_force_set(self):
        """Test agent test force set from path."""
        key_name = "agent.private_key_paths.cosmos"
        self.force_set_config(key_name, "testdata2000")
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert b"testdata2000" in result.stdout_bytes

    def test_agent_set(self):
        """Test agent test set from path."""
        self.set_config("agent.author", "testauthor21")
        result = self.run_cli_command(
            "config", "get", "agent.author", cwd=self._get_cwd()
        )
        assert b"testauthor21" in result.stdout_bytes

    def test_agent_get_exception(self):
        """Test agent test get non exists key."""
        with pytest.raises(AEATestingException, match=".*bad_key.*"):
            self.run_cli_command("config", "get", "agent.bad_key", cwd=self._get_cwd())


class TestRunAgent(AEATestCaseEmpty):
    """Tests test for generic cases of AEATestCases."""

    def test_run_agent(self):
        """Run agent and test it's launched."""
        process = self.run_agent()
        assert self.is_running(process, timeout=30)


class TestGenericCases(AEATestCaseEmpty):
    """Tests test for generic cases of AEATestCases."""

    def test_disable_aea_logging(self):
        """Call logging disable."""
        self.disable_aea_logging()

    def test_start_subprocess(self):
        """Start a python subprocess and check output."""
        proc = self.start_subprocess("-c", "print('hi')")
        proc.wait(10)

        assert "hi" in self.stdout[proc.pid]

    def test_start_thread(self):
        """Start and join thread for python code."""
        called = False

        def fn():
            nonlocal called
            called = True

        thread = self.start_thread(fn)
        thread.join(10)
        assert called

    def test_fetch_and_delete(self):
        """Fetch and delete agent from repo."""
        agent_name = "some_agent_for_tests"
        self.fetch_agent("fetchai/my_first_aea:0.10.0", agent_name)
        assert os.path.exists(agent_name)
        self.delete_agents(agent_name)
        assert not os.path.exists(agent_name)

    def test_diff(self):
        """Test difference_to_fetched_agent."""
        agent_name = "some_agent_for_tests2"
        self.fetch_agent("fetchai/my_first_aea:0.10.0", agent_name)
        self.run_cli_command(
            "config", "set", "agent.default_ledger", "test_ledger", cwd=agent_name
        )
        result = self.run_cli_command(
            "config", "get", "agent.default_ledger", cwd=agent_name
        )
        assert b"test_ledger" in result.stdout_bytes
        diff = self.difference_to_fetched_agent(
            "fetchai/my_first_aea:0.10.0", agent_name
        )
        assert diff
        assert "test_ledger" in diff[1]

    def test_no_diff(self):
        """Test no difference for two aea configs."""
        agent_name = "some_agent_for_tests3"
        self.fetch_agent("fetchai/my_first_aea:0.10.0", agent_name)
        diff = self.difference_to_fetched_agent(
            "fetchai/my_first_aea:0.10.0", agent_name
        )
        assert not diff

    def test_terminate_subprocesses(self):
        """Start and terminate long running python subprocess."""
        proc = self.start_subprocess("-c", "import time; time.sleep(10)")
        assert proc.returncode is None
        self._terminate_subprocesses()
        assert proc.returncode is not None

    def test_miss_from_output(self):
        """Test subprocess output missing output."""
        proc = self.start_subprocess("-c", "print('hi')")
        assert len(self.missing_from_output(proc, ["hi"], timeout=5)) == 0
        assert "HI" in self.missing_from_output(proc, ["HI"], timeout=5)

    def test_replace_file_content(self):
        """Replace content of the file with another one."""
        file1 = "file1.txt"
        file2 = "file2.txt"

        with open(file1, "w") as f:
            f.write("hi")

        with open(file2, "w") as f:
            f.write("world")

        self.replace_file_content(Path(file1), Path(file2))

        with open(file2, "r") as f:
            assert f.read() == "hi"


class TestAddAndRejectComponent(AEATestCaseEmpty):
    """Test add/reject components."""

    def test_add_and_eject(self):
        """Test add/reject components."""
        result = self.add_item("skill", "fetchai/echo:0.6.0", local=True)
        assert result.exit_code == 0

        result = self.eject_item("skill", "fetchai/echo:0.6.0")
        assert result.exit_code == 0


class TestGenerateAndAddKey(AEATestCaseEmpty):
    """Test generate and add private key."""

    def test_generate_and_add_key(self):
        """Test generate and add private key."""
        result = self.generate_private_key("cosmos")
        assert result.exit_code == 0
        result = self.add_private_key(
            "cosmos", "cosmos_private_key.txt", connection=True
        )
        assert result.exit_code == 0
        result = self.add_private_key("cosmos", "cosmos_private_key.txt")
        assert result.exit_code == 0


class TestGetWealth(AEATestCaseEmpty):
    """Test get_wealth."""

    def test_get_wealth(self):
        """Test get_wealth."""
        # just call it, network related and quite unstable
        self.get_wealth(FETCHAI)


class TestAEA(AEATestCase):
    """Test agent test set from path."""

    path_to_aea = Path("tests") / "data" / "dummy_aea"

    def test_scaffold_and_fingerprint(self):
        """Test component scaffold and fingerprint."""
        result = self.scaffold_item("skill", "skill1")
        assert result.exit_code == 0

        result = self.fingerprint_item("skill", "fetchai/skill1:0.1.0")
        assert result.exit_code == 0


class TestSendReceiveEnvelopesSkill(AEATestCaseEmpty):
    """Test that we can communicate with agent via stub connection."""

    def test_send_receive_envelope(self):
        """Run the echo skill sequence."""
        self.add_item("skill", "fetchai/echo:0.6.0")

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # add sending and receiving envelope from input/output files
        sender = "sender"

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: str
        ) -> Dialogue.Role:
            return DefaultDialogue.Role.AGENT

        default_dialogues = DefaultDialogues(sender, role_from_first_message)
        message_content = b"hello"
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            content=message_content,
        )
        sent_envelope = Envelope(
            to=self.agent_name,
            sender=sender,
            protocol_id=message.protocol_id,
            message=message,
        )

        self.send_envelope_to_agent(sent_envelope, self.agent_name)

        time.sleep(2.0)
        received_envelope = self.read_envelope_from_agent(self.agent_name)
        received_message = DefaultMessage.serializer.decode(received_envelope.message)
        assert sent_envelope.message.content == received_message.content
