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
"""This test module contains the tests for the `aea add protocol` sub-command."""
import os
import re
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

import aea.configurations.base
from aea.cli import cli
from aea.cli.registry.settings import REMOTE_IPFS
from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE, PublicId
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseEmptyFlaky

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.gym.message import GymMessage

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CUR_PATH,
    CliRunner,
    MAX_FLAKY_RERUNS,
    double_escape_windows_path_separator,
)


class TestAddProtocolFailsWhenProtocolAlreadyExists:
    """Test that the command 'aea add protocol' fails when the protocol already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = GymMessage.protocol_id
        cls.protocol_name = cls.protocol_id.name
        cls.protocol_author = cls.protocol_id.author
        cls.protocol_version = cls.protocol_id.version

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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
            [*CLI_LOG_OPTION, "add", "--local", "protocol", str(cls.protocol_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", str(cls.protocol_id)],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A protocol with id '{protocol_id}' already exists. Aborting...'
        """
        s = f"A protocol with id '{self.protocol_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddProtocolFailsWhenProtocolWithSameAuthorAndNameButDifferentVersion:
    """Test that the command 'aea add protocol' fails when the protocol already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = GymMessage.protocol_id
        cls.protocol_name = cls.protocol_id.name
        cls.protocol_author = cls.protocol_id.author
        cls.protocol_version = cls.protocol_id.version

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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
            [*CLI_LOG_OPTION, "add", "--local", "protocol", str(cls.protocol_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # add protocol again, but with different version number
        # first, change version number to package
        different_version = "0.1.1"
        different_id = (
            cls.protocol_author + "/" + cls.protocol_name + ":" + different_version
        )
        config_path = Path(
            cls.t,
            "packages",
            cls.protocol_author,
            "protocols",
            cls.protocol_name,
            DEFAULT_PROTOCOL_CONFIG_FILE,
        )
        config = yaml.safe_load(config_path.open())
        config["version"] = different_version
        yaml.safe_dump(config, config_path.open(mode="w"))
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", different_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A protocol with id '{protocol_id}' already exists. Aborting...'
        """
        s = f"A protocol with id '{self.protocol_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @unittest.mock.patch("aea.cli.add.get_package_path", return_value="dest/path")
    @unittest.mock.patch(
        "aea.cli.add.get_default_remote_registry", return_value=REMOTE_IPFS
    )
    @unittest.mock.patch("aea.cli.add.fetch_ipfs")
    def test_add_protocol_from_registry_positive(self, fetch_package_mock, *mocks):
        """Test add from registry positive result."""
        fetch_package_mock.return_value = Path(
            "vendor/{}/protocols/{}".format(self.protocol_author, self.protocol_name)
        )
        public_id = "{}/{}:{}".format(AUTHOR, self.protocol_name, self.protocol_version)
        obj_type = "protocol"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--remote", obj_type, public_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        public_id_obj = PublicId.from_str(public_id)
        fetch_package_mock.assert_called_once_with(obj_type, public_id_obj, "dest/path")

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddProtocolFailsWhenProtocolNotInRegistry:
    """Test that the command 'aea add protocol' fails when the protocol is not in the registry."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = "user/unknown_protocol:0.1.0"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find protocol: '{protocol_name}''
        """
        s = "Cannot find protocol: '{}'.".format(self.protocol_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddProtocolFailsWhenDifferentPublicId:
    """Test that the command 'aea add protocol' fails when the protocol has not the same public id."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = "different_author/default:1.0.0"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_wrong_public_id(self):
        """Test that the log error message is fixed."""
        s = "Cannot find protocol: '{}'.".format(self.protocol_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddProtocolFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea add protocol' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = str(GymMessage.protocol_id)

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # change the serialization of the ProtocolConfig class so to make the parsing to fail.
        cls.patch = unittest.mock.patch.object(
            aea.configurations.base.ProtocolConfig,
            "from_json",
            side_effect=ValidationError("test error message"),
        )
        cls.patch.start()

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Protocol configuration file not valid: ...'
        """
        assert re.match(
            "Protocol configuration file '.*' not valid: test error message",
            self.result.exception.message,
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddProtocolFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea add protocol' fails when the destination directory already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.protocol_id = str(GymMessage.protocol_id)
        cls.protocol_name = "gym"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(cls.agent_name)
        Path(
            cls.t, cls.agent_name, "vendor", "fetchai", "protocols", cls.protocol_name
        ).mkdir(parents=True, exist_ok=True)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", cls.protocol_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_file_exists_error(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find protocol: '{protocol_name}''
        """
        missing_path = os.path.join(
            "vendor", "fetchai", "protocols", self.protocol_name
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


class TestAddProtocolFromRemoteRegistry(AEATestCaseEmptyFlaky):
    """Test case for add protocol from Registry command."""

    IS_LOCAL = False
    IS_EMPTY = True

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_add_protocol_from_remote_registry_positive(self):
        """Test add protocol from Registry positive result."""
        self.add_item(
            "protocol", str(FipaMessage.protocol_id.to_latest()), local=self.IS_LOCAL
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "protocols")
        items_folders = os.listdir(items_path)
        item_name = "fipa"
        assert item_name in items_folders


class TestAddProtocolWithLatestVersion(AEATestCaseEmpty):
    """Test case for add protocol with latest version."""

    def test_add_protocol_latest_version(self):
        """Test add protocol with latest version."""
        self.add_item("protocol", str(FipaMessage.protocol_id.to_latest()), local=True)

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "protocols")
        items_folders = os.listdir(items_path)
        item_name = "fipa"
        assert item_name in items_folders
