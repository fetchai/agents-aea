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
from unittest import TestCase, mock

import pytest
import yaml
from aea_ledger_fetchai import FetchAICrypto

import aea
from aea.configurations.base import AgentConfig
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.test_cases import (
    AEATestCase,
    AEATestCaseEmpty,
    AEATestCaseEmptyFlaky,
    AEATestCaseManyFlaky,
    BaseAEATestCase,
)
from aea.test_tools.test_contract import BaseContractTestCase

from packages.fetchai.connections.stub.connection import PUBLIC_ID as STUB_CONNECTION_ID
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_SKILL_PUBLIC_ID
from packages.fetchai.skills.error import PUBLIC_ID as ERROR_SKILL_PUBLIC_ID

from tests.conftest import MY_FIRST_AEA_PUBLIC_ID
from tests.test_cli import test_generate_wealth, test_interact


TestWealthCommandsPositive = test_generate_wealth.TestWealthCommandsPositive
TestInteractCommand = test_interact.TestInteractCommand


class TestConfigCases(AEATestCaseEmpty):
    """Test config set/get."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        super(TestConfigCases, cls).setup_class()
        cls.add_item("connection", str(STUB_CONNECTION_ID))
        cls.add_item("skill", str(ERROR_SKILL_PUBLIC_ID))

    def test_agent_nested_set_agent_crudcollection(self):
        """Test agent test nested set from path."""
        key_name = "agent.private_key_paths.cosmos"
        self.nested_set_config(key_name, "testdata2000")
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert b"testdata2000" in result.stdout_bytes

    def test_agent_nested_set_agent_crudcollection_all(self):
        """Test agent test nested set from path."""
        key_name = "agent.private_key_paths"
        self.nested_set_config(key_name, {"cosmos": "testdata2000"})
        result = self.run_cli_command(
            "config", "get", f"{key_name}.cosmos", cwd=self._get_cwd()
        )
        assert b"testdata2000" in result.stdout_bytes

    def test_agent_nested_set_agent_simple(self):
        """Test agent test nested set from path."""
        key_name = "agent.default_ledger"
        self.nested_set_config(key_name, "some_ledger")
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert b"some_ledger" in result.stdout_bytes

    def test_agent_nested_set_skill_simple(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.skills.error.handlers.error_handler.args.some_key"
        self.nested_set_config(key_name, "some_value")
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert b"some_value" in result.stdout_bytes

    def test_agent_nested_set_skill_simple_nested(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.skills.error.handlers.error_handler.args.some_key"
        self.nested_set_config(f"{key_name}.some_nested_key", "some_value")

    def test_agent_nested_set_skill_all(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.skills.error.handlers.error_handler.args"
        self.nested_set_config(key_name, {"some_key": "some_value"})
        result = self.run_cli_command(
            "config", "get", f"{key_name}.some_key", cwd=self._get_cwd()
        )
        assert b"some_value" in result.stdout_bytes

    def test_agent_nested_set_skill_all_nested(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.skills.error.handlers.error_handler.args"
        self.nested_set_config(
            key_name, {"some_key": {"some_nested_key": "some_value"}}
        )

    def test_agent_nested_set_connection_simple(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.connections.stub.config.input_file"
        self.nested_set_config(key_name, "some_value")
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert b"some_value" in result.stdout_bytes

    def test_agent_nested_set_connection_dependency(self):
        """Test agent test nested set from path."""
        key_name = "vendor.fetchai.connections.stub.dependencies"
        self.nested_set_config(key_name, {"dep": {"version": "==1.0.0"}})

    def test_agent_set(self):
        """Test agent test set from path."""
        value = True
        key_name = "agent.logging_config.disable_existing_loggers"
        self.set_config(key_name, value)
        result = self.run_cli_command("config", "get", key_name, cwd=self._get_cwd())
        assert str(value) in str(result.stdout_bytes)

    def test_agent_get_exception(self):
        """Test agent test get non exists key."""
        with pytest.raises(Exception, match=".*bad_key.*"):
            self.run_cli_command("config", "get", "agent.bad_key", cwd=self._get_cwd())


class TestRunAgent(AEATestCaseEmpty):
    """Tests test for generic cases of AEATestCases."""

    def test_run_agent(self):
        """Run agent and test it's launched."""
        self.generate_private_key()
        self.add_private_key()
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
        thread.join()
        assert called

    def test_fetch_and_delete(self):
        """Fetch and delete agent from repo."""
        agent_name = "some_agent_for_tests"
        self.fetch_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        assert os.path.exists(agent_name)
        self.delete_agents(agent_name)
        assert not os.path.exists(agent_name)

    def test_diff(self):
        """Test difference_to_fetched_agent."""
        agent_name = "some_agent_for_tests2"
        self.fetch_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        self.run_cli_command(
            "config", "set", "agent.default_ledger", "test_ledger", cwd=agent_name
        )
        result = self.run_cli_command(
            "config", "get", "agent.default_ledger", cwd=agent_name
        )
        assert b"test_ledger" in result.stdout_bytes
        diff = self.difference_to_fetched_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        assert diff
        assert "test_ledger" in diff[1]

    def test_no_diff(self):
        """Test no difference for two aea configs."""
        agent_name = "some_agent_for_tests3"
        self.fetch_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        diff = self.difference_to_fetched_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        assert not diff

    def test_diff_different_overrides(self):
        """Test difference due to overrides."""
        agent_name = "some_agent_for_tests4"
        self.fetch_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        self.set_agent_context(agent_name)
        self.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.skills.echo.behaviours.echo.args.tick_interval",
            "2.0",
            cwd=self._get_cwd(),
        )
        diff = self.difference_to_fetched_agent(str(MY_FIRST_AEA_PUBLIC_ID), agent_name)
        assert diff
        assert diff[0] == DEFAULT_AEA_CONFIG_FILE

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


