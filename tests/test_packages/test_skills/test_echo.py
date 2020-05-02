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

import os
import time

from aea.connections.stub.connection import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
)
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.generic import (
    read_envelope_from_file,
    write_envelope_to_file,
)
from aea.test_tools.test_cases import AEATestCase


class TestEchoSkill(AEATestCase):
    """Test that echo skill works."""

    @skip_test_ci
    def test_echo(self, pytestconfig):
        """Run the echo skill sequence."""
        self.initialize_aea()
        agent_name = "my_first_agent"
        self.create_agents(agent_name)

        agent_dir_path = os.path.join(self.t, agent_name)
        os.chdir(agent_dir_path)

        self.add_item("skill", "fetchai/echo:0.1.0")

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # add sending and receiving envelope from input/output files
        message_content = b"hello"
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content=message_content,
        )
        sent_envelope = Envelope(
            to=agent_name,
            sender="sender",
            protocol_id=message.protocol_id,
            message=DefaultSerializer().encode(message),
        )

        write_envelope_to_file(sent_envelope, DEFAULT_INPUT_FILE_NAME)

        time.sleep(2.0)
        received_envelope = read_envelope_from_file(DEFAULT_OUTPUT_FILE_NAME)

        assert sent_envelope.to == received_envelope.sender
        assert sent_envelope.sender == received_envelope.to
        assert sent_envelope.protocol_id == received_envelope.protocol_id
        assert sent_envelope.message == received_envelope.message

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
