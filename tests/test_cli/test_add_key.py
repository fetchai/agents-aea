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

"""This test module contains the tests for the `aea add-key` sub-command."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import yaml

import aea
from aea.cli import cli
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from aea.crypto.default import DefaultCrypto, DEFAULT
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FetchAICrypto, FETCHAI
from aea.crypto.helpers import DEFAULT_PRIVATE_KEY_FILE, FETCHAI_PRIVATE_KEY_FILE, ETHEREUM_PRIVATE_KEY_FILE
from ..conftest import CLI_LOG_OPTION
from ..common.click_testing import CliRunner


class TestAddKey:
    """Test that the command 'aea add-key' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = Path(cls.t, cls.agent_name)
        os.chdir(cls.t)

        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

    def test_default(self):
        """Test that the default private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", DEFAULT])
        assert result.exit_code == 0
        assert Path(DEFAULT_PRIVATE_KEY_FILE).exists()

        # this line tests that the content of the file is correct.
        DefaultCrypto(DEFAULT_PRIVATE_KEY_FILE)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", DEFAULT, DEFAULT_PRIVATE_KEY_FILE])
        assert result.exit_code == 0

        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_configuration = config.private_key_paths.read(DEFAULT)
        assert private_key_configuration is not None
        assert private_key_configuration.ledger == DEFAULT
        assert private_key_configuration.path == DEFAULT_PRIVATE_KEY_FILE

        assert len(config.private_key_paths.read_all()) == 1

    def test_fetch(self):
        """Test that the fetch private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI])
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()

        # this line tests that the content of the file is correct.
        FetchAICrypto(FETCHAI_PRIVATE_KEY_FILE)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", FETCHAI, FETCHAI_PRIVATE_KEY_FILE])
        assert result.exit_code == 0

        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_configuration = config.private_key_paths.read(FETCHAI)
        assert private_key_configuration is not None
        assert private_key_configuration.ledger == FETCHAI
        assert private_key_configuration.path == FETCHAI_PRIVATE_KEY_FILE

        assert len(config.private_key_paths.read_all()) == 2

    def test_ethereum(self):
        """Test that the ethereum private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", ETHEREUM])
        assert result.exit_code == 0
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()

        # this line tests that the content of the file is correct.
        FetchAICrypto(FETCHAI_PRIVATE_KEY_FILE)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE])
        assert result.exit_code == 0

        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_configuration = config.private_key_paths.read(ETHEREUM)
        assert private_key_configuration is not None
        assert private_key_configuration.ledger == ETHEREUM
        assert private_key_configuration.path == ETHEREUM_PRIVATE_KEY_FILE

        assert len(config.private_key_paths.read_all()) == 3

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


def test_add_key_fails_bad_key():
    """Test that 'aea add-key' fails because the key is not valid."""
    oldcwd = os.getcwd()
    runner = CliRunner()
    agent_name = "myagent"
    with tempfile.TemporaryDirectory() as tmpdir:
        with mock.patch.object(aea.crypto.helpers.logger, "error") as mock_logger_error:
            os.chdir(tmpdir)
            result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
            assert result.exit_code == 0
            os.chdir(Path(tmpdir, agent_name))

            # create an empty file - surely not a private key
            pvk_file = "this_is_not_a_key.pem"
            Path(pvk_file).touch()

            result = runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", DEFAULT, pvk_file])
            assert result.exit_code == 1
            mock_logger_error.assert_called_with("This is not a valid private key file: '{}'".format(pvk_file))

            # check that no key has been added.
            f = open(Path(DEFAULT_AEA_CONFIG_FILE))
            expected_json = yaml.safe_load(f)
            config = AgentConfig.from_json(expected_json)
            assert len(config.private_key_paths.read_all()) == 0

    os.chdir(oldcwd)


def test_add_key_fails_bad_ledger_id():
    """Test that 'aea add-key' fails because the ledger id is not valid."""
    oldcwd = os.getcwd()
    runner = CliRunner()
    agent_name = "myagent"
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
        assert result.exit_code == 0
        os.chdir(Path(tmpdir, agent_name))

        # generate a private key file
        result = runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", DEFAULT])
        assert result.exit_code == 0
        assert Path(DEFAULT_PRIVATE_KEY_FILE).exists()
        bad_ledger_id = "this_is_a_bad_ledger_id"

        result = runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", bad_ledger_id, DEFAULT_PRIVATE_KEY_FILE])
        assert result.exit_code == 2

        # check that no key has been added.
        f = open(Path(DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        assert len(config.private_key_paths.read_all()) == 0

    os.chdir(oldcwd)
