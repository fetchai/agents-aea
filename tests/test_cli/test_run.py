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
"""This test module contains the tests for the `aea run` sub-command."""
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import patch

import pytest
import yaml
from aea_ledger_fetchai import FetchAICrypto
from aea_ledger_fetchai.test_tools.constants import FETCHAI_PRIVATE_KEY_FILE
from click import ClickException
from pexpect.exceptions import EOF  # type: ignore

from aea.cli import cli
from aea.cli.run import _build_aea, run_aea
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
)
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.exceptions import AEAPackageLoadingError
from aea.test_tools.test_cases import AEATestCaseEmpty, _get_password_option_args

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_ClIENT_PUBLIC_ID,
)
from packages.fetchai.connections.stub.connection import (
    PUBLIC_ID as STUB_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.fipa.message import FipaMessage

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import AUTHOR, CLI_LOG_OPTION, CliRunner, MAX_FLAKY_RERUNS, ROOT_DIR


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_run(password_or_none):
    """Test that the command 'aea run' works as expected."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))
    password_options = _get_password_option_args(password_or_none)

    os.chdir(t)
    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier, *password_options],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
            *password_options,
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_ledger",
            FetchAICrypto.identifier,
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            "--type",
            "list",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            str(HTTP_ClIENT_PUBLIC_ID),
        ],
    )
    assert result.exit_code == 0

    try:
        process = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "run", *password_options],
            env=os.environ.copy(),
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        process.expect("Start processing messages", timeout=10)
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


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # flaky on Windows
def test_run_with_profiling():
    """Test profiling data showed."""
    runner = CliRunner()
    agent_name = "myagent"
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    # copy the 'packages' directory in the parent of the agent folder.
    shutil.copytree(Path(ROOT_DIR, "packages"), Path(t, "packages"))

    os.chdir(t)
    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_ledger",
            FetchAICrypto.identifier,
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            "--type",
            "list",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            str(HTTP_ClIENT_PUBLIC_ID),
        ],
    )
    assert result.exit_code == 0

    try:
        process = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "run", "--profiling", "1"],
            env=os.environ.copy(),
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        process.expect("Start processing messages", timeout=10)
        process.expect("Profiling details", timeout=10)
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


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_ledger",
            FetchAICrypto.identifier,
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            "--type",
            "list",
        ],
    )
    assert result.exit_code == 0

    try:
        process = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "run"],
            env=os.environ.copy(),
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        process.expect("Start processing messages", timeout=10)
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


@pytest.mark.skip  # need remote registry
@pytest.mark.parametrize(
    argnames=["connection_ids"],
    argvalues=[
        [f"{str(HTTP_ClIENT_PUBLIC_ID)},{str(STUB_CONNECTION_PUBLIC_ID)}"],
        [f"'{str(HTTP_ClIENT_PUBLIC_ID)}, {str(STUB_CONNECTION_PUBLIC_ID)}'"],
        [f"{str(HTTP_ClIENT_PUBLIC_ID)},,{str(STUB_CONNECTION_PUBLIC_ID)},"],
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add",
            "--local",
            "connection",
            str(STUB_CONNECTION_PUBLIC_ID),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0

    # stub is the default connection, so it should fail
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add",
            "--local",
            "connection",
            str(STUB_CONNECTION_PUBLIC_ID),
        ],
    )
    assert result.exit_code == 1
    process = PexpectWrapper(  # nosec
        [sys.executable, "-m", "aea.cli", "run", "--connections", connection_ids],
        env=os.environ,
        maxread=10000,
        encoding="utf-8",
        logfile=sys.stdout,
    )

    try:
        process.expect_all(["Start processing messages"], timeout=40)
        process.control_c()
        process.expect(
            EOF,
            timeout=40,
        )
        process.wait_to_complete(15)
        assert process.returncode == 0
    finally:
        process.wait_to_complete(15)
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            str(HTTP_ClIENT_PUBLIC_ID),
        ],
    )
    assert result.exit_code == 0

    # Load the agent yaml file and manually insert the things we need
    file = open("aea-config.yaml", mode="r")

    # read all lines at once
    whole_file = file.read()

    find_text = "private_key_paths: {}"
    replace_text = """private_key_paths:
        fetchai_not: fetchai_private_key.txt"""

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
        [*CLI_LOG_OPTION, "run", "--connections", str(HTTP_ClIENT_PUBLIC_ID)],
        standalone_mode=False,
    )

    s = (
        "Unsupported identifier `fetchai_not` in private key paths. Supported identifiers: ['cosmos', 'ethereum', "
        "'fetchai']."
    )
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
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
        cli.main([*CLI_LOG_OPTION, "run", "--connections", str(HTTP_ClIENT_PUBLIC_ID)])
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
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
        cli.main([*CLI_LOG_OPTION, "run", "--connections", str(HTTP_ClIENT_PUBLIC_ID)])
    except SystemExit as e:
        error_msg = str(e)

    assert error_msg == "1"

    os.chdir(cwd)
    try:
        shutil.rmtree(t)
    except (OSError, IOError):
        pass


@pytest.mark.skip  # need remote registry
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            str(HTTP_ClIENT_PUBLIC_ID),
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
                str(HTTP_ClIENT_PUBLIC_ID),
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
        cli,
        [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, [*CLI_LOG_OPTION, "create", "--local", agent_name])
    assert result.exit_code == 0

    os.chdir(Path(t, agent_name))

    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "generate-key", FetchAICrypto.identifier]
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "add-key",
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_ledger",
            FetchAICrypto.identifier,
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            "--type",
            "list",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        [*CLI_LOG_OPTION, "add", "--local", "connection", str(HTTP_ClIENT_PUBLIC_ID)],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "config",
            "set",
            "agent.default_connection",
            str(HTTP_ClIENT_PUBLIC_ID),
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
                str(HTTP_ClIENT_PUBLIC_ID),
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

        os.chdir(Path(cls.t, cls.agent_name))

        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "connection",
                str(HTTP_ClIENT_PUBLIC_ID),
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
                [*CLI_LOG_OPTION, "run", "--connections", str(HTTP_ClIENT_PUBLIC_ID)]
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


class TestRunFailsWhenConfigurationFileIsEmpty:
    """Test that the command 'aea run' fails when the agent configuration file is empty."""

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
        s = "Agent configuration file was empty."
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

        Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE).write_text(
            "invalid_attribute: 'foo'\n"
        )

        os.chdir(Path(cls.t, cls.agent_name))

        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "run"], standalone_mode=False
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed."""
        s = (
            "Agent configuration file '{}' is invalid: `ExtraPropertiesError: properties not expected: "
            "invalid_attribute`. Please check the documentation.".format(
                DEFAULT_AEA_CONFIG_FILE
            )
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


class TestRunFailsWhenConnectionNotDeclared(AEATestCaseEmpty):
    """Test that the command 'aea run --connections' fails when the connection is not declared."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.connection_id = "author/unknown_connection:0.1.0"
        cls.connection_name = "unknown_connection"
        cls.generate_private_key(FetchAICrypto.identifier)
        cls.add_private_key(
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        )
        cls.set_config("agent.default_ledger", FetchAICrypto.identifier)
        cls.set_config(
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            type_="list",
        )

    def test_run(self):
        """Run the test."""
        expected_message = f"Connection ids ['{self.connection_id}'] not declared in the configuration file."
        with pytest.raises(ClickException, match=re.escape(expected_message)):
            self.run_cli_command(
                "run", "--connections", str(self.connection_id), cwd=self._get_cwd()
            )


class TestRunFailsWhenConnectionConfigFileNotFound:
    """Test that the command 'aea run --connections' fails when the connection config file is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = HTTP_ClIENT_PUBLIC_ID
        cls.connection_name = cls.connection_id.name
        cls.connection_author = cls.connection_id.author
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

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
                str(HTTP_ClIENT_PUBLIC_ID),
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
        cls.relative_connection_configuration_path = (
            cls.connection_configuration_path.relative_to(Path(cls.t, cls.agent_name))
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


class TestRunFailsWhenConnectionNotComplete(AEATestCaseEmpty):
    """Test that the command 'aea run --connections' fails when the connection.py module is missing."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.connection_id = HTTP_ClIENT_PUBLIC_ID
        cls.connection_author = cls.connection_id.author
        cls.connection_name = cls.connection_id.name
        cls.generate_private_key(FetchAICrypto.identifier)
        cls.add_private_key(
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        )
        cls.add_item("connection", str(cls.connection_id))
        cls.set_config("agent.default_ledger", FetchAICrypto.identifier)
        cls.set_config(
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            type_="list",
        )
        cls.set_config("agent.default_connection", str(HTTP_ClIENT_PUBLIC_ID))
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

    def test_run(self):
        """Run the test."""
        expected_message = (
            "Package loading error: An error occurred while loading connection {}: Connection module "
            "'{}' not found.".format(
                self.connection_id, self.relative_connection_module_path
            )
        )
        with pytest.raises(ClickException, match=re.escape(expected_message)):
            self.run_cli_command(
                "--skip-consistency-check",
                "run",
                "--connections",
                str(self.connection_id),
                cwd=self._get_cwd(),
            )


class TestRunFailsWhenConnectionClassNotPresent(AEATestCaseEmpty):
    """Test that the command 'aea run --connections' fails when the connection is not declared."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.connection_id = str(HTTP_ClIENT_PUBLIC_ID)
        cls.connection_name = "http_client"
        cls.generate_private_key(FetchAICrypto.identifier)
        cls.add_private_key(
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        )
        cls.add_item("connection", cls.connection_id)
        cls.set_config("agent.default_ledger", FetchAICrypto.identifier)
        cls.set_config(
            "agent.required_ledgers",
            json.dumps([FetchAICrypto.identifier]),
            type_="list",
        )
        cls.set_config("agent.default_connection", cls.connection_id)
        Path(
            cls.t,
            cls.agent_name,
            "vendor",
            "fetchai",
            "connections",
            cls.connection_name,
            "connection.py",
            # preserve import statement so to make the check of unused packages to pass
        ).write_text("import packages.fetchai.protocols.http")

    def test_run(self):
        """Run the test."""
        expected_message = (
            "Package loading error: An error occurred while loading connection {}: Connection class '{"
            "}' not found.".format(self.connection_id, "HTTPClientConnection")
        )
        with pytest.raises(ClickException, match=expected_message):
            self.run_cli_command(
                "--skip-consistency-check",
                "run",
                "--connections",
                self.connection_id,
                cwd=self._get_cwd(),
            )


@pytest.mark.skip  # need remote registry
class TestRunFailsWhenProtocolConfigFileNotFound:
    """Test that the command 'aea run' fails when a protocol configuration file is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.connection_id = str(STUB_CONNECTION_PUBLIC_ID)
        cls.connection_name = "stub"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

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

        os.chdir(os.path.join(cls.t, cls.agent_name))

        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "protocol",
                str(FipaMessage.protocol_id),
            ],
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

    def test_run_aea_positive_mock(self):
        """Test run_aea method for positive result (mocked)."""
        ctx = mock.Mock()
        aea = mock.Mock()

        aea.context.addresses = {}
        aea.resources.component_registry.fetch_by_type = lambda _: []

        ctx.config = {"skip_consistency_check": True}
        with tempfile.TemporaryDirectory() as temp_dir:
            ctx.cwd = str(temp_dir)
            with mock.patch("aea.cli.run._build_aea", return_value=aea), mock.patch(
                "aea.cli.run.list_available_packages", return_value=[]
            ):
                run_aea(ctx, ["author/name:0.1.0"], "env_file", False)

    def test_run_aea_positive_install_deps_mock(self):
        """Test run_aea method for positive result (mocked), install deps true."""
        ctx = mock.Mock()
        aea = mock.Mock()
        ctx.config = {"skip_consistency_check": True}

        aea.context.addresses = {}
        aea.resources.component_registry.fetch_by_type = lambda _: []

        with tempfile.TemporaryDirectory() as temp_dir:
            ctx.cwd = str(temp_dir)
            with mock.patch("aea.cli.run.do_install"):
                with mock.patch("aea.cli.run._build_aea", return_value=aea), mock.patch(
                    "aea.cli.run.list_available_packages", return_value=[]
                ):
                    run_aea(ctx, ["author/name:0.1.0"], "env_file", True)

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


class TestExcludeConnection(AEATestCaseEmpty):
    """Test that the command 'aea run --connections' fails when the connection is not declared."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.connection_id = str(HTTP_ClIENT_PUBLIC_ID)
        cls.connection2_id = str(STUB_CONNECTION_PUBLIC_ID)
        cls.generate_private_key(FetchAICrypto.identifier)
        cls.add_private_key(
            FetchAICrypto.identifier,
            PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier),
        )
        cls.add_item("connection", cls.connection_id)
        cls.add_item("connection", cls.connection2_id)

    def test_connection_excluded(self):
        """Test connection excluded."""

        def raise_err(*args):
            raise Exception(args[1])

        with pytest.raises(Exception, match="^None$"):
            with patch("aea.cli.run.run_aea", raise_err):
                self.run_cli_command(
                    "run",
                    cwd=self._get_cwd(),
                )
        with pytest.raises(Exception, match=f"^..{self.connection2_id}..$"):
            with patch("aea.cli.run.run_aea", raise_err):
                self.run_cli_command(
                    "run",
                    "--exclude-connections",
                    self.connection_id,
                    cwd=self._get_cwd(),
                )

    def test_fail_to_exclude_non_existing_connection(self):
        """Test fail to exclude not defined connection."""
        with pytest.raises(
            Exception,
            match="Connections to exclude: fake/connection:0.1.0 are not defined in agent configuration",
        ):
            self.run_cli_command(
                "--skip-consistency-check",
                "run",
                "--exclude-connections",
                "fake/connection:0.1.0",
                cwd=self._get_cwd(),
            )

    def test_fail_to_specify_connections_and_exclude_the_same_time(self):
        """Test connections specification and exclusion not permited."""

        with pytest.raises(
            Exception,
            match="Please use only one of --connections or --exclude-connections, not both!",
        ):
            self.run_cli_command(
                "run",
                "--exclude-connections",
                self.connection_id,
                "--connections",
                self.connection_id,
                cwd=self._get_cwd(),
            )
