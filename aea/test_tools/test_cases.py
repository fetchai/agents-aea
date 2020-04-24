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

import os
import shutil
import subprocess  # nosec
import sys
import tempfile
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import Any, Callable, List

import pytest

from aea.cli import cli
from aea.cli_gui import DEFAULT_AUTHOR as AUTHOR
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PackageType
from aea.configurations.constants import DEFAULT_REGISTRY_PATH
from aea.configurations.loader import ConfigLoader
from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.exceptions import AEATestingException


CLI_LOG_OPTION = ["-v", "OFF"]
PROJECT_ROOT_DIR = "."


class AEATestCase:
    """Test case for AEA end-to-end tests."""

    is_project_dir_test: bool  # whether or not the test is run in an aea directory
    author: str  # author name
    cwd: str  # current working directory path
    runner: CliRunner  # CLI runner
    agent_configuration: AgentConfig  # AgentConfig
    agent_name: str  # the agent name derived from the config
    subprocesses: List  # list of launched subprocesses
    t: str  # temporary directory path
    threads: List  # list of started threads

    @classmethod
    def setup_class(cls, packages_dir_path: str = DEFAULT_REGISTRY_PATH):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        aea_config_file_path = Path(
            os.path.join(PROJECT_ROOT_DIR, DEFAULT_AEA_CONFIG_FILE)
        )
        cls.is_project_dir_test = os.path.isfile(aea_config_file_path)
        if not cls.is_project_dir_test:
            cls.t = tempfile.mkdtemp()

            # add packages folder
            packages_src = os.path.join(cls.cwd, packages_dir_path)
            packages_dst = os.path.join(cls.t, packages_dir_path)
            shutil.copytree(packages_src, packages_dst)
        else:
            with aea_config_file_path.open(mode="r", encoding="utf-8") as fp:
                loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
                agent_configuration = loader.load(fp)
            cls.agent_configuration = agent_configuration
            cls.agent_name = agent_configuration.agent_name
            cls.t = PROJECT_ROOT_DIR

        cls.subprocesses = []
        cls.threads = []

        cls.author = AUTHOR

        os.chdir(cls.t)

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls._terminate_subprocesses()
        cls._join_threads()

        os.chdir(cls.cwd)

        if not cls.is_project_dir_test:
            try:
                shutil.rmtree(cls.t)
            except (OSError, IOError):
                pass

    @classmethod
    def _terminate_subprocesses(cls):
        """Terminate all launched subprocesses."""
        for process in cls.subprocesses:
            if not process.returncode == 0:
                poll = process.poll()
                if poll is None:
                    process.terminate()
                    process.wait(2)

    @classmethod
    def _join_threads(cls):
        """Join all started threads."""
        for thread in cls.threads:
            thread.join()

    def set_config(self, dotted_path: str, value: Any, type: str = "str") -> None:
        """
        Set a config.
        Run from agent's directory.

        :param dotted_path: str dotted path to config param.
        :param value: a new value to set.
        :param type: the type

        :return: None
        """
        self.run_cli_command("config", "set", dotted_path, str(value), "--type", type)

    def disable_aea_logging(self):
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
            self.run_cli_command("config", "set", path, value)

    def run_cli_command(self, *args: str) -> None:
        """
        Run AEA CLI command.

        :param args: CLI args
        :raises AEATestingException: if command fails.

        :return: None
        """
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, *args], standalone_mode=False
        )
        if result.exit_code != 0:
            raise AEATestingException(
                "Failed to execute AEA CLI command with args {}.\n"
                "Exit code: {}\nException: {}".format(
                    args, result.exit_code, result.exception
                )
            )

    def _run_python_subprocess(self, *args: str) -> subprocess.Popen:
        """
        Run python with args as subprocess.

        :param *args: CLI args

        :return: subprocess object.
        """
        process = subprocess.Popen(  # nosec
            [sys.executable, *args], stdout=subprocess.PIPE, env=os.environ.copy(),
        )
        self.subprocesses.append(process)
        return process

    def start_thread(self, target: Callable, process: subprocess.Popen) -> None:
        """
        Start python Thread.

        :param target: target method.
        :param process: subprocess passed to thread args.

        :return: None.
        """
        thread = Thread(target=target, args=(process,))
        thread.start()
        self.threads.append(thread)

    def run_agent(self, *args: str) -> subprocess.Popen:
        """
        Run agent as subprocess.
        Run from agent's directory.

        :param *args: CLI args

        :return: subprocess object.
        """
        return self._run_python_subprocess("-m", "aea.cli", "run", *args)

    def initialize_aea(self, author=None) -> None:
        """
        Initialize AEA locally with author name.

        :return: None
        """
        if author is None:
            author = self.author
        self.run_cli_command("init", "--local", "--author", author)

    def create_agents(self, *agents_names: str) -> None:
        """
        Create agents in current working directory.

        :param *agents_names: str agent names.

        :return: None
        """
        for name in agents_names:
            self.run_cli_command("create", "--local", name, "--author", self.author)

    def delete_agents(self, *agents_names: str) -> None:
        """
        Delete agents in current working directory.

        :param *agents_names: str agent names.

        :return: None
        """
        for name in agents_names:
            self.run_cli_command("delete", name)

    def add_item(self, item_type: str, public_id: str) -> None:
        """
        Add an item to the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param item_type: str item type.

        :return: None
        """
        self.run_cli_command("add", "--local", item_type, public_id)

    def run_install(self):
        """
        Execute AEA CLI install command.
        Run from agent's directory.

        :return: None
        """
        self.run_cli_command("install")

    def generate_private_key(self, ledger_api_id: str = FETCHAI_NAME) -> None:
        """
        Generate AEA private key with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: None
        """
        self.run_cli_command("generate-key", ledger_api_id)

    def add_private_key(
        self,
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
        self.run_cli_command("add-key", ledger_api_id, private_key_filepath)

    def generate_wealth(self, ledger_api_id: str = FETCHAI_NAME) -> None:
        """
        Generate wealth with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: None
        """
        self.run_cli_command("generate-wealth", ledger_api_id)

    def replace_file_content(self, src: Path, dest: Path) -> None:
        """
        Replace the content of the source file to the dest file.
        :param src: the source file.
        :param dest: the destination file.
        :return: None
        """
        assert src.is_file() and dest.is_file()
        src.write_text(dest.read_text())


class AEAWithOefTestCase(AEATestCase):
    """Test case for AEA end-to-end tests with OEF node."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @staticmethod
    def _read_tty(pid: subprocess.Popen):
        for line in TextIOWrapper(pid.stdout, encoding="utf-8"):
            print("stdout: " + line.replace("\n", ""))

    @staticmethod
    def _read_error(pid: subprocess.Popen):
        if pid.stderr is not None:
            for line in TextIOWrapper(pid.stderr, encoding="utf-8"):
                print("stderr: " + line.replace("\n", ""))

    def start_tty_read_thread(self, process: subprocess.Popen) -> None:
        """
        Start a tty reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        self.start_thread(target=self._read_tty, process=process)

    def start_error_read_thread(self, process: subprocess.Popen) -> None:
        """
        Start an error reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        self.start_thread(target=self._read_error, process=process)

    def add_scripts_folder(self):
        scripts_src = os.path.join(self.cwd, "scripts")
        scripts_dst = os.path.join(self.t, "scripts")
        shutil.copytree(scripts_src, scripts_dst)
