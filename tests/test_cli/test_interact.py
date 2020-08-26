# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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


"""This test module contains tests for iteract command."""
import time
from unittest import TestCase, mock

import pytest

from aea.cli.interact import (
    _construct_message,
    _process_envelopes,
    _try_construct_envelope,
)
from aea.helpers.base import send_control_c
from aea.mail.base import Envelope
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseMany

from tests.conftest import MAX_FLAKY_RERUNS


class TestInteractCommand(AEATestCaseMany):
    """Test that interact command work."""

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_interact_command_positive(self):
        """Run interaction."""
        agent_name = "test_iteraction_agent"
        self.create_agents(agent_name)

        # prepare agent
        self.set_agent_context(agent_name)
        self.run_install()

        agent_process = self.run_agent()
        interaction_process = self.run_interaction()

        check_strings = ("Starting AEA interaction channel...",)
        missing_strings = self.missing_from_output(
            interaction_process, check_strings, is_terminating=False
        )
        assert missing_strings == [], "Strings {} didn't appear in output.".format(
            missing_strings
        )

        self.terminate_agents(interaction_process)
        self.terminate_agents(agent_process)
        assert (
            self.is_successfully_terminated()
        ), "Agent {} wasn't successfully terminated.".format(agent_name)


class ConstructMessageTestCase(TestCase):
    """Test case for _construct_message method."""

    @mock.patch(
        "aea.cli.interact.DefaultMessage.serializer.decode",
        return_value="Decoded message",
    )
    def test__construct_message_positive(self, *mocks):
        """Test _construct_message method for positive result."""
        envelope = mock.Mock()
        envelope.to = "receiver"
        envelope.sender = "sender"
        envelope.protocol_id = "protocol-id"

        envelope.message = "Message"
        result = _construct_message("action", envelope)
        expected_result = (
            "\nAction envelope:"
            "\nto: receiver"
            "\nsender: sender"
            "\nprotocol_id: protocol-id"
            "\nmessage: Message\n"
        )
        self.assertEqual(result, expected_result)

        envelope.message = b"Encoded message"
        result = _construct_message("action", envelope)
        expected_result = (
            "\nAction envelope:"
            "\nto: receiver"
            "\nsender: sender"
            "\nprotocol_id: protocol-id"
            "\nmessage: Decoded message\n"
        )
        self.assertEqual(result, expected_result)


def _raise_keyboard_interrupt():
    raise KeyboardInterrupt()


def _raise_exception():
    raise Exception()


class TryConstructEnvelopeTestCase(TestCase):
    """Test case for _try_construct_envelope method."""

    @mock.patch("builtins.input", return_value="Inputed value")
    def test__try_construct_envelope_positive(self, *mocks):
        """Test _try_construct_envelope for positive result."""
        dialogues_mock = mock.Mock()
        msg_mock = mock.Mock()
        dialogues_mock.create.return_value = msg_mock, None
        envelope = _try_construct_envelope("agent_name", dialogues_mock)
        self.assertIsInstance(envelope, Envelope)

    @mock.patch("builtins.input", return_value="")
    def test__try_construct_envelope_positive_no_input_message(self, *mocks):
        """Test _try_construct_envelope for no input message result."""
        envelope = _try_construct_envelope("agent_name", "dialogues")
        self.assertEqual(envelope, None)

    @mock.patch("builtins.input", _raise_keyboard_interrupt)
    def test__try_construct_envelope_keyboard_interrupt(self, *mocks):
        """Test _try_construct_envelope for keyboard interrupt result."""
        with self.assertRaises(KeyboardInterrupt):
            _try_construct_envelope("agent_name", "dialogues")

    @mock.patch("builtins.input", _raise_exception)
    def test__try_construct_envelope_exception_raised(self, *mocks):
        """Test _try_construct_envelope for exception raised result."""
        envelope = _try_construct_envelope("agent_name", "dialogues")
        self.assertEqual(envelope, None)


