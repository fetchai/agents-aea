# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This test module contains the tests for the `aea add connection` sub-command."""
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from jsonschema import ValidationError

import aea.configurations.base
from aea.cli import cli
from aea.cli.registry.settings import REMOTE_IPFS
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE, PublicId
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseEmptyFlaky

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.connections.local.connection import (
    PUBLIC_ID as LOCAL_CONNECTION_PUBLIC_ID,
)

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CUR_PATH,
    CliRunner,
    MAX_FLAKY_RERUNS,
    double_escape_windows_path_separator,
)


class TestAddConnectionFailsWhenConnectionAlreadyExists:
    """Test that the command 'aea add connection' fails when the connection already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_name = "http_client"
        cls.connection_author = "fetchai"
        cls.connection_version = "0.3.0"
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        # add connection first time
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        # add connection again
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    @unittest.mock.patch("aea.cli.add.get_package_path", return_value="dest/path")
    @unittest.mock.patch(
        "aea.cli.add.get_default_remote_registry", return_value=REMOTE_IPFS
    )
    @unittest.mock.patch("aea.cli.add.fetch_ipfs")
    def test_add_connection_from_registry_positive(self, fetch_package_mock, *mocks):
        """Test add from registry positive result."""
        fetch_package_mock.return_value = Path(
            "vendor/{}/connections/{}".format(
                self.connection_author, self.connection_name
            )
        )
        public_id = "{}/{}:{}".format(
            AUTHOR, self.connection_name, self.connection_version
        )
        obj_type = "connection"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--remote", obj_type, public_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0, result.stdout
        public_id_obj = PublicId.from_str(public_id)
        fetch_package_mock.assert_called_once_with(obj_type, public_id_obj, "dest/path")

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A connection with id '{connection_id}' already exists. Aborting...'
        """
        s = f"A connection with id '{self.connection_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFailsWhenConnectionWithSameAuthorAndNameButDifferentVersion:
    """Test that 'aea add connection' fails when the connection with different version already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_name = "http_client"
        cls.connection_author = "fetchai"
        cls.connection_version = "0.3.0"
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        # add connection first time
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # add connection again, but with different version number
        # first, change version number to package
        different_version = "0.1.1"
        different_id = (
            cls.connection_author + "/" + cls.connection_name + ":" + different_version
        )
        config_path = Path(
            cls.t,
            "packages",
            cls.connection_author,
            "connections",
            cls.connection_name,
            DEFAULT_CONNECTION_CONFIG_FILE,
        )
        config = yaml.safe_load(config_path.open())
        config["version"] = different_version
        yaml.safe_dump(config, config_path.open(mode="w"))
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", different_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A connection with id '{connection_id}' already exists. Aborting...'
        """
        s = f"A connection with id '{self.connection_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFailsWhenConnectionNotInRegistry:
    """Test that the command 'aea add connection' fails when the connection is not in the registry."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = "author/unknown_connection:0.1.0"
        cls.connection_name = "unknown_connection"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find connection: '{connection_name}''
        """
        s = "Cannot find connection: '{}'.".format(self.connection_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFailsWhenDifferentPublicId:
    """Test that the command 'aea add connection' fails when the connection has not the same public id."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = "different_author/local:0.1.0"
        cls.connection_name = "unknown_connection"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_wrong_public_id(self):
        """Test that the log error message is fixed."""
        s = "Cannot find connection: '{}'.".format(self.connection_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea add connection' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        cls.connection_name = "http_client"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # change the serialization of the AgentConfig class so to make the parsing to fail.
        cls.patch = unittest.mock.patch.object(
            aea.configurations.base.ConnectionConfig,
            "from_json",
            side_effect=ValidationError("test error message"),
        )
        cls.patch.start()

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Connection configuration file not valid: '{connection_name}''
        """
        s = "Connection configuration file not valid: test error message"
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea add connection' fails when the destination directory already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        cls.connection_name = "http_client"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(cls.agent_name)
        Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "connections",
            cls.connection_name,
        ).mkdir(parents=True, exist_ok=True)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_file_exists_error(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find connection: '{connection_name}''
        """
        missing_path = os.path.join(
            "vendor", "fetchai", "connections", self.connection_name
        )
        missing_path = double_escape_windows_path_separator(missing_path)
        assert missing_path in self.result.exception.message

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddConnectionFromRemoteRegistry(AEATestCaseEmptyFlaky):
    """Test case for add connection from Registry command."""

    IS_LOCAL = False
    IS_EMPTY = True

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_add_connection_from_remote_registry_positive(self):
        """Test add connection from Registry positive result."""
        self.add_item(
            "connection",
            str(LOCAL_CONNECTION_PUBLIC_ID.to_latest()),
            local=self.IS_LOCAL,
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "connections")
        items_folders = os.listdir(items_path)
        item_name = "local"
        assert item_name in items_folders


class TestAddConnectionWithLatestVersion(AEATestCaseEmpty):
    """Test case for add connection with latest version."""

    def test_add_connection_latest_version(self):
        """Test add connection with latest version."""
        self.add_item(
            "connection", str(LOCAL_CONNECTION_PUBLIC_ID.to_latest()), local=True
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "connections")
        items_folders = os.listdir(items_path)
        item_name = "local"
        assert item_name in items_folders


@pytest.mark.skip  # need remote registry
class TestAddConnectionMixedWhenNoLocalRegistryExists:
    """Test that the command 'aea add connection' works in mixed mode when the local registry does not exists (it swaps to remote)."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        cls.connection_name = "http_client"

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(cls.agent_name)
        with patch("aea.cli.registry.utils.request_api"), patch(
            "aea.cli.add.fetch_package"
        ), patch("aea.cli.add.load_item_config"), patch(
            "aea.cli.add.is_fingerprint_correct"
        ), patch(
            "aea.cli.add.register_item"
        ):

            cls.result = cls.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "add", "connection", cls.connection_id],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0."""
        assert self.result.exit_code == 0

    def test_standard_output_mentions_swap_to_remote(self):
        """Test standard output contains information on swap to remote."""
        assert "Trying remote registry (`--remote`)." in self.result.stdout

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@pytest.mark.skip  # need remote registry
class TestAddConnectionLocalWhenNoLocalRegistryExists:
    """Test that the command 'aea add connection' fails in local mode when the local registry does not exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        cls.connection_name = "http_client"

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )
        assert result.exit_code == 0, result.stdout

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0, result.stdout

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1."""
        assert self.result.exit_code == 1, self.result.stdout

    def test_standard_output_mentions_failure(self):
        """Test standard output contains information on failure."""
        assert (
            "Registry path not provided and local registry `packages` not found in current (.) and parent directory."
            in self.result.exception.message
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
