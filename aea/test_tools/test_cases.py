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
import copy
import logging
import os
import random
import shutil
import signal  # pylint: disable=unused-import
import string
import subprocess  # nosec
import sys
import tempfile
import time
from abc import ABC
from filecmp import dircmp
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import pytest

import yaml

from aea.cli import cli
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PackageType
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.configurations.loader import ConfigLoader
from aea.connections.stub.connection import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
)
from aea.helpers.base import cd, sigint_crossplatform
from aea.mail.base import Envelope
from aea.test_tools.click_testing import CliRunner, Result
from aea.test_tools.constants import DEFAULT_AUTHOR
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.generic import (
    force_set_config,
    read_envelope_from_file,
    write_envelope_to_file,
)

from tests.conftest import ROOT_DIR

logger = logging.getLogger(__name__)

CLI_LOG_OPTION = ["-v", "OFF"]
PROJECT_ROOT_DIR = "."

DEFAULT_PROCESS_TIMEOUT = 120
DEFAULT_LAUNCH_TIMEOUT = 10
LAUNCH_SUCCEED_MESSAGE = ("Start processing messages...",)


class BaseAEATestCase(ABC):
    """Base class for AEA test cases."""

    runner: CliRunner  # CLI runner
    last_cli_runner_result: Optional[Result] = None
    author: str = DEFAULT_AUTHOR  # author
    subprocesses: List[subprocess.Popen] = []  # list of launched subprocesses
    threads: List[Thread] = []  # list of started threads
    packages_dir_path: Path = Path("packages")
    use_packages_dir: bool = True
    package_registry_src: Path = Path(ROOT_DIR, "packages")
    old_cwd: Path  # current working directory path
    t: Path  # temporary directory path
    current_agent_context: str = ""  # the name of the current agent
    agents: Set[str] = set()  # the set of created agents
    stdout: Dict[int, str]  # dict of process.pid: string stdout
    stderr: Dict[int, str]  # dict of process.pid: string stderr

    @classmethod
    def set_agent_context(cls, agent_name: str):
        """Set the current agent context."""
        cls.current_agent_context = agent_name

    @classmethod
    def unset_agent_context(cls):
        """Unset the current agent context."""
        cls.current_agent_context = ""

    @classmethod
    def set_config(cls, dotted_path: str, value: Any, type_: str = "str") -> None:
        """
        Set a config.
        Run from agent's directory.

        :param dotted_path: str dotted path to config param.
        :param value: a new value to set.
        :param type_: the type

        :return: None
        """
        cls.run_cli_command(
            "config",
            "set",
            dotted_path,
            str(value),
            "--type",
            type_,
            cwd=cls._get_cwd(),
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
            cls.last_cli_runner_result = result
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
    def start_subprocess(cls, *args: str, cwd: str = ".") -> subprocess.Popen:
        """
        Run python with args as subprocess.

        :param args: CLI args

        :return: subprocess object.
        """
        process = cls._run_python_subprocess(*args, cwd=cwd)
        cls._start_output_read_thread(process)
        cls._start_error_read_thread(process)
        return process

    @classmethod
    def start_thread(cls, target: Callable, **kwargs) -> None:
        """
        Start python Thread.

        :param target: target method.
        :param process: subprocess passed to thread args.

        :return: None.
        """
        if "process" in kwargs:
            thread = Thread(target=target, args=(kwargs["process"],))
        else:
            thread = Thread(target=target)
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
    def fetch_agent(cls, public_id: str, agent_name: str) -> None:
        """
        Create agents in current working directory.

        :param public_id: str public id
        :param agents_name: str agent name.

        :return: None
        """
        cls.run_cli_command("fetch", "--local", public_id, "--alias", agent_name)
        cls.agents.add(agent_name)

    @classmethod
    def difference_to_fetched_agent(cls, public_id: str, agent_name: str) -> List[str]:
        """
        Compare agent against the one fetched from public id.

        :param public_id: str public id
        :param agents_name: str agent name.

        :return: list of files differing in the projects
        """

        def is_allowed_diff_in_agent_config(
            path_to_fetched_aea, path_to_manually_created_aea
        ) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
            with open(
                os.path.join(path_to_fetched_aea, "aea-config.yaml"), "r"
            ) as file:
                content1 = yaml.full_load(file)
            with open(
                os.path.join(path_to_manually_created_aea, "aea-config.yaml"), "r"
            ) as file:
                content2 = yaml.full_load(file)
            content1c = copy.deepcopy(content1)
            for key, value in content1c.items():
                if content2[key] == value:
                    content1.pop(key)
                    content2.pop(key)
            allowed_diff_keys = ["aea_version", "author", "description", "version"]
            result = all([key in allowed_diff_keys for key in content1.keys()])
            result = result and all(
                [key in allowed_diff_keys for key in content2.keys()]
            )
            if result:
                return result, {}, {}
            else:
                return result, content1, content2

        path_to_manually_created_aea = os.path.join(cls.t, agent_name)
        new_cwd = os.path.join(cls.t, "fetch_dir")
        os.mkdir(new_cwd)
        path_to_fetched_aea = os.path.join(new_cwd, agent_name)
        registry_tmp_dir = os.path.join(new_cwd, cls.packages_dir_path)
        shutil.copytree(str(cls.package_registry_src), str(registry_tmp_dir))
        with cd(new_cwd):
            cls.run_cli_command("fetch", "--local", public_id, "--alias", agent_name)
        comp = dircmp(path_to_manually_created_aea, path_to_fetched_aea)
        file_diff = comp.diff_files
        result, diff1, diff2 = is_allowed_diff_in_agent_config(
            path_to_fetched_aea, path_to_manually_created_aea
        )
        if result:
            file_diff.remove("aea-config.yaml")  # won't match!
        else:
            file_diff.append(
                "Difference in aea-config.yaml: " + str(diff1) + " vs. " + str(diff2)
            )
        try:
            shutil.rmtree(new_cwd)
        except (OSError, IOError):
            pass
        return file_diff

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
        process = cls._run_python_subprocess(
            "-m", "aea.cli", "run", *args, cwd=cls._get_cwd()
        )
        cls._start_output_read_thread(process)
        cls._start_error_read_thread(process)
        return process

    @classmethod
    def run_interaction(cls) -> subprocess.Popen:
        """
        Run interaction as subprocess.
        Run from agent's directory.

        :param args: CLI args

        :return: subprocess object.
        """
        process = cls._run_python_subprocess(
            "-m", "aea.cli", "interact", cwd=cls._get_cwd()
        )
        cls._start_output_read_thread(process)
        cls._start_error_read_thread(process)
        return process

    @classmethod
    def terminate_agents(
        cls,
        *subprocesses: subprocess.Popen,
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
        if not subprocesses:
            subprocesses = tuple(cls.subprocesses)
        for process in subprocesses:
            sigint_crossplatform(process)
        for process in subprocesses:
            process.wait(timeout=timeout)

    @classmethod
    def is_successfully_terminated(cls, *subprocesses: subprocess.Popen):
        """
        Check if all subprocesses terminated successfully
        """
        if not subprocesses:
            subprocesses = tuple(cls.subprocesses)

        all_terminated = all([process.returncode == 0 for process in subprocesses])
        return all_terminated

    @classmethod
    def initialize_aea(cls, author) -> None:
        """
        Initialize AEA locally with author name.

        :return: None
        """
        cls.run_cli_command("init", "--local", "--author", author, cwd=cls._get_cwd())

    @classmethod
    def add_item(cls, item_type: str, public_id: str, local: bool = True) -> None:
        """
        Add an item to the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.
        :param local: a flag for local folder add True by default.

        :return: None
        """
        cli_args = ["add", "--local", item_type, public_id]
        if not local:
            cli_args.remove("--local")
        cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def scaffold_item(cls, item_type: str, name: str) -> None:
        """
        Scaffold an item for the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param name: name of the item.

        :return: None
        """
        cls.run_cli_command("scaffold", item_type, name, cwd=cls._get_cwd())

    @classmethod
    def fingerprint_item(cls, item_type: str, public_id: str) -> None:
        """
        Scaffold an item for the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param name: public id of the item.

        :return: None
        """
        cls.run_cli_command("fingerprint", item_type, public_id, cwd=cls._get_cwd())

    @classmethod
    def eject_item(cls, item_type: str, public_id: str) -> None:
        """
        Eject an item in the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.

        :return: None
        """
        cli_args = ["eject", item_type, public_id]
        cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def run_install(cls):
        """
        Execute AEA CLI install command.
        Run from agent's directory.

        :return: None
        """
        cls.run_cli_command("install", cwd=cls._get_cwd())

    @classmethod
    def generate_private_key(cls, ledger_api_id: str = DEFAULT_LEDGER) -> None:
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
        ledger_api_id: str = DEFAULT_LEDGER,
        private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE,
        connection: bool = False,
    ) -> None:
        """
        Add private key with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param private_key_filepath: private key filepath.
        :param connection: whether or not the private key filepath is for a connection.

        :return: None
        """
        if connection:
            cls.run_cli_command(
                "add-key",
                ledger_api_id,
                private_key_filepath,
                "--connection",
                cwd=cls._get_cwd(),
            )
        else:
            cls.run_cli_command(
                "add-key", ledger_api_id, private_key_filepath, cwd=cls._get_cwd()
            )

    @classmethod
    def replace_private_key_in_file(
        cls, private_key: str, private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE
    ) -> None:
        """
        Replace the private key in the provided file with the provided key.

        :param private_key: the private key
        :param private_key_filepath: the filepath to the private key file

        :return: None
        :raises: exception if file does not exist
        """
        with cd(cls._get_cwd()):
            with open(private_key_filepath, "wt") as f:
                f.write(private_key)

    @classmethod
    def generate_wealth(cls, ledger_api_id: str = DEFAULT_LEDGER) -> None:
        """
        Generate wealth with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: None
        """
        cls.run_cli_command(
            "generate-wealth", ledger_api_id, "--sync", cwd=cls._get_cwd()
        )

    @classmethod
    def get_wealth(cls, ledger_api_id: str = DEFAULT_LEDGER) -> str:
        """
        Get wealth with CLI command.
        Run from agent's directory.

        :param ledger_api_id: ledger API ID.

        :return: command line output
        """
        cls.run_cli_command("get-wealth", ledger_api_id, cwd=cls._get_cwd())
        assert cls.last_cli_runner_result is not None, "Runner result not set!"
        return str(cls.last_cli_runner_result.stdout_bytes, "utf-8")

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
    def _read_out(cls, process: subprocess.Popen):
        for line in TextIOWrapper(process.stdout, encoding="utf-8"):
            cls.stdout[process.pid] += line

    @classmethod
    def _read_err(cls, process: subprocess.Popen):
        if process.stderr is not None:
            for line in TextIOWrapper(process.stderr, encoding="utf-8"):
                cls.stderr[process.pid] += line

    @classmethod
    def _start_output_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start an output reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        cls.stdout[process.pid] = ""
        cls.start_thread(target=cls._read_out, process=process)

    @classmethod
    def _start_error_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start an error reading thread.

        :param process: target process passed to a thread args.

        :return: None.
        """
        cls.stderr[process.pid] = ""
        cls.start_thread(target=cls._read_err, process=process)

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
    def missing_from_output(
        cls,
        process: subprocess.Popen,
        strings: Tuple[str],
        timeout: int = DEFAULT_PROCESS_TIMEOUT,
        period: int = 1,
        is_terminating: bool = True,
    ) -> List[str]:
        """
        Check if strings are present in process output.
        Read process stdout in thread and terminate when all strings are present
        or timeout expired.

        :param process: agent subprocess.
        :param strings: tuple of strings expected to appear in output.
        :param timeout: int amount of seconds before stopping check.
        :param period: int period of checking.
        :param is_terminating: whether or not the agents are terminated

        :return: list of missed strings.
        """
        missing_strings = list(strings)
        end_time = time.time() + timeout
        while missing_strings:
            if time.time() > end_time:
                break
            missing_strings = [
                line for line in missing_strings if line not in cls.stdout[process.pid]
            ]
            time.sleep(period)

        if is_terminating:
            cls.terminate_agents(process)
        if missing_strings != []:
            logger.info(
                "Non-empty missing strings, stderr:\n{}".format(cls.stderr[process.pid])
            )
            logger.info("=====================")
            logger.info(
                "Non-empty missing strings, stdout:\n{}".format(cls.stdout[process.pid])
            )
            logger.info("=====================")
        return missing_strings

    @classmethod
    def is_running(
        cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT
    ):
        """
        Check if the AEA is launched and running (ready to process messages).

        :param process: agent subprocess.
        :param timeout: the timeout to wait for launch to complete
        """
        missing_strings = cls.missing_from_output(
            process, LAUNCH_SUCCEED_MESSAGE, timeout, is_terminating=False
        )

        return missing_strings == []

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.old_cwd = Path(os.getcwd())
        cls.subprocesses = []
        cls.threads = []

        cls.t = Path(tempfile.mkdtemp())
        cls.change_directory(cls.t)

        if cls.use_packages_dir:
            registry_tmp_dir = cls.t / cls.packages_dir_path
            cls.package_registry_src = cls.old_cwd / cls.packages_dir_path
            shutil.copytree(str(cls.package_registry_src), str(registry_tmp_dir))

        cls.initialize_aea(cls.author)
        cls.stdout = {}
        cls.stderr = {}

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        cls.terminate_agents(*cls.subprocesses)
        cls._terminate_subprocesses()
        cls._join_threads()
        cls.unset_agent_context()
        cls.change_directory(cls.old_cwd)
        cls.last_cli_runner_result = None
        cls.packages_dir_path = Path("packages")
        cls.use_packages_dir = True
        cls.agents = set()
        cls.current_agent_context = ""
        cls.package_registry_src = Path(ROOT_DIR, "packages")
        cls.stdout = {}
        cls.stderr = {}
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@pytest.mark.integration
class UseOef:
    """
    Inherit from this class to launch an OEF node.
    """

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
        """Teardown the test class."""
        BaseAEATestCase.teardown_class()


class AEATestCase(BaseAEATestCase):
    """
    Test case from an existing AEA project.

    Subclass this class and set `path_to_aea` properly. By default,
    it is assumed the project is inside the current working directory.
    """

    path_to_aea: Union[Path, str] = Path(".")
    packages_dir_path: Path = Path("..", "packages")
    agent_configuration: AgentConfig
    t: Path  # temporary directory path

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        # make paths absolute
        cls.path_to_aea = cls.path_to_aea.absolute()
        # TODO: decide whether to keep optionally: cls.packages_dir_path = cls.packages_dir_path.absolute()
        # load agent configuration
        with Path(cls.path_to_aea, DEFAULT_AEA_CONFIG_FILE).open(
            mode="r", encoding="utf-8"
        ) as fp:
            loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
            agent_configuration = loader.load(fp)
        cls.agent_configuration = agent_configuration
        cls.agent_name = agent_configuration.agent_name

        # this will create a temporary directory and move into it
        # TODO: decide whether to keep optionally:  BaseAEATestCase.packages_dir_path = cls.packages_dir_path
        BaseAEATestCase.use_packages_dir = False
        BaseAEATestCase.setup_class()

        # copy the content of the agent into the temporary directory
        shutil.copytree(str(cls.path_to_aea), str(cls.t / cls.agent_name))
        cls.set_agent_context(cls.agent_name)

    @classmethod
    def teardown_class(cls):
        """Teardown the test class."""
        cls.path_to_aea = Path(".")
        # TODO: decide whether to keep optionally:  cls.packages_dir_path = Path("..", "packages")
        cls.agent_configuration = None
        BaseAEATestCase.teardown_class()