class TestDifferenceToFetchedAgent(BaseAEATestCase):
    """Test 'different_to_fetched_agent' in case of component overrides."""

    _mock_called = False
    original_function = yaml.safe_load_all
    test_agent_name: str

    @classmethod
    def setup_class(cls) -> None:
        """Set up the class."""
        super().setup_class()

        # build aea, and override the tick interval
        cls.test_agent_name = "test_agent"
        cls.fetch_agent(str(MY_FIRST_AEA_PUBLIC_ID), cls.test_agent_name)
        cls.set_agent_context(cls.test_agent_name)
        cls.run_cli_command(
            "config",
            "set",
            "vendor.fetchai.skills.echo.behaviours.echo.args.tick_interval",
            "2.0",
            cwd=cls._get_cwd(),
        )

    @classmethod
    def _safe_load_all_side_effect(cls, file):
        """Implement yaml.safe_load_all side-effect for testing."""
        result = list(cls.original_function(file))
        if not cls._mock_called:
            cls._mock_called = True
            fake_override = {}
            result.append(fake_override)
        return iter(result)

    def test_difference_to_fetched_agent(self, *_mocks):
        """Test difference to fetched agent."""
        with mock.patch(
            "yaml.safe_load_all", side_effect=self._safe_load_all_side_effect
        ):
            file_diff = self.difference_to_fetched_agent(
                str(MY_FIRST_AEA_PUBLIC_ID), self.test_agent_name
            )
            assert file_diff


class TestLoadAgentConfig(AEATestCaseEmpty):
    """Test function 'load_agent_config'."""

    def test_load_agent_config(self):
        """Test load_agent_config."""
        agent_config = self.load_agent_config(self.agent_name)
        assert isinstance(agent_config, AgentConfig)

    def test_load_agent_config_when_agent_name_not_exists(self):
        """Test load_agent_config with a wrong agent name."""
        wrong_agent_name = "non-existing-agent-name"
        with pytest.raises(
            AEATestingException,
            match=f"Cannot find agent '{wrong_agent_name}' in the current test case.",
        ):
            self.load_agent_config(wrong_agent_name)


class TestAddAndEjectComponent(AEATestCaseEmpty):
    """Test add/reject components."""

    def test_add_and_eject(self):
        """Test add/reject components."""
        result = self.add_item("skill", str(ECHO_SKILL_PUBLIC_ID), local=True)
        assert result.exit_code == 0

        result = self.eject_item("skill", str(ECHO_SKILL_PUBLIC_ID))
        assert result.exit_code == 0


class TestAddAndRemoveComponent(AEATestCaseEmpty):
    """Test add/remove components."""

    def test_add_and_eject(self):
        """Test add/reject components."""
        result = self.add_item("skill", str(ECHO_SKILL_PUBLIC_ID), local=True)
        assert result.exit_code == 0

        result = self.remove_item("skill", str(ECHO_SKILL_PUBLIC_ID))
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

        result = self.remove_private_key("cosmos")
        assert result.exit_code == 0


