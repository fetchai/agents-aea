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

        agent_dir_path = os.path.join(self.t, agent_name)
        os.chdir(agent_dir_path)

        self.add_item("skill", "fetchai/echo:0.1.0")

        try:
            process = self.run_agent()
            time.sleep(2.0)

            # add sending and receiving envelope from input/output files
            message = self.create_default_message(b"hello")
            expected_envelope = self.create_envelope(agent_name, message)

            self.write_envelope(expected_envelope)

            time.sleep(2.0)
            lines = self.readlines_output_file()

            assert len(lines) == 2
            line = lines[0] + lines[1]
            to, sender, protocol_id, message, end = line.strip().split(b",", maxsplit=4)
            to = to.decode("utf-8")
            sender = sender.decode("utf-8")
            protocol_id = self.create_public_id(protocol_id.decode("utf-8"))
            assert end in [b"", b"\n"]

            actual_envelope = self.create_envelope(
                agent_name=to, message=message, sender=sender, protocol_id=protocol_id
            )
            assert expected_envelope.to == actual_envelope.sender
            assert expected_envelope.sender == actual_envelope.to
            assert expected_envelope.protocol_id == actual_envelope.protocol_id
            assert expected_envelope.message == actual_envelope.message
            time.sleep(2.0)
        finally:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=20)
            if not process.returncode == 0:
                poll = process.poll()
                if poll is None:
                    process.terminate()
                    process.wait(2)

            os.chdir(self.t)
            self.delete_agents(agent_name)
