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
import subprocess  # nosec
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

import yaml

import aea.cli.common
from aea.cli import cli
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    PublicId,
)

from ..common.click_testing import CliRunner
from ..conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH


def test_run(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run"],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
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


def test_run_with_default_connection(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run"],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
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
        ["fetchai/local:0.1.0,fetchai/stub:0.1.0"],
        ["'fetchai/local:0.1.0, fetchai/stub:0.1.0'"],
        ["fetchai/local:0.1.0,,fetchai/stub:0.1.0,"],
    ],
)
def test_run_multiple_connections(pytestconfig, connection_ids):
    """Test that the command 'aea run' works as expected when specifying multiple connections."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    # stub is the default connection, so it should fail
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/stub:0.1.0"]
    )
    assert result.exit_code == 1

    try:
        process = subprocess.Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "run", "--connections", connection_ids],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(5.0)
        process.send_signal(signal.SIGINT)
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


def test_run_unknown_private_key(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    patch = mock.patch.object(aea.cli.common.logger, "error")
    mocked_logger_error = patch.__enter__()
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    find_text = "private_key_paths: {}"
    replace_text = """private_key_paths:
        fetchai-not: fet_private_key.txt"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    # Private key needs to exist otherwise doesn't get to code path we are interested in testing
    with open("fet_private_key.txt", "w") as f:
        f.write("3801d3703a1fcef18f6bf393fba89245f36b175f4989d8d6e026300dad21e05d")

    try:
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/local:0.1.0"])
    except SystemExit:
        pass

    mocked_logger_error.assert_called_with(
        "Unsupported identifier in private key paths."
    )

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_unknown_ledger(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    patch = mock.patch.object(aea.cli.common.logger, "error")
    mocked_logger_error = patch.__enter__()
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    # add in the ledger address
    find_text = "ledger_apis: {}"
    replace_text = """ledger_apis:
    unknown:
        address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
        chain_id: 3
        gas_price: 20"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    try:
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/local:0.1.0"])
    except SystemExit:
        pass

    mocked_logger_error.assert_called_with("Unsupported identifier in ledger apis.")

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_fet_private_key_config(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
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
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/local:0.1.0"])
    except SystemExit as e:
        error_msg = str(e)

    assert error_msg == "1"

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_ethereum_private_key_config(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
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
        cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/local:0.1.0"])
    except SystemExit as e:
        error_msg = str(e)

    assert error_msg == "1"

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


def test_run_ledger_apis(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    # add in the ledger address
    find_text = "ledger_apis: {}"
    replace_text = """ledger_apis:
    ethereum:
        address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
        chain_id: 3
        gas_price: 20
    fetchai:
        network: testnet"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    try:
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--connections",
                "fetchai/local:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
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


def test_run_fet_ledger_apis(pytestconfig):
    """Test that the command 'aea run' works as expected."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    # add in the ledger address

    find_text = "ledger_apis: {}"
    replace_text = """ledger_apis:
    fetchai:
        network: testnet"""

    whole_file = whole_file.replace(find_text, replace_text)

    # close the file
    file.close()

    with open("aea-config.yaml", "w") as f:
        f.write(whole_file)

    try:
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--connections",
                "fetchai/local:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
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


def test_run_with_install_deps(pytestconfig):
    """Test that the command 'aea run --install-deps' does not crash."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    packages_src = os.path.join(cwd, "packages")
    packages_dst = os.path.join(t, "packages")
    shutil.copytree(packages_src, packages_dst)

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    try:
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--install-deps",
                "--connections",
                "fetchai/local:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
        process.communicate(timeout=20)

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


def test_run_with_install_deps_and_requirement_file(pytestconfig):
    """Test that the command 'aea run --install-deps' with requirement file does not crash."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"]
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "freeze"])
    assert result.exit_code == 0
    Path(t, agent_name, "requirements.txt").write_text(result.output)

    try:
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--install-deps",
                "--connections",
                "fetchai/local:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
        process.wait(timeout=20)

        assert process.returncode == 0

    finally:
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
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "connection", "fetchai/local:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        shutil.copytree(
            Path(CUR_PATH, "data", "exception_skill"),
            Path(cls.t, cls.agent_name, "vendor", "fetchai", "skills", "exception"),
        )
        config_path = Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connections", "fetchai/local:0.1.0"])
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
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0
        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).unlink()

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main(["--skip-consistency-check", *CLI_LOG_OPTION, "run"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' not found in the current directory.".format(
            DEFAULT_AEA_CONFIG_FILE
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0

        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).write_text("")

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main([*CLI_LOG_OPTION, "run"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Agent configuration file '{}' is invalid. Please check the documentation.".format(
            DEFAULT_AEA_CONFIG_FILE
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.__exit__()
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
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))

        try:
            cli.main([*CLI_LOG_OPTION, "run", "--connections", cls.connection_id])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection ids ['{}'] not declared in the configuration file.".format(
            self.connection_id
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.__exit__()
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
        cls.connection_id = PublicId.from_str("fetchai/local:0.1.0")
        cls.connection_name = cls.connection_id.name
        cls.connection_author = cls.connection_id.author
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "connection", str(cls.connection_id)],
            standalone_mode=False,
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

        try:
            cli.main(
                [
                    "--skip-consistency-check",
                    *CLI_LOG_OPTION,
                    "run",
                    "--connections",
                    str(cls.connection_id),
                ]
            )
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection configuration not found: {}".format(
            self.relative_connection_configuration_path
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.__exit__()
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
        cls.connection_id = PublicId.from_str("fetchai/local:0.1.0")
        cls.connection_author = cls.connection_id.author
        cls.connection_name = cls.connection_id.name
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "connection", str(cls.connection_id)],
            standalone_mode=False,
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

        try:
            cli.main(
                [
                    "--skip-consistency-check",
                    *CLI_LOG_OPTION,
                    "run",
                    "--connections",
                    str(cls.connection_id),
                ]
            )
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection module '{}' not found.".format(
            self.relative_connection_module_path
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.__exit__()
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
        cls.connection_id = "fetchai/local:0.1.0"
        cls.connection_name = "local"
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0
        os.chdir(Path(cls.t, cls.agent_name))
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "connection", cls.connection_id],
            standalone_mode=False,
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

        try:
            cli.main(
                [
                    "--skip-consistency-check",
                    *CLI_LOG_OPTION,
                    "run",
                    "--connections",
                    cls.connection_id,
                ]
            )
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Connection class '{}' not found.".format("OEFLocalConnection")
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
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
        cls.connection_id = "fetchai/stub:0.1.0"
        cls.connection_name = "local"
        cls.patch = mock.patch.object(aea.cli.common.logger, "error")
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
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

        try:
            cli.main(
                [
                    "--skip-consistency-check",
                    *CLI_LOG_OPTION,
                    "run",
                    "--connections",
                    cls.connection_id,
                ]
            )
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = "Protocol configuration not found: {}".format(
            self.relative_configuration_file_path
        )
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.__exit__()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


# class TestRunFailsWhenProtocolNotComplete:
#     """Test that the command 'aea run' fails when a protocol directory is not complete."""
#
#     @classmethod
#     def setup_class(cls):
#         """Set the test up."""
#         cls.runner = CliRunner()
#         cls.agent_name = "myagent"
#         cls.connection_id = "fetchai/local:0.1.0"
#         cls.connection_name = "local"
#         cls.patch = mock.patch.object(aea.cli.common.logger, "error")
#         cls.mocked_logger_error = cls.patch.__enter__()
#         cls.cwd = os.getcwd()
#         cls.t = tempfile.mkdtemp()
#         # copy the 'packages' directory in the parent of the agent folder.
#         shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))
#
#         os.chdir(cls.t)
#         result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
#         assert result.exit_code == 0
#
#         result = cls.runner.invoke(
#             cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
#
#         try:
#             cli.main(
#                 [
#                     "--skip-consistency-check",
#                     *CLI_LOG_OPTION,
#                     "run",
#                     "--connections",
#                     cls.connection_id,
#                 ]
#             )
#         except SystemExit as e:
#             cls.exit_code = e.code
#
#     def test_exit_code_equal_to_1(self):
#         """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
#         assert self.exit_code == 1
#
#     def test_log_error_message(self):
#         """Test that the log error message is fixed."""
#         s = "Protocol configuration not found: {}".format(
#             self.relative_configuration_file_path
#         )
#         self.mocked_logger_error.assert_called_once_with(s)
#
#     @classmethod
#     def teardown_class(cls):
#         """Tear the test down."""
#         cls.patch.__exit__()
#         os.chdir(cls.cwd)
#         try:
#             shutil.rmtree(cls.t)
#         except (OSError, IOError):
#             pass