class TestGetWealth(AEATestCaseEmpty):
    """Test get_wealth."""

    def test_get_wealth(self):
        """Test get_wealth."""
        # just call it, network related and quite unstable
        self.generate_private_key()
        self.add_private_key()
        self.get_wealth(FetchAICrypto.identifier)


class TestGetAddress(AEATestCaseEmpty):
    """Test get_address."""

    def test_get_address(self):
        """Test get_address."""
        # just call it, network related and quite unstable
        self.generate_private_key()
        self.add_private_key()
        result = self.get_address(FetchAICrypto.identifier)
        assert len(result) == 44
        assert result.startswith("fetch")


class TestAEA(AEATestCase):
    """Test agent test set from path."""

    path_to_aea = Path("tests") / "data" / "dummy_aea"

    def test_scaffold_and_fingerprint(self):
        """Test component scaffold and fingerprint."""
        result = self.scaffold_item("skill", "skill1")
        assert result.exit_code == 0

        result = self.fingerprint_item("skill", "fetchai/skill1:0.1.0")
        assert result.exit_code == 0

    def test_scaffold_and_fingerprint_protocol(self):
        """Test component scaffold and fingerprint protocol."""
        result = self.scaffold_item("protocol", "protocol1")
        assert result.exit_code == 0

        result = self.fingerprint_item("protocol", "fetchai/protocol1:0.1.0")
        assert result.exit_code == 0


class TestSendReceiveEnvelopesSkill(AEATestCaseEmpty):
    """Test that we can communicate with agent via stub connection."""

    def test_send_receive_envelope(self):
        """Run the echo skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", str(STUB_CONNECTION_ID))
        self.add_item("skill", str(ECHO_SKILL_PUBLIC_ID))

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
            protocol_specification_id=message.protocol_specification_id,
            message=message,
        )

        self.send_envelope_to_agent(sent_envelope, self.agent_name)

        time.sleep(2.0)
        received_envelope = self.read_envelope_from_agent(self.agent_name)
        received_message = DefaultMessage.serializer.decode(received_envelope.message)
        assert sent_envelope.message.content == received_message.content


class TestInvoke(AEATestCaseEmpty):
    """Test invoke method."""

    def test_invoke(self):
        """Test invoke method."""
        result = self.invoke("--version")
        assert result.exit_code == 0
        assert f"aea, version {aea.__version__}" in result.stdout


class TestFlakyMany(AEATestCaseManyFlaky):
    """Test that flaky tests are properly rerun."""

    @pytest.mark.flaky(reruns=1)
    def test_fail_on_first_run(self):
        """Test failure on first run leads to second run."""
        file = os.path.join(self.t, "test_file")
        if self.run_count == 1:
            open(file, "a").close()
            raise AssertionError("Expected error to trigger rerun!")
        assert self.run_count == 2, "Should only be rerun once!"
        assert not os.path.isfile(file), "File should not exist"


class TestFlakyEmpty(AEATestCaseEmptyFlaky):
    """Test that flaky tests are properly rerun."""

    @pytest.mark.flaky(reruns=1)
    def test_fail_on_first_run(self):
        """Test failure on first run leads to second run."""
        file = os.path.join(self.t, "test_file")
        if self.run_count == 1:
            open(file, "a").close()
            raise AssertionError("Expected error to trigger rerun!")
        assert self.run_count == 2, "Should only be rerun once!"
        assert not os.path.isfile(file), "File should not exist"


class TestBaseContractTestCase(TestCase):
    """Test case for BaseContractTestCase ABC class."""

    @mock.patch(
        "aea.test_tools.test_contract.BaseContractTestCase.sign_send_confirm_receipt_multisig_transaction"
    )
    def test_sign_send_confirm_receipt_transaction(
        self, sign_send_confirm_receipt_multisig_transaction_mock
    ):
        """Test sign_send_confirm_receipt_multisig_transaction is called for backward compatibility."""

        class ContractTestCase(BaseContractTestCase):
            pass

        ContractTestCase.sign_send_confirm_receipt_transaction(
            "tx", "ledger_api", "crypto"
        )
        sign_send_confirm_receipt_multisig_transaction_mock.assert_called_once()
