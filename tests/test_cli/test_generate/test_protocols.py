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

"""This test module contains the tests for the `aea generate protocol` sub-command."""

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
from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE
from aea.configurations.loader import make_jsonschema_base_uri

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    CUR_PATH,
    CliRunner,
    PROTOCOL_CONFIGURATION_SCHEMA,
    ROOT_DIR,
)


class TestGenerateProtocolFullMode:
    """Test that the command 'aea generate protocol' works correctly in correct preconditions."""

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
        shutil.copyfile(
            Path(CUR_PATH, "data", "sample_specification.yaml"),
            Path(cls.t, "sample_specification.yaml"),
        )
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        cls.schema = json.load(open(PROTOCOL_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        os.chdir(cls.agent_name)

        # generate protocol
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate", "protocol", cls.path_to_specification],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when generating a protocol."""
        assert self.result.exit_code == 0, "Failed with stdout='{}'".format(
            self.result.stdout
        )

    def test_resource_folder_contains_configuration_file(self):
        """Test that the protocol folder contains a structurally valid configuration file."""
        p = Path(
            self.t,
            self.agent_name,
            "protocols",
            "t_protocol",
            DEFAULT_PROTOCOL_CONFIG_FILE,
        )
        config_file = yaml.safe_load(open(p))
        self.validator.validate(instance=config_file)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestGenerateProtocolProtobufOnlyMode:
    """Test that the command 'aea generate protocol' works correctly in correct preconditions."""

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
        shutil.copyfile(
            Path(CUR_PATH, "data", "sample_specification.yaml"),
            Path(cls.t, "sample_specification.yaml"),
        )
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        cls.schema = json.load(open(PROTOCOL_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            cls.schema,
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        os.chdir(cls.agent_name)

        # generate protocol
        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "generate",
                "protocol",
                "--l",
                "cpp",
                cls.path_to_specification,
            ],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when generating a protocol."""
        assert self.result.exit_code == 0, "Failed with stdout='{}'".format(
            self.result.stdout
        )

    def test_resource_folder_contains_protobuf_schema_file(self):
        """Test that the protocol folder contains a structurally valid configuration file."""
        protobuf_schema_file = Path(
            self.t, self.agent_name, "protocols", "t_protocol", "t_protocol.proto",
        )
        cpp_header_file = Path(
            self.t, self.agent_name, "protocols", "t_protocol", "t_protocol.pb.h",
        )
        cpp_implementation_file = Path(
            self.t, self.agent_name, "protocols", "t_protocol", "t_protocol.pb.cc",
        )

        assert protobuf_schema_file.exists()
        assert cpp_header_file.exists()
        assert cpp_implementation_file.exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestGenerateProtocolFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea generate protocol' fails when a directory with the same name as the name of the protocol being generated already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.protocol_name = "t_protocol"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        shutil.copyfile(
            Path(CUR_PATH, "data", "sample_specification.yaml"),
            Path(cls.t, "sample_specification.yaml"),
        )
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        os.chdir(cls.agent_name)

        # create a dummy 'myprotocol' folder
        Path(cls.t, cls.agent_name, "protocols", cls.protocol_name).mkdir(
            exist_ok=False, parents=True
        )

        # generate protocol
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate", "protocol", cls.path_to_specification],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_protocol_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A protocol with name '{protocol_name}' already exists. Aborting...'
        """
        s = (
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + "A directory with name '{}' already exists. Aborting...".format(
                self.protocol_name
            )
        )
        assert self.result.exception.message == s

    def test_resource_directory_exists(self):
        """Test that the resource directory still exists.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert Path(self.t, self.agent_name, "protocols", self.protocol_name).exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestGenerateProtocolFailsWhenProtocolAlreadyExists:
    """Test that the command 'aea add protocol' fails when the protocol already exists."""

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
        shutil.copyfile(
            Path(CUR_PATH, "data", "sample_specification.yaml"),
            Path(cls.t, "sample_specification.yaml"),
        )
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        os.chdir(cls.agent_name)

        # generate protocol first time
        cls.generate_result_1 = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate", "protocol", cls.path_to_specification],
            standalone_mode=False,
        )

        # generate protocol second time
        cls.generate_result_2 = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "generate",
                "protocol",
                cls.path_to_specification,
            ],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_generate_protocol_first_time_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 the first time a protocol is generated."""
        assert self.generate_result_1.exit_code == 0

    def test_generate_protocol_second_time_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 the second time the protocol is generated (i.e. catchall for general errors)."""
        assert self.generate_result_2.exit_code == 1

    def test_error_message_protocol_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A protocol with name '{protocol_name}' already exists. Aborting...'
        """
        s = (
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + "A protocol with name 't_protocol' already exists. Aborting..."
        )
        assert self.generate_result_2.exception.message == s

    def test_resource_directory_exists(self):
        """Test that the resource directory still exists.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert Path(self.t, self.agent_name, "protocols", "t_protocol").exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestGenerateProtocolFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea generate protocol' fails when the configuration file is not compliant with the schema."""

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
        shutil.copyfile(
            Path(CUR_PATH, "data", "sample_specification.yaml"),
            Path(cls.t, "sample_specification.yaml"),
        )
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

        # change the dumping of yaml module to raise an exception.
        cls.patch = unittest.mock.patch(
            "yaml.dump_all", side_effect=ValidationError("test error message")
        )
        cls.patch.start()

        # generate protocol
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate", "protocol", cls.path_to_specification],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 when config file is non-compliant (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_resource_directory_does_not_exists(self):
        """Test that the resource directory does not exist.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert not Path(self.t, self.agent_name, "protocols", "t_protocol").exists()

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find protocol: '{protocol_name}'
        """
        s = "Protocol is NOT generated. The following error happened while generating the protocol:\ntest error message"
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestGenerateProtocolFailsWhenExceptionOccurs:
    """Test that the command 'aea generate protocol' fails when the configuration file is not compliant with the schema."""

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
        cls.path_to_specification = str(Path("..", "sample_specification.yaml"))

        # create an agent
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        cls.create_result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )

        # create an exception
        cls.patch = unittest.mock.patch(
            "shutil.copytree", side_effect=Exception("unknwon exception")
        )
        cls.patch.start()

        # generate protocol
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate", "protocol", cls.path_to_specification],
            standalone_mode=False,
        )
        os.chdir(cls.cwd)

    def test_create_agent_exit_code_equal_to_0(self):
        """Test that the exit code is equal to 0 when creating the agent."""
        assert self.create_result.exit_code == 0

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 when an exception is thrown (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_resource_directory_does_not_exists(self):
        """Test that the resource directory does not exist.

        This means that after every failure, we make sure we restore the previous state.
        """
        assert not Path(self.t, self.agent_name, "protocols", "t_protocol").exists()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
