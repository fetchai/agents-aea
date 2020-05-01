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

"""This module contains test case classes based on pytest for AEA end-to-end testing."""
import contextlib
import os
import random
import shutil
import signal
import string
import subprocess  # nosec
import sys
import tempfile
from abc import ABC
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import Any, Callable, List, Optional, Set, Union

import pytest

from aea.cli import cli
from aea.cli_gui import DEFAULT_AUTHOR
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PackageType
from aea.configurations.loader import ConfigLoader
from aea.connections.stub.connection import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
)
from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE
from aea.mail.base import Envelope
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.generic import (
    force_set_config,
    read_envelope_from_file,
    write_envelope_to_file,
)

CLI_LOG_OPTION = ["-v", "OFF"]
PROJECT_ROOT_DIR = "."


@contextlib.contextmanager
def cd(path):
    """Change working directory temporarily."""
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


class BaseAEATestCase(ABC):
    """Base class for AEA test cases."""

    runner: CliRunner  # CLI runner
    author: str = DEFAULT_AUTHOR  # author
    subprocesses: List[subprocess.Popen] = []  # list of launched subprocesses
    threads: List[Thread] = []  # list of started threads
    packages_dir_path: Path = Path("packages")
    old_cwd: Path  # current working directory path
    t: Path  # temporary directory path
    current_agent_context: str = ""  # the name of the current agent
    agents: Set[str] = set()  # the set of created agents

    @classmethod
    def set_agent_context(cls, agent_name: str):
        """Set the current agent context."""
        cls.current_agent_context = agent_name

    @classmethod
    def unset_agent_context(cls):
        """Unset the current agent context."""
        cls.current_agent_context = ""

    @classmethod
    def initialize_aea(cls, author) -> None:
        """
        Initialize AEA locally with author name.

        :return: None
        """
        cls.run_cli_command("init", "--local", "--author", author, cwd=cls._get_cwd())

    @classmethod
    def set_config(cls, dotted_path: str, value: Any, type: str = "str") -> None:
        """
        Set a config.
        Run from agent's directory.

        :param dotted_path: str dotted path to config param.
        :param value: a new value to set.
        :param type: the type

        :return: None
        """
        cls.run_cli_command(
            "config", "set", dotted_path, str(value), "--type", type, cwd=cls._get_cwd()
        )

    @classmethod
    def force_set_config(cls, dotted_path: str, value: Any) -> None:
        """Force set config."""
        with cd(cls._get_cwd()):
            force_set_config(dotted_path, value)

    @classmethod
    def disable_aea_logging(cls):
        """
        Disable AEA logging of specific agent.
        Run from agent's directory.

        :return: None
        """
        config_update_dict = {
            "agent.logging_config.disable_existing_loggers": "False",
            "agent.logging_config.version": "1",
        }
        for path, value in config_update_dict.items():
            cls.run_cli_command("config", "set", path, value, cwd=cls._get_cwd())

    @classmethod
    def run_cli_command(cls, *args: str, cwd: str = ".") -> None:
        """
        Run AEA CLI command.

        :param args: CLI args
        :param cwd: the working directory from where to run the command.
        :raises AEATestingException: if command fails.

        :return: None
        """
        with cd(cwd):
            result = cls.runner.invoke(
                cli, [*CLI_LOG_OPTION, *args], standalone_mode=False
            )
            if result.exit_code != 0:
                raise AEATestingException(
                    "Failed to execute AEA CLI command with args {}.\n"
                    "Exit code: {}\nException: {}".format(
                        args, result.exit_code, result.exception
                    )
                )

    @classmethod
    def _run_python_subprocess(cls, *args: str, cwd: str = ".") -> subprocess.Popen:
        """
        Run python with args as subprocess.

        :param args: CLI args

        :return: subprocess object.
        """
        process = subprocess.Popen(  # nosec
            [sys.executable, *args],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
            cwd=cwd,
        )
        cls.subprocesses.append(process)
        return process

    @classmethod
    def start_thread(cls, target: Callable, process: subprocess.Popen) -> None:
        """
        Start python Thread.

        :param target: target method.
        :param process: subprocess passed to thread args.

        :return: None.
        """
        thread = Thread(target=target, args=(process,))
        thread.start()
        cls.threads.append(thread)

    @classmethod
    def create_agents(cls, *agents_names: str) -> None:
        """
        Create agents in current working directory.

        :param agents_names: str agent names.

        :return: None
        """
        for name in set(agents_names):
            cls.run_cli_command("create", "--local", name, "--author", cls.author)
            cls.agents.add(name)

    @classmethod
    def delete_agents(cls, *agents_names: str) -> None:
        """
        Delete agents in current working directory.

        :param agents_names: str agent names.

        :return: None
        """
        for name in set(agents_names):
            cls.run_cli_command("delete", name)
            cls.agents.remove(name)

    @classmethod
    def run_agent(cls, *args: str) -> subprocess.Popen:
        """
        Run agent as subprocess.
        Run from agent's directory.

        :param args: CLI args

        :return: subprocess object.
        """
        return cls._run_python_subprocess(
            "-m", "aea.cli", "run", *args, cwd=cls._get_cwd()
        )

    @classmethod
    def terminate_agents(
        cls,
        subprocesses: Optional[List[subprocess.Popen]] = None,
        signal: signal.Signals = signal.SIGINT,
        timeout: int = 10,
    ) -> None:
        """
        Terminate agent subprocesses.
        Run from agent's directory.

        :param subprocesses: the subprocesses running the agents
        :param signal: the signal for interuption
        :param timeout: the timeout for interuption
        """
        if subprocesses is None:
            subprocesses = cls.subprocesses
        for process in subprocesses:
            process.send_signal(signal.SIGINT)
        for process in subprocesses:
            process.wait(timeout=timeout)

    @classmethod
    def add_item(cls, item_type: str, public_id: str) -> None:
        """
        Add an item to the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param item_type: str item type.

        :return: None
        """
        cls.run_cli_command("add", "--local", item_type, public_id, cwd=cls._get_cwd())

    @classmethod
    def run_install(cls):
        """
        Execute AEA CLI install command.
        Run from agent's directory.

        :return: None
        """
        cls.run_cli_command("install", cwd=cls._get_cwd())

    @classmethod
    def generate_private_key(cls, ledger_api_id: str = FETCHAI_NAME) -> None:
        """
        Generate AEA private key with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: None
        """
        cls.run_cli_command("generate-key", ledger_api_id, cwd=cls._get_cwd())

    @classmethod
    def add_private_key(
        cls,
        ledger_api_id: str = FETCHAI_NAME,
        private_key_filepath: str = FETCHAI_PRIVATE_KEY_FILE,
    ) -> None:
        """
        Add private key with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param private_key_filepath: private key filepath.

        :return: None
        """
        cls.run_cli_command(
            "add-key", ledger_api_id, private_key_filepath, cwd=cls._get_cwd()
        )

    @classmethod
    def generate_wealth(cls, ledger_api_id: str = FETCHAI_NAME) -> None:
        """
        Generate wealth with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: None
        """
        cls.run_cli_command("generate-wealth", ledger_api_id, cwd=cls._get_cwd())

    @classmethod
    def replace_file_content(cls, src: Path, dest: Path) -> None:
        """
        Replace the content of the source file to the dest file.
        :param src: the source file.
        :param dest: the destination file.
        :return: None
        """
        assert src.is_file() and dest.is_file(), "Source or destination is not a file."
        src.write_text(dest.read_text())

    @classmethod
    def change_directory(cls, path: Path) -> None:
        """
        Change current working directory.

        :param path: path to the new working directory.
        :return: None
        """
        os.chdir(Path(path))

    @classmethod
    def _terminate_subprocesses(cls):
        """Terminate all launched subprocesses."""
        for process in cls.subprocesses:
            if not process.returncode == 0:
                poll = process.poll()
                if poll is None:
                    process.terminate()
                    process.wait(2)
        cls.subprocesses = []

    @classmethod
    def _join_threads(cls):
        """Join all started threads."""
        for thread in cls.threads:
            thread.join()
        cls.threads = []

    @classmethod
    def is_successfully_terminated(
        cls, subprocesses: Optional[List[subprocess.Popen]] = None
    ):
        """
        Check if all subprocesses terminated successfully
        """
        if subprocesses is None:
            subprocesses = cls.subprocesses
        all_terminated = [process.returncode == 0 for process in subprocesses]
        return all_terminated

    @staticmethod
    def _read_tty(pid: subprocess.Popen):
        for line in TextIOWrapper(pid.stdout, encoding="utf-8"):
            print("stdout: " + line.replace("\n", ""))

    @staticmethod
    def _read_error(pid: subprocess.Popen):
        if pid.stderr is not None:
            for line in TextIOWrapper(pid.stderr, encoding="utf-8"):
                print("stderr: " + line.replace("\n", ""))

    @classmethod
    def start_tty_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start a tty reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        cls.start_thread(target=cls._read_tty, process=process)

    @classmethod
    def start_error_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start an error reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        cls.start_thread(target=cls._read_error, process=process)

    @classmethod
    def _get_cwd(cls) -> str:
        """Get the current working directory."""
        return str(cls.t / cls.current_agent_context)

    @classmethod
    def send_envelope_to_agent(cls, envelope: Envelope, agent: str):
        """Send an envelope to an agent, using the stub connection."""
        write_envelope_to_file(envelope, str(cls.t / agent / DEFAULT_INPUT_FILE_NAME))

    @classmethod
    def read_envelope_from_agent(cls, agent: str) -> Envelope:
        """Read an envelope from an agent, using the stub connection."""
        return read_envelope_from_file(str(cls.t / agent / DEFAULT_OUTPUT_FILE_NAME))

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.old_cwd = Path(os.getcwd())
        cls.subprocesses = []
        cls.threads = []

        cls.t = Path(tempfile.mkdtemp())
        cls.change_directory(cls.t)

        cls.registry_tmp_dir = cls.t / "packages"
        package_registry_src = cls.old_cwd / cls.packages_dir_path
        shutil.copytree(str(package_registry_src), str(cls.registry_tmp_dir))

        cls.initialize_aea(cls.author)

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls._terminate_subprocesses()
        cls._join_threads()
        cls.unset_agent_context()
        cls.change_directory(cls.old_cwd)
        cls.packages_dir_path = Path("packages")
        cls.agents = set()
        cls.current_agent_context = ""
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class UseOef:
    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""


