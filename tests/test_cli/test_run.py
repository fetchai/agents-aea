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
import subprocess  # nosec
import sys
import tempfile
import time
from pathlib import Path
from unittest import TestCase, mock

from click import ClickException

import pytest

import yaml

from aea.cli import cli
from aea.cli.run import _build_aea, run_aea
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    PublicId,
)
from aea.configurations.constants import DEFAULT_CONNECTION
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE
from aea.exceptions import AEAPackageLoadingError
from aea.helpers.base import sigint_crossplatform

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import AUTHOR, CLI_LOG_OPTION, CliRunner, MAX_FLAKY_RERUNS, ROOT_DIR


if sys.platform.startswith("win"):
    pytest.skip("skipping tests on Windows", allow_module_level=True)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_run():
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            "fetchai/http_client:0.5.0",
        ],
    )
    assert result.exit_code == 0

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run"],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        sigint_crossplatform(process)
        process.wait(timeout=20)

        assert process.returncode == 0

    finally:
        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        os.chdir(cwd)
        try:
            shutil.rmtree(t)
        except (OSError, IOError):
            pass


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_run_with_default_connection():
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run"],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        sigint_crossplatform(process)
        process.wait(timeout=20)

        assert process.returncode == 0

    finally:
        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        os.chdir(cwd)
        try:
            shutil.rmtree(t)
        except (OSError, IOError):
            pass


