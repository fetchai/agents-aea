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
from unittest import TestCase, mock

import pytest

from aea.cli.interact import (
    _construct_message,
    _process_envelopes,
    _try_construct_envelope,
)
from aea.helpers.base import send_control_c
from aea.mail.base import Envelope
from aea.test_tools.test_cases import AEATestCaseEmptyFlaky, AEATestCaseManyFlaky

from packages.fetchai.connections.stub.connection import PUBLIC_ID as STUB_CONNECTION_ID
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_SKILL_PUBLIC_ID

from tests.conftest import MAX_FLAKY_RERUNS


class TestInteractCommand(AEATestCaseManyFlaky):
    """Test that interact command work."""

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_interact_command_positive(self):
        """Run interaction."""
        agent_name = "test_iteraction_agent"
        self.create_agents(agent_name)

        # prepare agent
        self.set_agent_context(agent_name)
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", str(STUB_CONNECTION_ID))
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

    def test__construct_message_positive(self, *mocks):
        """Test _construct_message method for positive result."""
        envelope = mock.Mock()
        envelope.to = "receiver"
        envelope.sender = "sender"
        envelope.protocol_specification_id = "protocol-id"

        envelope.message = "Message"
        message_class = DefaultMessage
        with mock.patch.object(
            message_class.serializer, "decode", return_value="Decoded message"
        ):
            result = _construct_message("action", envelope, message_class)
            expected_result = (
                "\nAction envelope:"
                "\nto: receiver"
                "\nsender: sender"
                "\nprotocol_specification_id: protocol-id"
                "\nmessage: Message\n"
            )
            self.assertEqual(result, expected_result)

            envelope.message = b"Encoded message"
            result = _construct_message("action", envelope, message_class)
            expected_result = (
                "\nAction envelope:"
                "\nto: receiver"
                "\nsender: sender"
                "\nprotocol_specification_id: protocol-id"
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
        msg_mock = mock.Mock(spec=DefaultMessage)
        msg_mock.to = "to"
        msg_mock.sender = "sender"
        dialogues_mock.create.return_value = msg_mock, None
        message_class = mock.Mock()
        envelope = _try_construct_envelope("agent_name", dialogues_mock, message_class)
        self.assertIsInstance(envelope, Envelope)

    @mock.patch("builtins.input", return_value="")
    def test__try_construct_envelope_positive_no_input_message(self, *mocks):
        """Test _try_construct_envelope for no input message result."""
        envelope = _try_construct_envelope("agent_name", "dialogues", "message_class")
        self.assertEqual(envelope, None)

    @mock.patch("builtins.input", _raise_keyboard_interrupt)
    def test__try_construct_envelope_keyboard_interrupt(self, *mocks):
        """Test _try_construct_envelope for keyboard interrupt result."""
        with self.assertRaises(KeyboardInterrupt):
            _try_construct_envelope("agent_name", "dialogues", mock.Mock())

    @mock.patch("builtins.input", _raise_exception)
    def test__try_construct_envelope_exception_raised(self, *mocks):
        """Test _try_construct_envelope for exception raised result."""
        envelope = _try_construct_envelope("agent_name", "dialogues", "message_class")
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
        identity_stub.name = "identity_stub_name"
        inbox = mock.Mock()
        inbox.empty = lambda: False
        inbox.get_nowait = lambda: "Not None"
        outbox = mock.Mock()
        dialogues = mock.Mock()
        message_class = mock.Mock()

        try_construct_envelope_mock.return_value = None
        constructed_message = "Constructed message"
        construct_message_mock.return_value = constructed_message

        # no envelope and inbox not empty behaviour
        _process_envelopes(agent_name, inbox, outbox, dialogues, message_class)
        click_echo_mock.assert_called_once_with(constructed_message)

        # no envelope and inbox empty behaviour
        inbox.empty = lambda: True
        _process_envelopes(agent_name, inbox, outbox, dialogues, message_class)
        click_echo_mock.assert_called_with("Received no new envelope!")

        # present envelope behaviour
        try_construct_envelope_mock.return_value = "Not None envelope"
        outbox.put = mock.Mock()
        _process_envelopes(agent_name, inbox, outbox, dialogues, message_class)
        outbox.put.assert_called_once_with("Not None envelope")
        click_echo_mock.assert_called_with(constructed_message)

    @mock.patch("aea.cli.interact._try_construct_envelope", return_value=None)
    def test__process_envelopes_couldnt_recover(self, *mocks):
        """Test _process_envelopes for couldn't recover envelope result."""
        agent_name = "agent_name"
        identity_stub = mock.Mock()
        identity_stub.name = "identity_stub_name"
        inbox = mock.Mock()
        inbox.empty = lambda: False
        inbox.get_nowait = lambda: None
        outbox = mock.Mock()
        dialogues = mock.Mock()
        message_class = mock.Mock()

        with self.assertRaises(ValueError):
            _process_envelopes(agent_name, inbox, outbox, dialogues, message_class)


class TestInteractEcho(AEATestCaseEmptyFlaky):
    """Test 'aea interact' with the echo skill."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # can be flaky on Windows
    def test_interact(self):
        """Test the 'aea interact' command with the echo skill."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", str(STUB_CONNECTION_ID))
        self.add_item("skill", str(ECHO_SKILL_PUBLIC_ID))
        self.run_agent()
        process = self.run_interaction()

        assert not self.missing_from_output(
            process,
            [
                "Starting AEA interaction channel...",
                f"Provide message of protocol '{str(DefaultMessage.protocol_id)}' for performative bytes",
            ],
            timeout=10,
            is_terminating=False,
        )

        # send first message
        process.stdin.write(b"hello\n")
        process.stdin.flush()

        assert not self.missing_from_output(
            process,
            [
                "Sending envelope:",
                f"to: {self.agent_name}",
                f"sender: {self.agent_name}_interact",
                f"protocol_specification_id: {str(DefaultMessage.protocol_specification_id)}",
                "message_id=1",
                "target=0",
                "performative=bytes",
                "content=b'hello'",
                f"Provide message of protocol '{str(DefaultMessage.protocol_id)}' for performative bytes:",
            ],
            timeout=10,
            is_terminating=False,
        )

        # read incoming messages
        process.stdin.write(b"\n")
        process.stdin.flush()
        assert not self.missing_from_output(
            process,
            [
                "Interrupting input, checking inbox ...",
                "Received envelope:",
                f"to: {self.agent_name}_interact",
                f"sender: {self.agent_name}",
                f"protocol_specification_id: {str(DefaultMessage.protocol_specification_id)}",
                "message_id=-1",
                "target=1",
                "performative=bytes",
                "content=b'hello'",
                f"Provide message of protocol '{str(DefaultMessage.protocol_id)}' for performative bytes:",
            ],
            timeout=10,
            is_terminating=False,
        )

        # read another message - should return nothing
        process.stdin.write(b"\n")
        process.stdin.flush()
        assert not self.missing_from_output(
            process,
            [
                "Interrupting input, checking inbox ...",
                "Received no new envelope!",
                f"Provide message of protocol '{str(DefaultMessage.protocol_id)}' for performative bytes:",
            ],
            timeout=10,
            is_terminating=False,
        )

        send_control_c(process)

        assert not self.missing_from_output(
            process, ["Interaction interrupted!"], timeout=10, is_terminating=False
        )
