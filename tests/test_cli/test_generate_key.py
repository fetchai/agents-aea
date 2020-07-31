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

import os
import shutil
import tempfile
from pathlib import Path

from aea.cli import cli
from aea.crypto.registries import make_crypto

from tests.conftest import (
    CLI_LOG_OPTION,
    CliRunner,
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI,
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

    def test_fetchai(self):
        """Test that the fetch private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI])
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        make_crypto(FETCHAI, private_key_path=FETCHAI_PRIVATE_KEY_FILE)

        Path(FETCHAI_PRIVATE_KEY_FILE).unlink()

    def test_ethereum(self):
        """Test that the fetch private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", ETHEREUM])
        assert result.exit_code == 0
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        make_crypto(ETHEREUM, private_key_path=ETHEREUM_PRIVATE_KEY_FILE)

        Path(ETHEREUM_PRIVATE_KEY_FILE).unlink()

    def test_all(self):
        """Test that all the private keys are created correctly when running 'aea generate-key all'."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "all"])
        assert result.exit_code == 0

        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        make_crypto(FETCHAI, private_key_path=FETCHAI_PRIVATE_KEY_FILE)
        make_crypto(ETHEREUM, private_key_path=ETHEREUM_PRIVATE_KEY_FILE)

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
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI])
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()

        # This tests if the file has been created and its content is correct.
        make_crypto(FETCHAI, private_key_path=FETCHAI_PRIVATE_KEY_FILE)
        content = Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes()

        # Saying 'no' leave the files as it is.
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI], input="n"
        )
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes() == content

        # Saying 'yes' overwrites the file.
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI], input="y"
        )
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).read_bytes() != content
        make_crypto(FETCHAI, private_key_path=FETCHAI_PRIVATE_KEY_FILE)

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
            cli, [*CLI_LOG_OPTION, "generate-key", FETCHAI, test_file]
        )
        assert result.exit_code == 0
        assert Path(test_file).exists()

        # This tests if the file has been created and its content is correct.
        crypto = make_crypto(FETCHAI, private_key_path=test_file)
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
