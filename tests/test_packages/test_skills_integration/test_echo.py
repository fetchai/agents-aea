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

"""This test module contains the integration test for the echo skill."""
import time

from aea.common import Address
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.protocols.default.dialogues import DefaultDialogue
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage


class DefaultDialogues(BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


class TestEchoSkill(AEATestCaseEmpty):
    """Test that echo skill works."""

    capture_log = True

    def test_echo(self):
        """Run the echo skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", "fetchai/stub:0.21.0")
        self.add_item("skill", "fetchai/echo:0.19.0")

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # add sending and receiving envelope from input/output files
        sender = "sender"
        default_dialogues = DefaultDialogues(sender)
        message_content = b"hello"
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            content=message_content,
        )
        sent_envelope = Envelope(to=self.agent_name, sender=sender, message=message,)

        self.send_envelope_to_agent(sent_envelope, self.agent_name)

        time.sleep(2.0)
        received_envelope = self.read_envelope_from_agent(self.agent_name)

        assert sent_envelope.sender == received_envelope.to
        assert (
            sent_envelope.protocol_specification_id
            == received_envelope.protocol_specification_id
        )
        msg = DefaultMessage.serializer.decode(received_envelope.message)
        assert sent_envelope.message.content == msg.content

        check_strings = (
            "Echo Handler: setup method called.",
            "Echo Behaviour: setup method called.",
            "Echo Behaviour: act method called.",
            "content={}".format(message_content),
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "Echo agent wasn't successfully terminated."
