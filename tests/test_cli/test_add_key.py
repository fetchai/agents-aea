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
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import (
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
)

from ..common.click_testing import CliRunner
from ..conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH


class TestAddFetchKey:
    """Test that the command 'aea add-key' works as expected for a 'fetchai' key."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = Path(cls.t, cls.agent_name)
        os.chdir(cls.t)

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name]
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        shutil.copy(
            Path(CUR_PATH, "data", "fet_private_key.txt"),
            cls.agent_folder / FETCHAI_PRIVATE_KEY_FILE,
        )

        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", FETCHAI, FETCHAI_PRIVATE_KEY_FILE]
        )

    def test_return_code(self):
        """Test return code equal to zero."""
        assert self.result.exit_code == 0

    def test_key_added(self):
        """Test that the fetch private key has been added correctly."""
        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path = config.private_key_paths.read(FETCHAI)
        assert private_key_path == FETCHAI_PRIVATE_KEY_FILE
        assert len(config.private_key_paths.read_all()) == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


class TestAddEthereumhKey:
    """Test that the command 'aea add-key' works as expected for an 'ethereum' key."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = Path(cls.t, cls.agent_name)
        os.chdir(cls.t)

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name]
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        shutil.copy(
            Path(CUR_PATH, "data", "eth_private_key.txt"),
            cls.agent_folder / ETHEREUM_PRIVATE_KEY_FILE,
        )

        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE]
        )

    def test_return_code(self):
        """Test return code equal to zero."""
        assert self.result.exit_code == 0

    def test_key_added(self):
        """Test that the fetch private key has been added correctly."""
        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path = config.private_key_paths.read(ETHEREUM)
        assert private_key_path == ETHEREUM_PRIVATE_KEY_FILE
        assert len(config.private_key_paths.read_all()) == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


class TestAddManyKeys:
    """Test that the command 'aea add-key' works as expected when adding many keys."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = Path(cls.t, cls.agent_name)
        os.chdir(cls.t)

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name]
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        shutil.copy(
            Path(CUR_PATH, "data", "fet_private_key.txt"),
            cls.agent_folder / FETCHAI_PRIVATE_KEY_FILE,
        )
        shutil.copy(
            Path(CUR_PATH, "data", "eth_private_key.txt"),
            cls.agent_folder / ETHEREUM_PRIVATE_KEY_FILE,
        )

    def test_add_many_keys(self):
        """Test that the keys are added correctly."""

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", FETCHAI, FETCHAI_PRIVATE_KEY_FILE]
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE]
        )
        assert result.exit_code == 0

        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path_ethereum = config.private_key_paths.read(FETCHAI)
        assert private_key_path_ethereum == FETCHAI_PRIVATE_KEY_FILE
        private_key_path_ethereum = config.private_key_paths.read(ETHEREUM)
        assert private_key_path_ethereum == ETHEREUM_PRIVATE_KEY_FILE
        assert len(config.private_key_paths.read_all()) == 2

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

            result = runner.invoke(
                cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
            )

            result = runner.invoke(
                cli, [*CLI_LOG_OPTION, "create", "--local", agent_name]
            )
            assert result.exit_code == 0
            os.chdir(Path(tmpdir, agent_name))

            # create an empty file - surely not a private key
            pvk_file = "this_is_not_a_key.txt"
            Path(pvk_file).touch()

            result = runner.invoke(cli, [*CLI_LOG_OPTION, "add-key", FETCHAI, pvk_file])
            assert result.exit_code == 1
            error_message = "Invalid length of private key, received 0, expected 32"
            mock_logger_error.assert_called_with(
                "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                    pvk_file, error_message
                )
            )

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

        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )

        result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
        assert result.exit_code == 0
        os.chdir(Path(tmpdir, agent_name))

        # generate a private key file
        result = runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI])
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        bad_ledger_id = "this_is_a_bad_ledger_id"

        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", bad_ledger_id, FETCHAI_PRIVATE_KEY_FILE]
        )
        assert result.exit_code == 2

        # check that no key has been added.
        f = open(Path(DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        assert len(config.private_key_paths.read_all()) == 0

    os.chdir(oldcwd)
