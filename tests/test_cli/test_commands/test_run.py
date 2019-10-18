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

"""This test module contains the tests for the `aea run` sub-command."""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest.mock
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

import aea.cli.common
from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE
from ...conftest import CLI_LOG_OPTION, CUR_PATH


def test_run(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "local"])
    assert result.exit_code == 0

    process = subprocess.Popen([
        sys.executable,
        '-m',
        'aea.cli',
        "run",
        "--connection",
        "local"
    ],
        stdout=subprocess.PIPE,
        env=os.environ.copy())

    time.sleep(10.0)
    process.send_signal(signal.SIGINT)
    process.wait(timeout=20)

    assert process.returncode == 0

    os.chdir(cwd)

    poll = process.poll()
    if poll is None:
        process.terminate()
        process.wait(2)

    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_with_install_deps(pytestconfig):
    """Test that the command 'aea run --install-deps' does not crash."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "local"])
    assert result.exit_code == 0

    process = subprocess.Popen([
        sys.executable,
        '-m',
        'aea.cli',
        "run",
        "--install-deps",
        "--connection",
        "local"
    ],
        stdout=subprocess.PIPE,
        env=os.environ.copy())

    time.sleep(10.0)
    process.send_signal(signal.SIGINT)
    process.communicate(timeout=20)

    assert process.returncode == 0

    poll = process.poll()
    if poll is None:
        process.terminate()
        process.wait(2)

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_with_install_deps_and_requirement_file(pytestconfig):
    """Test that the command 'aea run --install-deps' with requirement file does not crash."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "local"])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "freeze"])
    assert result.exit_code == 0
    Path(t, agent_name, "requirements.txt").write_text(result.output)

    process = subprocess.Popen([
        sys.executable,
        '-m',
        'aea.cli',
        "run",
        "--install-deps",
        "--connection",
        "local"
    ],
        stdout=subprocess.PIPE,
        env=os.environ.copy())

    time.sleep(10.0)
    process.send_signal(signal.SIGINT)
    process.wait(timeout=20)

    assert process.returncode == 0

    poll = process.poll()
    if poll is None:
        process.terminate()
        process.wait(10)

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


class TestRunFailsWhenExceptionOccursInSkill:
    """Test that the command 'aea run' fails when an exception occurs in any skill."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "local"])
        assert result.exit_code == 0

        shutil.copytree(Path(CUR_PATH, "data", "exception_skill"), Path(cls.t, cls.agent_name, "skills", "exception"))
        config_path = Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("exception")
        yaml.safe_dump(config, open(config_path, "w"))

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", "local"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRunFailsWhenConfigurationFileNotFound:
    """Test that the command 'aea run' fails when the agent configuration file is not found in the current directory."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).unlink()

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main([*CLI_LOG_OPTION, "run"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' not found in the current directory.".format(DEFAULT_AEA_CONFIG_FILE)
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


class TestRunFailsWhenConfigurationFileInvalid:
    """Test that the command 'aea run' fails when the agent configuration file is invalid."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0

        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).write_text("")

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main([*CLI_LOG_OPTION, "run"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' is invalid. Please check the documentation.".format(DEFAULT_AEA_CONFIG_FILE)
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


class TestRunFailsWhenConnectionNotDeclared:
    """Test that the command 'aea run --connection' fails when the connection is not declared."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "unknown_connection"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection name '{}' not declared in the configuration file.".format(self.connection_name)
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


class TestRunFailsWhenConnectionConfigFileNotFound:
    """Test that the command 'aea run --connection' fails when the connection config file is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "myconnection"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "scaffold", "connection", cls.connection_name])
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, "connections", cls.connection_name, DEFAULT_CONNECTION_CONFIG_FILE).unlink()

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection config for '{}' not found.".format(self.connection_name)
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


class TestRunFailsWhenConnectionNotComplete:
    """Test that the command 'aea run --connection' fails when the connection.py module is missing."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "stub"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", cls.connection_name])
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, "connections", cls.connection_name, "connection.py").unlink()

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection '{}' not found.".format(self.connection_name)
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


class TestRunFailsWhenConnectionClassNotPresent:
    """Test that the command 'aea run --connection' fails when the connection class is missing in connection.py."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "stub"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", cls.connection_name])
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, "connections", cls.connection_name, "connection.py").write_text("")

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection class '{}' not found.".format("StubConnection")
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


class TestRunFailsWhenProtocolConfigFileNotFound:
    """Test that the command 'aea run' fails when a protocol configuration file is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "local"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        Path(cls.t, cls.agent_name, "protocols", "default", "protocol.yaml").unlink()

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Protocol configuration file for protocol {} not found.".format("default")
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


class TestRunFailsWhenProtocolNotComplete:
    """Test that the command 'aea run' fails when a protocol directory is not complete."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_name = "local"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        Path(cls.t, cls.agent_name, "protocols", "default", "__init__.py").unlink()

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connection", cls.connection_name])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_minus_one(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.exit_code == -1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "A problem occurred while processing protocol {}.".format("default")
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
