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
from unittest import TestCase, mock

import pytest
import yaml
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto
from click.exceptions import BadParameter

import aea
from aea.cli import cli
from aea.cli.add_key import _try_add_key
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CUR_PATH,
    CliRunner,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
    ROOT_DIR,
)
from tests.test_cli.tools_for_testing import ContextMock


class TestAddFetchKey:
    """Test that the command 'aea add-key' works as expected for a 'fetchai' key."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
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
            Path(CUR_PATH, "data", FETCHAI_PRIVATE_KEY_FILE),
            cls.agent_folder / FETCHAI_PRIVATE_KEY_FILE,
        )

        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add-key",
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE,
            ],
        )

    def test_return_code(self):
        """Test return code equal to zero."""
        assert self.result.exit_code == 0

    def test_key_added(self):
        """Test that the fetch private key has been added correctly."""
        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path = config.private_key_paths.read(FetchAICrypto.identifier)
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
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
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
            Path(CUR_PATH, "data", ETHEREUM_PRIVATE_KEY_FILE),
            cls.agent_folder / ETHEREUM_PRIVATE_KEY_FILE,
        )

        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add-key",
                EthereumCrypto.identifier,
                ETHEREUM_PRIVATE_KEY_FILE,
            ],
        )

    def test_return_code(self):
        """Test return code equal to zero."""
        assert self.result.exit_code == 0

    def test_key_added(self):
        """Test that the fetch private key has been added correctly."""
        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path = config.private_key_paths.read(EthereumCrypto.identifier)
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
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
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
            Path(CUR_PATH, "data", FETCHAI_PRIVATE_KEY_FILE),
            cls.agent_folder / FETCHAI_PRIVATE_KEY_FILE,
        )
        shutil.copy(
            Path(CUR_PATH, "data", ETHEREUM_PRIVATE_KEY_FILE),
            cls.agent_folder / ETHEREUM_PRIVATE_KEY_FILE,
        )

    def test_add_many_keys(self, pytestconfig):
        """Test that the keys are added correctly."""

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", FetchAICrypto.identifier],
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add-key",
                EthereumCrypto.identifier,
                ETHEREUM_PRIVATE_KEY_FILE,
            ],
        )
        assert result.exit_code == 0

        f = open(Path(self.agent_folder, DEFAULT_AEA_CONFIG_FILE))
        expected_json = yaml.safe_load(f)
        config = AgentConfig.from_json(expected_json)
        private_key_path_ethereum = config.private_key_paths.read(
            FetchAICrypto.identifier
        )
        assert private_key_path_ethereum == FETCHAI_PRIVATE_KEY_FILE
        private_key_path_ethereum = config.private_key_paths.read(
            EthereumCrypto.identifier
        )
        assert private_key_path_ethereum == ETHEREUM_PRIVATE_KEY_FILE
        assert len(config.private_key_paths.read_all()) == 2

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except OSError:
            pass


def test_add_key_fails_bad_key():
    """Test that 'aea add-key' fails because the key is not valid."""
    oldcwd = os.getcwd()
    runner = CliRunner()
    agent_name = "myagent"
    tmpdir = tempfile.mkdtemp()
    dir_path = Path("packages")
    tmp_dir = tmpdir / dir_path
    src_dir = oldcwd / Path(ROOT_DIR, dir_path)
    shutil.copytree(str(src_dir), str(tmp_dir))
    os.chdir(tmpdir)
    try:
        with mock.patch.object(
            aea.crypto.helpers._default_logger, "error"
        ) as mock_logger_error:

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

            result = runner.invoke(
                cli, [*CLI_LOG_OPTION, "add-key", FetchAICrypto.identifier, pvk_file]
            )
            assert result.exit_code == 1
            error_message = "Invalid length of private key, received 0, expected 32"
            mock_logger_error.assert_called_with(
                "This is not a valid private key file: '{}'\n Exception: '{}'".format(
                    pvk_file, error_message
                ),
            )

            # check that no key has been added.
            f = open(Path(DEFAULT_AEA_CONFIG_FILE))
            expected_json = yaml.safe_load(f)
            config = AgentConfig.from_json(expected_json)
            assert len(config.private_key_paths.read_all()) == 0
    finally:
        os.chdir(oldcwd)


def test_add_key_fails_bad_ledger_id():
    """Test that 'aea add-key' fails because the ledger id is not valid."""
    oldcwd = os.getcwd()
    runner = CliRunner()
    agent_name = "myagent"
    tmpdir = tempfile.mkdtemp()
    dir_path = Path("packages")
    tmp_dir = tmpdir / dir_path
    src_dir = oldcwd / Path(ROOT_DIR, dir_path)
    shutil.copytree(str(src_dir), str(tmp_dir))
    os.chdir(tmpdir)
    try:
        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )

        result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
        assert result.exit_code == 0
        os.chdir(Path(tmpdir, agent_name))

        # generate a private key file
        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
        )
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
    finally:
        os.chdir(oldcwd)


@mock.patch("aea.cli.add_key.open_file", mock.mock_open())
class AddKeyTestCase(TestCase):
    """Test case for _add_key method."""

    def test__add_key_positive(self, *mocks):
        """Test for _add_key method positive result."""
        ctx = ContextMock()
        _try_add_key(ctx, "type", "filepath")


@mock.patch("aea.cli.add_key.open_file", mock.mock_open())
class AddKeyConnectionTestCase(TestCase):
    """Test case for _add_key method."""

    def test__add_key_positive(self, *mocks):
        """Test for _add_key method positive result."""
        ctx = ContextMock()
        _try_add_key(ctx, "type", "filepath", connection=True)


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.add_key.try_validate_private_key_path")
@mock.patch("aea.cli.add_key._try_add_key")
class AddKeyCommandTestCase(TestCase):
    """Test case for CLI add_key command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI add_key positive result."""
        filepath = str(
            Path(ROOT_DIR, "setup.py")
        )  # some existing filepath to pass CLI argument check
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "add-key",
                FetchAICrypto.identifier,
                filepath,
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.add_key.try_validate_private_key_path")
@mock.patch("aea.cli.add_key._try_add_key")
class CheckFileNotExistsTestCase(TestCase):
    """Test case for CLI add_key command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_file_specified_does_not_exist(self, *mocks):
        """Test for CLI add_key fails on file not exists."""
        with pytest.raises(BadParameter, match=r"File '.*' does not exist."):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "--skip-consistency-check",
                    "add-key",
                    FetchAICrypto.identifier,
                    "somefile",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_file_not_specified_does_not_exist(self, *mocks):
        """Test for CLI add_key fails on file not exists."""
        with pytest.raises(BadParameter, match=r"File '.*' does not exist."):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "--skip-consistency-check",
                    "add-key",
                    FetchAICrypto.identifier,
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )


class TestAddKeyWithPassword(AEATestCaseEmpty):
    """Test the '--password' option to 'add-key' command."""

    FAKE_PASSWORD = "password"  # nosec

    @classmethod
    def setup_class(cls) -> None:
        """Set up the class."""
        super().setup_class()
        cls.run_cli_command(
            "generate-key",
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE,
            "--password",
            cls.FAKE_PASSWORD,
            cwd=cls._get_cwd(),
        )

    def test_add_key_with_password(self):
        """Test add key with password."""
        self.run_cli_command(
            "add-key",
            FetchAICrypto.identifier,
            "--password",
            self.FAKE_PASSWORD,
            cwd=self._get_cwd(),
        )
