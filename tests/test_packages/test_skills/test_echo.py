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
import signal
import time

import pytest

from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.test_tools.generic import (
    read_envelope_from_file,
    write_envelope_to_file,
)
from aea.test_tools.test_cases import AEATestCase


class TestEchoSkill(AEATestCase):
    """Test that echo skill works."""

    def test_echo(self, pytestconfig):
        """Run the echo skill sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        self.initialize_aea()
        agent_name = "my_first_agent"
        self.create_agents(agent_name)
        file = "my_file"

        agent_dir_path = os.path.join(self.t, agent_name)
        os.chdir(agent_dir_path)

        self.add_item("skill", "fetchai/echo:0.1.0")

        process = self.run_agent()
        time.sleep(2.0)

        # add sending and receiving envelope from input/output files
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content=b"hello",
        )
        expected_envelope = Envelope(
            to=agent_name,
            sender=file,
            protocol_id=message.protocol_id,
            message=DefaultSerializer().encode(message),
        )

        write_envelope_to_file(expected_envelope)

        time.sleep(2.0)
        actual_envelope = read_envelope_from_file()
        assert expected_envelope.to == actual_envelope.sender
        assert expected_envelope.sender == actual_envelope.to
        assert expected_envelope.protocol_id == actual_envelope.protocol_id
        assert expected_envelope.message == actual_envelope.message
        time.sleep(2.0)

        process.send_signal(signal.SIGINT)
        process.wait(timeout=20)
        assert process.returncode == 0
