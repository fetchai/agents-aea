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
import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict
from unittest.mock import patch

import jsonschema
import pytest
import yaml
from click.testing import CliRunner
from jsonschema import validate

import aea
import aea.cli.common
from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.loader import ConfigLoader
from ...conftest import AGENT_CONFIGURATION_SCHEMA, ROOT_DIR

_l = logging.getLogger("python_jsonschema_objects")
_l.setLevel(logging.CRITICAL)


class TestCreate:
    """Test that the command 'aea create <agent_name>' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        cls.result = cls.runner.invoke(cli, ["create", cls.agent_name])

    def _load_config_file(self) -> Dict:
        """Load a config file."""
        agent_config_file = Path(self.agent_name, DEFAULT_AEA_CONFIG_FILE)  # type: ignore
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
        agent_config_instance = self._load_config_file()
        agent_config_schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))

        try:
            jsonschema.validate(instance=agent_config_instance, schema=agent_config_schema)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail("Configuration file is not compliant with the schema. Exception: {}".format(str(e)))

    def test_aea_version_is_correct(self):
        """Check that the aea version in the configuration file is correct, i.e. the same of the installed package."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["aea_version"] == aea.__version__

    def test_agent_name_is_correct(self):
        """Check that the agent name in the configuration file is correct."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["agent_name"] == self.agent_name

    def test_authors_field_is_empty_string(self):
        """Check that the 'authors' field in the config file is the empty string."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["authors"] == ""

    def test_connections_contains_only_oef(self):
        """Check that the 'connections' list contains only the 'oef' connection."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["connections"] == ["oef"]

    def test_default_connection_field_is_oef(self):
        """Check that the 'default_connection' is the 'oef' connection."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["default_connection"] == "oef"

    def test_license_field_is_empty_string(self):
        """Check that the 'license' is the empty string."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["license"] == ""

    def test_private_key_pem_path_field_is_empty_string(self):
        """Check that the 'private_key_pem_path' is the empty string."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["private_key_pem_path"] == ""

    def test_protocols_field_is_empty_list(self):
        """Check that the 'protocols' field is a list with the 'default' protocol."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["protocols"] == ["default"]

    def test_skills_field_is_empty_list(self):
        """Check that the 'skills' field is a list with the 'error' skill."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["skills"] == ["error"]

    def test_url_field_is_empty_string(self):
        """Check that the 'url' field is the empty string."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["url"] == ""

    def test_version_field_is_equal_to_v1(self):
        """Check that the 'version' field is equal to the string 'v1'."""
        agent_config_instance = self._load_config_file()
        assert agent_config_instance["version"] == "v1"

    def test_connections_directory_exists(self):
        """Check that the connections directory exists."""
        connections_dirpath = Path(self.agent_name, "connections")
        assert connections_dirpath.exists()
        assert connections_dirpath.is_dir()

    def test_connections_contains_oef_connection(self):
        """Check that the connections directory contains the oef directory."""
        oef_connection_dirpath = Path(self.agent_name, "connections", "oef")
        assert oef_connection_dirpath.exists()
        assert oef_connection_dirpath.is_dir()

    def test_oef_connection_directory_is_equal_to_library_oef_connection(self):
        """Check that the oef connection directory is equal to the package's one (aea.connections.oef)."""
        oef_connection_dirpath = Path(self.agent_name, "connections", "oef")
        comparison = filecmp.dircmp(str(oef_connection_dirpath), str(Path(ROOT_DIR, "aea", "connections", "oef")))
        assert comparison.diff_files == []

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
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

        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        # create a directory with the agent name -> make 'aea create fail.
        os.mkdir(cls.agent_name)
        cls.result = cls.runner.invoke(cli, ["create", cls.agent_name])

    def test_exit_code_equal_to_minus_1(self):
        """Test that the error code is equal to -1."""
        assert self.result.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed.

        The expected message is: 'Directory already exist. Aborting...'
        """
        s = "Directory already exist. Aborting..."
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.patch.__exit__()
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
        cls.patch = patch("jsonschema.validators.Draft4Validator.validate", side_effect=Exception)
        cls.patch.__enter__()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.result = cls.runner.invoke(cli, ["create", cls.agent_name])

    def test_exit_code_equal_to_minus_1(self):
        """Test that the error code is equal to -1."""
        assert self.result.exit_code == -1

    def test_agent_folder_is_not_created(self):
        """Test that the agent folder is removed."""
        assert not Path(self.agent_name).exists()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
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
        cls.patch.__enter__()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.result = cls.runner.invoke(cli, ["create", cls.agent_name])

    def test_exit_code_equal_to_minus_1(self):
        """Test that the error code is equal to -1."""
        assert self.result.exit_code == -1

    def test_agent_folder_is_not_created(self):
        """Test that the agent folder is removed."""
        assert not Path(self.agent_name).exists()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.patch.__exit__()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