@pytest.mark.parametrize(
    argnames=["connection_ids"],
    argvalues=[
        ["fetchai/http_client:0.5.0,{}".format(str(DEFAULT_CONNECTION))],
        ["'fetchai/http_client:0.5.0, {}'".format(str(DEFAULT_CONNECTION))],
        ["fetchai/http_client:0.5.0,,{},".format(str(DEFAULT_CONNECTION))],
    ],
)
def test_run_multiple_connections(connection_ids):
    """Test that the command 'aea run' works as expected when specifying multiple connections."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0

    # stub is the default connection, so it should fail
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "--local", "connection", str(DEFAULT_CONNECTION)]
    )
    assert result.exit_code == 1

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run", "--connections", connection_ids],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(5.0)
        sigint_crossplatform(process)
        process.wait(timeout=5)

        assert process.returncode == 0

    finally:
        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        os.chdir(cwd)
        try:
            shutil.rmtree(t)
        except (OSError, IOError):
            pass


def test_run_unknown_private_key():
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            "fetchai/http_client:0.5.0",
        ],
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    find_text = "private_key_paths: {}"
    replace_text = """private_key_paths:
        fetchai_not: fet_private_key.txt"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    # Private key needs to exist otherwise doesn't get to code path we are interested in testing
    with open(FETCHAI_PRIVATE_KEY_FILE, "w") as f:
        f.write("3801d3703a1fcef18f6bf393fba89245f36b175f4989d8d6e026300dad21e05d")

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "run", "--connections", "fetchai/http_client:0.5.0"],
        standalone_mode=False,
    )

    s = "Item not registered with id 'fetchai_not'."
    assert result.exception.message == s

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_fet_private_key_config():
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    find_text = "private_key_paths: {}"
    replace_text = """private_key_paths:
    fetchai: default_private_key_not.txt"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    error_msg = ""
    try:
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/http_client:0.5.0"])
    except SystemExit as e:
        error_msg = str(e)

    assert error_msg == "1"

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_ethereum_private_key_config():
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    find_text = "private_key_paths: {}"
    replace_text = """private_key_paths:
    ethereum: default_private_key_not.txt"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    error_msg = ""
    try:
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/http_client:0.5.0"])
    except SystemExit as e:
        error_msg = str(e)

    assert error_msg == "1"

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # install depends on network
def test_run_with_install_deps():
    """Test that the command 'aea run --install-deps' does not crash."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    packages_src = os.path.join(ROOT_DIR, "packages")
    packages_dst = os.path.join(t, "packages")
    shutil.copytree(packages_src, packages_dst)

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            "fetchai/http_client:0.5.0",
        ],
    )
    assert result.exit_code == 0

    try:
        process = PexpectWrapper(
            [
                sys.executable,
                "-m",
                "aea.cli",
                "-v",
                "DEBUG",
                "run",
                "--install-deps",
                "--connections",
                "fetchai/http_client:0.5.0",
            ],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )
        process.expect_all(["Start processing messages..."], timeout=30)
        time.sleep(1.0)
        process.control_c()
        process.wait_to_complete(10)
        assert process.returncode == 0

    finally:
        process.terminate()
        process.wait_to_complete(10)
        os.chdir(cwd)
        try:
            shutil.rmtree(t)
        except (OSError, IOError):
            pass


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # install depends on network
def test_run_with_install_deps_and_requirement_file():
    """Test that the command 'aea run --install-deps' with requirement file does not crash."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/http_client:0.5.0"],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            "fetchai/http_client:0.5.0",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "freeze"])
    assert result.exit_code == 0
    Path(t, agent_name, "requirements.txt").write_text(result.output)

    try:
        process = PexpectWrapper(
            [
                sys.executable,
                "-m",
                "aea.cli",
                "-v",
                "DEBUG",
                "run",
                "--install-deps",
                "--connections",
                "fetchai/http_client:0.5.0",
            ],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )
        process.expect_all(["Start processing messages..."], timeout=30)
        time.sleep(1.0)
        process.control_c()
        process.wait_to_complete(10)
        assert process.returncode == 0

    finally:
        process.terminate()
        process.wait_to_complete(10)
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
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "connection",
                "fetchai/http_client:0.5.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        shutil.copytree(
            Path(ROOT_DIR, "tests", "data", "exception_skill"),
            Path(cls.t, cls.agent_name, "vendor", "fetchai", "skills", "exception"),
        )
        config_path = Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))

        try:
            cli.main(
                [*CLI_LOG_OPTION, "run", "--connections", "fetchai/http_client:0.5.0"]
            )
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).unlink()

        os.chdir(Path(cls.t, cls.agent_name))

        cls.result = cls.runner.invoke(
            cli,
            ["--skip-consistency-check", *CLI_LOG_OPTION, "run"],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' not found in the current directory.".format(
            DEFAULT_AEA_CONFIG_FILE
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).write_text("")

        os.chdir(Path(cls.t, cls.agent_name))

        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "run"], standalone_mode=False
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' is invalid. Please check the documentation.".format(
            DEFAULT_AEA_CONFIG_FILE
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRunFailsWhenConnectionNotDeclared:
    """Test that the command 'aea run --connections' fails when the connection is not declared."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = "author/unknown_connection:0.1.0"
        cls.connection_name = "unknown_connection"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "run", "--connections", cls.connection_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection ids ['{}'] not declared in the configuration file.".format(
            self.connection_id
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRunFailsWhenConnectionConfigFileNotFound:
    """Test that the command 'aea run --connections' fails when the connection config file is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = PublicId.from_str("fetchai/http_client:0.5.0")
        cls.connection_name = cls.connection_id.name
        cls.connection_author = cls.connection_id.author
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", str(cls.connection_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/http_client:0.5.0",
            ],
        )
        assert result.exit_code == 0
        cls.connection_configuration_path = Path(
            cls.t,
            cls.agent_name,
            "vendor",
            cls.connection_author,
            "connections",
            cls.connection_name,
            DEFAULT_CONNECTION_CONFIG_FILE,
        )
        cls.connection_configuration_path.unlink()
        cls.relative_connection_configuration_path = cls.connection_configuration_path.relative_to(
            Path(cls.t, cls.agent_name)
        )

        cls.result = cls.runner.invoke(
            cli,
            [
                "--skip-consistency-check",
                *CLI_LOG_OPTION,
                "run",
                "--connections",
                str(cls.connection_id),
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection configuration not found: {}".format(
            self.relative_connection_configuration_path
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRunFailsWhenConnectionNotComplete:
    """Test that the command 'aea run --connections' fails when the connection.py module is missing."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = PublicId.from_str("fetchai/http_client:0.5.0")
        cls.connection_author = cls.connection_id.author
        cls.connection_name = cls.connection_id.name
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", str(cls.connection_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/http_client:0.5.0",
            ],
        )
        assert result.exit_code == 0
        connection_module_path = Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "connections",
            cls.connection_name,
            "connection.py",
        )
        connection_module_path.unlink()
        cls.relative_connection_module_path = connection_module_path.relative_to(
            Path(cls.t, cls.agent_name)
        )
        cls.result = cls.runner.invoke(
            cli,
            [
                "--skip-consistency-check",
                *CLI_LOG_OPTION,
                "run",
                "--connections",
                str(cls.connection_id),
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "An error occurred while loading connection {}: Connection module '{}' not found.".format(
            self.connection_id, self.relative_connection_module_path
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRunFailsWhenConnectionClassNotPresent:
    """Test that the command 'aea run --connections' fails when the connection class is missing in connection.py."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = "fetchai/http_client:0.5.0"
        cls.connection_name = "http_client"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/http_client:0.5.0",
            ],
        )
        assert result.exit_code == 0
        Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "connections",
            cls.connection_name,
            "connection.py",
        ).write_text("")

        cls.result = cls.runner.invoke(
            cli,
            [
                "--skip-consistency-check",
                *CLI_LOG_OPTION,
                "run",
                "--connections",
                cls.connection_id,
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "An error occurred while loading connection {}: Connection class '{}' not found.".format(
            self.connection_id, "HTTPClientConnection"
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.connection_id = str(DEFAULT_CONNECTION)
        cls.connection_name = "stub"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))

        configuration_file_path = Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "protocols",
            "default",
            "protocol.yaml",
        )

        configuration_file_path.unlink()
        cls.relative_configuration_file_path = configuration_file_path.relative_to(
            Path(cls.t, cls.agent_name)
        )

        cls.result = cls.runner.invoke(
            cli,
            [
                "--skip-consistency-check",
                *CLI_LOG_OPTION,
                "run",
                "--connections",
                cls.connection_id,
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Protocol configuration not found: {}".format(
            self.relative_configuration_file_path
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        os.chdir(os.path.join(cls.t, cls.agent_name))

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "protocol", "fetchai/fipa:0.4.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # remove protocol configuration
        configuration_path = Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "protocols",
            "fipa",
            "protocol.yaml",
        )
        configuration_path.unlink()
        cls.relative_configuration_file_path = configuration_path.relative_to(
            Path(cls.t, cls.agent_name)
        )

        cls.result = cls.runner.invoke(
            cli,
            ["--skip-consistency-check", *CLI_LOG_OPTION, "run"],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Protocol configuration not found: {}".format(
            self.relative_configuration_file_path
        )
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


def _raise_click_exception(*args, **kwargs):
    raise ClickException("message")


class RunAEATestCase(TestCase):
    """Test case for run_aea method."""

    @mock.patch("aea.cli.run._prepare_environment", _raise_click_exception)
    def test_run_aea_negative(self, *mocks):
        """Test run_aea method for negative result."""
        ctx = mock.Mock()
        ctx.config = {"skip_consistency_check": True}
        with self.assertRaises(ClickException):
            run_aea(ctx, ["author/name:0.1.0"], "env_file", False)


def _raise_aea_package_loading_error(*args, **kwargs):
    raise AEAPackageLoadingError()


@mock.patch("aea.cli.run.AEABuilder.from_aea_project", _raise_aea_package_loading_error)
class BuildAEATestCase(TestCase):
    """Test case for run_aea method."""

    def test__build_aea_negative(self, *mocks):
        """Test _build_aea method for negative result."""
        with self.assertRaises(ClickException):
            _build_aea(connection_ids=[], skip_consistency_check=True)