class AEATestCaseEmpty(BaseAEATestCase):
    """
    Test case for a default AEA project.

    This test case will create a default AEA project.
    """

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        BaseAEATestCase.setup_class()
        cls.agent_name = "agent-" + "".join(random.choices(string.ascii_lowercase, k=5))
        cls.create_agents(cls.agent_name)
        cls.set_agent_context(cls.agent_name)


class AEATestCaseMany(BaseAEATestCase):
    """Test case for many AEA projects."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        BaseAEATestCase.setup_class()

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls._terminate_subprocesses()
        cls._join_threads()
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class AEATestCase(BaseAEATestCase):
    """
    Test case from an existing AEA project.

    Subclass this class and set `path_to_aea` properly. By default,
    it is assumed the project is inside the current working directory.
    """

    path_to_aea: Union[Path, str] = Path(".")
    packages_dir_path = Path("..", "packages")
    agent_configuration: AgentConfig

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        # make paths absolute
        cls.path_to_aea = cls.path_to_aea.absolute()
        cls.packages_dir_path = cls.packages_dir_path.absolute()
        # load agent configuration
        with Path(cls.path_to_aea, DEFAULT_AEA_CONFIG_FILE).open(
            mode="r", encoding="utf-8"
        ) as fp:
            loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
            agent_configuration = loader.load(fp)
        cls.agent_configuration = agent_configuration
        cls.agent_name = agent_configuration.agent_name

        # this will create a temporary directory and move into it
        BaseAEATestCase.packages_dir_path = cls.packages_dir_path
        BaseAEATestCase.setup_class()

        # copy the content of the agent into the temporary directory
        shutil.copytree(str(cls.path_to_aea), str(cls.t / cls.agent_name))
        cls.set_agent_context(cls.agent_name)
