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

"""This test module contains the tests for the `aea remove protocol` sub-command."""

import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml

import aea
import aea.configurations.base
from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE

from packages.fetchai.protocols.gym.message import GymMessage

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner


class TestRemoveProtocolWithPublicId:
    """Test that the command 'aea remove protocol' works correctly when using the public id."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))
        cls.protocol_id = str(GymMessage.protocol_id)
        cls.protocol_name = "gym"

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "remove", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 0

    def test_directory_does_not_exist(self):
        """Test that the directory of the removed protocol does not exist."""
        assert not Path("protocols", self.protocol_name).exists()

    def test_protocol_not_present_in_agent_config(self):
        """Test that the name of the removed protocol is not present in the agent configuration file."""
        agent_config = aea.configurations.base.AgentConfig.from_json(
            yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE))
        )
        assert self.protocol_id not in agent_config.protocols

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveProtocolFailsWhenProtocolDoesNotExist:
    """Test that the command 'aea remove protocol' fails when the protocol does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))
        cls.protocol_id = str(GymMessage.protocol_id)

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "remove", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_not_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Protocol '{protocol_name}' not found.'
        """
        s = "The protocol '{}' is not supported.".format(self.protocol_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveProtocolFailsWhenExceptionOccurs:
    """Test that the command 'aea remove protocol' fails when an exception occurs while removing the directory."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))
        cls.protocol_id = str(GymMessage.protocol_id)

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        cls.patch = unittest.mock.patch(
            "shutil.rmtree", side_effect=BaseException("an exception")
        )
        cls.patch.start()

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "remove", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
