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

"""This test module contains the tests for the `aea create` sub-command."""

import filecmp
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict
from unittest import TestCase
from unittest.mock import patch

import jsonschema
from jsonschema import Draft4Validator

import pytest

import yaml

import aea
from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.constants import (
    DEFAULT_CONNECTION,
    DEFAULT_PROTOCOL,
    DEFAULT_SKILL,
)
from aea.configurations.loader import ConfigLoader, make_jsonschema_base_uri

from tests.conftest import (
    AGENT_CONFIGURATION_SCHEMA,
    AUTHOR,
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    CliRunner,
    ROOT_DIR,
    skip_test_windows,
)


class TestCreate:
    """Test that the command 'aea create <agent_name>' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        cls.agent_config = cls._load_config_file(cls.agent_name)

    @classmethod
    def _load_config_file(cls, agent_name) -> Dict:
        """Load a config file."""
        agent_config_file = Path(agent_name, DEFAULT_AEA_CONFIG_FILE)  # type: ignore
        file_pointer = open(agent_config_file, mode="r", encoding="utf-8")
        agent_config_instance = yaml.safe_load(file_pointer)
        return agent_config_instance

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    def test_agent_directory_path_exists(self):
        """Check that the agent's directory has been created."""
        agent_dir = Path(self.agent_name)
        assert agent_dir.exists()
        assert agent_dir.is_dir()

    def test_configuration_file_has_been_created(self):
        """Check that an agent's configuration file has been created."""
        agent_config_file = Path(self.agent_name, DEFAULT_AEA_CONFIG_FILE)
        assert agent_config_file.exists()
        assert agent_config_file.is_file()

    def test_configuration_file_is_compliant_to_schema(self):
        """Check that the agent's configuration file is compliant with the schema."""
        try:
            self.validator.validate(instance=self.agent_config)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(
                "Configuration file is not compliant with the schema. Exception: {}".format(
                    str(e)
                )
            )

    def test_aea_version_is_correct(self):
        """Check that the aea version in the configuration file is correct, i.e. the same of the installed package."""
        assert self.agent_config["aea_version"] == aea.__version__

    def test_agent_name_is_correct(self):
        """Check that the agent name in the configuration file is correct."""
        assert self.agent_config["agent_name"] == self.agent_name

    def test_authors_field_is_empty_string(self):
        """Check that the 'authors' field in the config file is the empty string."""
        assert self.agent_config["author"] == AUTHOR

    def test_connections_contains_only_stub(self):
        """Check that the 'connections' list contains only the 'stub' connection."""
        assert self.agent_config["connections"] == [str(DEFAULT_CONNECTION)]

    def test_default_connection_field_is_stub(self):
        """Check that the 'default_connection' is the 'stub' connection."""
        assert self.agent_config["default_connection"] == str(DEFAULT_CONNECTION)

    def test_license_field_is_empty_string(self):
        """Check that the 'license' is the empty string."""
        assert (
            self.agent_config["license"] == aea.configurations.constants.DEFAULT_LICENSE
        )

    # def test_private_key_pem_path_field_is_empty_string(self):
    #     """Check that the 'private_key_pem_path' is the empty string."""
    #         #     assert self.agent_config["private_key_pem_path"] == ""

    def test_protocols_field_is_not_empty_list(self):
        """Check that the 'protocols' field is a list with the 'default' protocol."""
        assert self.agent_config["protocols"] == [str(DEFAULT_PROTOCOL)]

    def test_skills_field_is_not_empty_list(self):
        """Check that the 'skills' field is a list with the 'error' skill."""
        assert self.agent_config["skills"] == [str(DEFAULT_SKILL)]

    def test_connections_field_is_not_empty_list(self):
        """Check that the 'connections' field is a list with the 'error' skill."""
        assert self.agent_config["skills"] == [str(DEFAULT_SKILL)]

    def test_version_field_is_equal_to_0_1_0(self):
        """Check that the 'version' field is equal to the string '0.1.0'."""
        assert self.agent_config["version"] == "0.1.0"

    def test_vendor_content(self):
        """Check the content of vendor directory is as expected."""
        vendor_dir = Path(self.agent_name, "vendor")
        assert vendor_dir.exists()
        assert set(vendor_dir.iterdir()) == {
            vendor_dir / "fetchai",
            vendor_dir / "__init__.py",
        }

        # assert that every subdirectory of vendor/fetchai is a Python package
        # (i.e. that contains __init__.py)
        for package_dir in (vendor_dir / "fetchai").iterdir():
            assert (package_dir / "__init__.py").exists()

    def test_vendor_connections_contains_stub_connection(self):
        """Check that the vendor connections directory contains the stub directory."""
        stub_connection_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "connections", "stub"
        )
        assert stub_connection_dirpath.exists()
        assert stub_connection_dirpath.is_dir()

    def test_stub_connection_directory_is_equal_to_library_stub_connection(self):
        """Check that the stub connection directory is equal to the package's one (aea.connections.stub)."""
        stub_connection_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "connections", "stub"
        )
        comparison = filecmp.dircmp(
            str(stub_connection_dirpath),
            str(Path(ROOT_DIR, "aea", "connections", "stub")),
        )
        assert comparison.diff_files == []

    def test_vendor_protocols_contains_default_protocol(self):
        """Check that the vendor protocols directory contains the default protocol."""
        stub_connection_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "protocols", "default"
        )
        assert stub_connection_dirpath.exists()
        assert stub_connection_dirpath.is_dir()

    def test_default_protocol_is_equal_to_library_default_protocol(self):
        """Check that the stub connection directory is equal to the package's one (aea.protocols.default)."""
        default_protocol_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "protocols", "default"
        )
        comparison = filecmp.dircmp(
            str(default_protocol_dirpath),
            str(Path(ROOT_DIR, "aea", "protocols", "default")),
        )
        assert comparison.diff_files == []

    def test_vendor_skills_contains_error_skill(self):
        """Check that the vendor skills directory contains the error skill."""
        error_skill_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "skills", "error"
        )
        assert error_skill_dirpath.exists()
        assert error_skill_dirpath.is_dir()

    def test_error_skill_is_equal_to_library_error_skill(self):
        """Check that the error skill directory is equal to the package's one (aea.skills.error)."""
        default_protocol_dirpath = Path(
            self.agent_name, "vendor", "fetchai", "skills", "error"
        )
        comparison = filecmp.dircmp(
            str(default_protocol_dirpath), str(Path(ROOT_DIR, "aea", "skills", "error"))
        )
        assert comparison.diff_files == []

    def test_protocols_directory_content(self):
        """Test the content of the 'protocols' directory."""
        dir = Path(self.t, self.agent_name, "protocols")
        assert dir.exists()
        assert dir.is_dir()
        assert set(dir.iterdir()) == {dir / "__init__.py"}

    def test_connections_directory_content(self):
        """Test the content of the 'connections' directory."""
        dir = Path(self.t, self.agent_name, "connections")
        assert dir.exists()
        assert dir.is_dir()
        assert set(dir.iterdir()) == {dir / "__init__.py"}

    def test_skills_directory_content(self):
        """Test the content of the 'skills' directory."""
        dir = Path(self.t, self.agent_name, "skills")
        assert dir.exists()
        assert dir.is_dir()
        assert set(dir.iterdir()) == {dir / "__init__.py"}

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCreateFailsWhenDirectoryAlreadyExists:
    """Test that 'aea create' sub-command fails when the directory with the agent name in input already exists."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        # create a directory with the agent name -> make 'aea create fail.
        os.mkdir(cls.agent_name)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the error code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed.

        The expected message is: 'Directory already exist. Aborting...'
        """
        s = "Directory already exist. Aborting..."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCreateFailsWhenConfigFileIsNotCompliant:
    """Test that 'aea create' sub-command fails when the generated configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"

        # change the serialization of the AgentConfig class so to make the parsing to fail.
        cls.patch = patch.object(
            aea.configurations.base.AgentConfig, "json", return_value={"hello": "world"}
        )
        cls.patch.start()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the error code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    # TODO fix this on Windows
    @skip_test_windows
    def test_agent_folder_is_not_created(self):
        """Test that the agent folder is removed."""
        assert not Path(self.agent_name).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCreateFailsWhenExceptionOccurs:
    """Test that 'aea create' sub-command fails when the generated configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"

        # change the serialization of the AgentConfig class so to make the parsing to fail.
        cls.patch = patch.object(ConfigLoader, "dump", side_effect=Exception)
        cls.patch.start()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the error code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    # TODO fix this on Windows
    @skip_test_windows
    def test_agent_folder_is_not_created(self):
        """Test that the agent folder is removed."""
        assert not Path(self.agent_name).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCreateFailsWhenAlreadyInAEAProject:
    """Test that 'aea create' sub-command fails when it is called within an AEA project."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert cls.result.exit_code == 0

        # calling 'aea create myagent' again within an AEA project - recursively.
        os.chdir(cls.agent_name)
        os.mkdir("another_subdir")
        os.chdir("another_subdir")
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the error code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed.

        The expected message is: "The current folder is already an AEA project. Please move to the parent folder.".
        """
        s = "The current folder is already an AEA project. Please move to the parent folder."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class CreateCommandTestCase(TestCase):
    """Test case for CLI create command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_create_no_init(self):
        """Test for CLI create no init result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "agent_name", "--author=some"],
            standalone_mode=False,
        )
        self.assertEqual(
            result.exception.message,
            "Author is not set up. Please use 'aea init' to initialize.",
        )

    @patch("aea.cli.create.get_or_create_cli_config", return_value={})
    def test_create_no_author_local(self, *mocks):
        """Test for CLI create no author local result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", "agent_name"],
            standalone_mode=False,
        )
        expected_message = (
            "The AEA configurations are not initialized. "
            "Uses `aea init` before continuing or provide optional argument `--author`."
        )
        self.assertEqual(result.exception.message, expected_message)
