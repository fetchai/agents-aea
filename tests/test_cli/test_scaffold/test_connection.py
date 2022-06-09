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
"""This test module contains the tests for the `aea scaffold connection` sub-command."""
import json
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import jsonschema
import yaml
from jsonschema import Draft4Validator, ValidationError

from aea.cli import cli
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE
from aea.configurations.loader import make_jsonschema_base_uri

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    CONNECTION_CONFIGURATION_SCHEMA,
    CliRunner,
    ROOT_DIR,
)


class TestScaffoldConnection:
    """Test that the command 'aea scaffold connection' works correctly in correct preconditions."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

        cls.schema = json.load(open(CONNECTION_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

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
        # scaffold connection
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0."""
        assert self.result.exit_code == 0

    def test_resource_folder_contains_module_connection(self):
        """Test that the resource folder contains scaffold connection.py module."""
        p = Path(
            self.t, self.agent_name, "connections", self.resource_name, "connection.py"
        )
        assert p.exists()

    def test_resource_folder_contains_configuration_file(self):
        """Test that the resource folder contains a good configuration file."""
        p = Path(
            self.t,
            self.agent_name,
            "connections",
            self.resource_name,
            DEFAULT_CONNECTION_CONFIG_FILE,
        )
        config_file = yaml.safe_load(open(p))
        self.validator.validate(instance=config_file)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionToRegistry:
    """Test that the command 'aea scaffold connection' works correctly in correct preconditions."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

        cls.schema = json.load(open(CONNECTION_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        dir_path.mkdir(exist_ok=True)
        # scaffold connection
        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                f"--registry-path={str(dir_path)}",
                "scaffold",
                "--to-local-registry",
                "connection",
                cls.resource_name,
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0."""
        assert self.result.exit_code == 0

    def test_resource_folder_contains_module_connection(self):
        """Test that the resource folder contains scaffold connection.py module."""
        p = Path(
            self.t,
            "packages",
            AUTHOR,
            "connections",
            self.resource_name,
            "connection.py",
        )
        assert p.exists()

    def test_resource_folder_contains_configuration_file(self):
        """Test that the resource folder contains a good configuration file."""
        p = Path(
            self.t,
            "packages",
            AUTHOR,
            "connections",
            self.resource_name,
            DEFAULT_CONNECTION_CONFIG_FILE,
        )
        config_file = yaml.safe_load(open(p))
        self.validator.validate(instance=config_file)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionWithSymlinks:
    """Test that the command 'aea scaffold connection' works correctly in correct preconditions with the `--with-symlinks` flag."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

        cls.schema = json.load(open(CONNECTION_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

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
        # scaffold connection
        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "scaffold",
                "--with-symlinks",
                "connection",
                cls.resource_name,
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0."""
        assert self.result.exit_code == 0

    def test_resource_folder_contains_module_connection(self):
        """Test that the resource folder contains scaffold connection.py module."""
        p = Path(
            self.t, self.agent_name, "connections", self.resource_name, "connection.py"
        )
        assert p.exists()

    def test_resource_folder_contains_configuration_file(self):
        """Test that the resource folder contains a good configuration file."""
        p = Path(
            self.t,
            self.agent_name,
            "connections",
            self.resource_name,
            DEFAULT_CONNECTION_CONFIG_FILE,
        )
        config_file = yaml.safe_load(open(p))
        self.validator.validate(instance=config_file)

    def test_symlinks_exist(self):
        """Test that the symlinks where created."""
        packages = "packages"
        assert os.path.islink(packages)
        assert os.readlink(packages) == "vendor"
        vendor_package = Path("vendor", AUTHOR, "connections", self.resource_name)
        non_vendor_package = Path("connections", self.resource_name)
        assert os.path.islink(vendor_package)
        assert os.readlink(str(vendor_package)) == os.path.join(
            "..", "..", "..", non_vendor_package
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea scaffold connection' fails when a folder with 'scaffold' name already."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

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
        # create a dummy 'myresource' folder
        Path(cls.t, cls.agent_name, "connections", cls.resource_name).mkdir(
            exist_ok=False, parents=True
        )
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A connection with name '{connection_name}' already exists. Aborting...'
        """
        s = "A connection with this name already exists. Please choose a different name and try again."
        assert self.result.exception.message == s

    def test_resource_directory_exists(self):
        """Test that the resource directory still exists.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert Path(self.t, self.agent_name, "connections", self.resource_name).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionFailsWhenConnectionAlreadyExists:
    """Test that the command 'aea add connection' fails when the connection already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

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
        # add connection first time
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        # scaffold connection with the same connection name
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A connection with name '{connection_name}' already exists. Aborting...'
        """
        s = "A connection with name '{}' already exists. Aborting...".format(
            self.resource_name
        )
        assert self.result.exception.message == s

    def test_resource_directory_exists(self):
        """Test that the resource directory still exists.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert Path(self.t, self.agent_name, "connections", self.resource_name).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea scaffold connection' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

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

        # change the dumping of yaml module to raise an exception.
        cls.patch = unittest.mock.patch(
            "yaml.dump", side_effect=ValidationError("test error message")
        )
        cls.patch.start()

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find connection: '{connection_name}''
        """
        s = "Error when validating the connection configuration file."
        assert self.result.exception.message == s

    def test_resource_directory_does_not_exists(self):
        """Test that the resource directory does not exist.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert not Path(
            self.t, self.agent_name, "connections", self.resource_name
        ).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestScaffoldConnectionFailsWhenExceptionOccurs:
    """Test that the command 'aea scaffold connection' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "myresource"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))

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

        cls.patch = unittest.mock.patch(
            "shutil.copytree", side_effect=Exception("unknwon exception")
        )
        cls.patch.start()

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "connection", cls.resource_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_resource_directory_does_not_exists(self):
        """Test that the resource directory does not exist.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert not Path(
            self.t, self.agent_name, "connections", self.resource_name
        ).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