class ProcessEnvelopesTestCase(TestCase):
    """Test case for _process_envelopes method."""

    @mock.patch("aea.cli.interact.click.echo")
    @mock.patch("aea.cli.interact._construct_message")
    @mock.patch("aea.cli.interact._try_construct_envelope")
    def test__process_envelopes_positive(
        self, try_construct_envelope_mock, construct_message_mock, click_echo_mock
    ):
        """Test _process_envelopes method for positive result."""
        agent_name = "agent_name"
        identity_stub = mock.Mock()
        identity_stub.name = "identity-stub-name"
        inbox = mock.Mock()
        inbox.empty = lambda: False
        inbox.get_nowait = lambda: "Not None"
        outbox = mock.Mock()
        dialogues = mock.Mock()

        try_construct_envelope_mock.return_value = None
        constructed_message = "Constructed message"
        construct_message_mock.return_value = constructed_message

        # no envelope and inbox not empty behaviour
        _process_envelopes(agent_name, inbox, outbox, dialogues)
        click_echo_mock.assert_called_once_with(constructed_message)

        # no envelope and inbox empty behaviour
        inbox.empty = lambda: True
        _process_envelopes(agent_name, inbox, outbox, dialogues)
        click_echo_mock.assert_called_with("Received no new envelope!")

        # present envelope behaviour
        try_construct_envelope_mock.return_value = "Not None envelope"
        outbox.put = mock.Mock()
        _process_envelopes(agent_name, inbox, outbox, dialogues)
        outbox.put.assert_called_once_with("Not None envelope")
        click_echo_mock.assert_called_with(constructed_message)

    @mock.patch("aea.cli.interact._try_construct_envelope", return_value=None)
    def test__process_envelopes_couldnt_recover(self, *mocks):
        """Test _process_envelopes for couldn't recover envelope result."""
        agent_name = "agent_name"
        identity_stub = mock.Mock()
        identity_stub.name = "identity-stub-name"
        inbox = mock.Mock()
        inbox.empty = lambda: False
        inbox.get_nowait = lambda: None
        outbox = mock.Mock()
        dialogues = mock.Mock()

        with self.assertRaises(ValueError):
            _process_envelopes(agent_name, inbox, outbox, dialogues)


class TestInteractEcho(AEATestCaseEmpty):
    """Test 'aea interact' with the echo skill."""

    @pytest.mark.integration
    def test_interact(self):
        """Test the 'aea interact' command with the echo skill."""
        self.add_item("skill", "fetchai/echo:0.6.0")
        self.run_agent()
        process = self.run_interaction()

        time.sleep(1.0)

        # send first message
        process.stdin.write(b"hello\n")
        process.stdin.flush()
        time.sleep(3.0)

        # read incoming messages
        process.stdin.write(b"\n")
        process.stdin.flush()
        time.sleep(1.0)

        # read another message - should return nothing
        process.stdin.write(b"\n")
        process.stdin.flush()
        time.sleep(1.0)

        send_control_c(process)
        time.sleep(0.5)

        expected_output = [
            "Starting AEA interaction channel...",
            "Provide message of protocol fetchai/default:0.5.0 for performative bytes:",
            "Sending envelope:",
            f"to: {self.agent_name}",
            f"sender: {self.agent_name}_interact",
            "protocol_id: fetchai/default:0.5.0",
            "message_id=1,target=0,performative=bytes,content=b'hello')",
            "Provide message of protocol fetchai/default:0.5.0 for performative bytes:",
            "Interrupting input, checking inbox ...",
            "Received envelope:",
            f"to: {self.agent_name}_interact",
            f"sender: {self.agent_name}",
            "protocol_id: fetchai/default:0.5.0",
            "message_id=2,target=1,performative=bytes,content=b'hello')",
            "Provide message of protocol fetchai/default:0.5.0 for performative bytes:",
            "Interrupting input, checking inbox ...",
            "Received no new envelope!",
            "Provide message of protocol fetchai/default:0.5.0 for performative bytes:",
            "Interaction interrupted!",
        ]
        missing = self.missing_from_output(
            process, expected_output, timeout=10, is_terminating=False
        )
        assert len(missing) == 0, "Strings {} didn't appear in agent output.".format(
            missing
        )
