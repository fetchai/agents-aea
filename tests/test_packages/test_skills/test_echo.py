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
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from ...conftest import CLI_LOG_OPTION, ROOT_DIR
from ...common.click_testing import CliRunner


class TestEchoSkill:
    """Test that echo skill works."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "my_first_agent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_echo(self, pytestconfig):
        """Run the echo skill sequence."""
        # add packages folder
        packages_src = os.path.join(ROOT_DIR, 'packages')
        packages_dst = os.path.join(self.t, 'packages')
        shutil.copytree(packages_src, packages_dst)

        # create agent
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        agent_dir_path = os.path.join(self.t, self.agent_name)
        os.chdir(agent_dir_path)

        # add skills
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "echo"], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "stub"], standalone_mode=False)
        assert result.exit_code == 0

        # disable logging
        aea_config_path = Path(self.t, self.agent_name, DEFAULT_AEA_CONFIG_FILE)
        aea_config = AgentConfig.from_json(yaml.safe_load(open(aea_config_path)))
        aea_config.logging_config = {"disable_existing_loggers": False, "version": 1,
                                     "loggers": {"aea.echo_skill": {"level": "CRITICAL"}}}
        yaml.safe_dump(aea_config.json, open(aea_config_path, "w"))

        # run the agent
        process = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run",
            "--connection",
            "stub"
        ],
            stdout=subprocess.PIPE,
            env=os.environ.copy())

        time.sleep(1.0)
        # add sending and receiving envelope from input/output files
        message = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        expected_envelope = Envelope(to=self.agent_name, sender="sender", protocol_id="default",
                                     message=DefaultSerializer().encode(message))
        encoded_envelope = "{},{},{},{}".format(expected_envelope.to, expected_envelope.sender,
                                                expected_envelope.protocol_id,
                                                expected_envelope.message.decode("utf-8"))
        encoded_envelope = encoded_envelope.encode("utf-8")
        with open(Path(self.t, self.agent_name, "input_file"), "ab+") as f:
            f.write(encoded_envelope + b"\n")
            f.flush()

        time.sleep(1.0)
        with open(Path(self.t, self.agent_name, "output_file"), "rb+") as f:
            lines = f.readlines()

        assert len(lines) == 1
        line = lines[0]
        to, sender, protocol_id, message = line.strip().split(b",", maxsplit=3)
        to = to.decode("utf-8")
        sender = sender.decode("utf-8")
        protocol_id = protocol_id.decode("utf-8")

        actual_envelope = Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message)
        assert expected_envelope.to == actual_envelope.sender
        assert expected_envelope.sender == actual_envelope.to
        assert expected_envelope.protocol_id == actual_envelope.protocol_id
        assert expected_envelope.message == actual_envelope.message

        time.sleep(0.5)
        process.send_signal(signal.SIGINT)
        time.sleep(0.5)
        process.wait(timeout=20)

        assert process.returncode == 0

        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        os.chdir(self.t)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
