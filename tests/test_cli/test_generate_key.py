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

"""This test module contains the tests for the `aea generate-key` sub-command."""
import json
import os
import shutil
import tempfile
from pathlib import Path

from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.cli import cli
from aea.crypto.registries import make_crypto
from aea.helpers.sym_link import cd
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import (
    CLI_LOG_OPTION,
    CliRunner,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
)


class TestGenerateKey:
    """Test that the command 'aea generate-key' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_fetchai(self, password_or_none):
        """Test that the fetch private key is created correctly."""
        args = [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier] + (
            ["--password", password_or_none] if password_or_none is not None else []
        )
        result = self.runner.invoke(cli, args)
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        make_crypto(
            FetchAICrypto.identifier,
            private_key_path=FETCHAI_PRIVATE_KEY_FILE,
            password=password_or_none,
        )

        Path(FETCHAI_PRIVATE_KEY_FILE).unlink()

    def test_ethereum(self, password_or_none):
        """Test that the fetch private key is created correctly."""
        args = [*CLI_LOG_OPTION, "generate-key", EthereumCrypto.identifier] + (
            ["--password", password_or_none] if password_or_none is not None else []
        )
        result = self.runner.invoke(cli, args)
        assert result.exit_code == 0
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        make_crypto(
            EthereumCrypto.identifier,
            private_key_path=ETHEREUM_PRIVATE_KEY_FILE,
            password=password_or_none,
        )

        Path(ETHEREUM_PRIVATE_KEY_FILE).unlink()

    def test_all(self):
        """Test that all the private keys are created correctly when running 'aea generate-key all'."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "all"])
        assert result.exit_code == 0

        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        make_crypto(FetchAICrypto.identifier, private_key_path=FETCHAI_PRIVATE_KEY_FILE)
        make_crypto(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_FILE
        )

        Path(FETCHAI_PRIVATE_KEY_FILE).unlink()
        Path(ETHEREUM_PRIVATE_KEY_FILE).unlink()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


class TestGenerateKeyWhenAlreadyExists:
    """Test that the command 'aea generate-key' asks for confirmation when a key already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_fetchai(self):
        """Test that the fetchai private key is overwritten or not dependending on the user input."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
        )
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()

        # This tests if the file has been created and its content is correct.
        make_crypto(FetchAICrypto.identifier, private_key_path=FETCHAI_PRIVATE_KEY_FILE)
        content = Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes()

        # Saying 'no' leave the files as it is.
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier], input="n"
        )
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes() == content

        # Saying 'yes' overwrites the file.
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier], input="y"
        )
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes() != content
        make_crypto(FetchAICrypto.identifier, private_key_path=FETCHAI_PRIVATE_KEY_FILE)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


class TestGenerateKeyWithFile:
    """Test that the command 'aea generate-key' can accept a file path."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_fetchai(self):
        """Test that the fetchai private key can be deposited in a custom file."""
        test_file = "test.txt"
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier, test_file]
        )
        assert result.exit_code == 0
        assert Path(test_file).exists()

        # This tests if the file has been created and its content is correct.
        crypto = make_crypto(FetchAICrypto.identifier, private_key_path=test_file)
        content = Path(test_file).read_bytes()
        assert content.decode("utf-8") == crypto.private_key

    def test_all(self):
        """Test that the all command does not allow a file to be provided."""
        test_file = "test.txt"
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", "all", test_file]
        )
        assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)


class TestGenerateKeyWithAddKeyWithoutConnection(AEATestCaseEmpty):
    """Test that the command 'aea generate-key --add-key' works as expected."""

    keys_config_path = "agent.private_key_paths"
    args = []  # type: ignore

    def test_fetchai(self):
        """Test that the fetch private key is created correctly."""

        with cd(self._get_cwd()):
            result = self.run_cli_command(
                "config", "get", self.keys_config_path, cwd=self._get_cwd()
            )
            assert result.exit_code == 0
            assert json.loads(result.stdout_bytes) == {}

            args = [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
            result = self.run_cli_command(
                *args, "--add-key", *self.args, cwd=self._get_cwd()
            )
            assert result.exit_code == 0
            assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
            make_crypto(
                FetchAICrypto.identifier,
                private_key_path=FETCHAI_PRIVATE_KEY_FILE,
                password=None,
            )

            Path(FETCHAI_PRIVATE_KEY_FILE).unlink()

            result = self.run_cli_command(
                "config", "get", self.keys_config_path, cwd=self._get_cwd()
            )
            assert result.exit_code == 0
            agent_keys = json.loads(result.stdout_bytes)
            assert agent_keys.get(FetchAICrypto.identifier) == FETCHAI_PRIVATE_KEY_FILE


class TestGenerateKeyWithAddKeyWithConnection(
    TestGenerateKeyWithAddKeyWithoutConnection
):
    """Test that the command 'aea generate-key --add-key' works as expected."""

    keys_config_path = "agent.connection_private_key_paths"
    args = ["--connection"]  # type: ignore
