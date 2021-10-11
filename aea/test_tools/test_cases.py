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
import string
import subprocess  # nosec
import sys
import tempfile
import time
from abc import ABC
from contextlib import suppress
from filecmp import dircmp
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

import yaml

from aea.cli import cli
from aea.configurations.base import (
    AgentConfig,
    PackageType,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_LEDGER,
    DEFAULT_OUTPUT_FILE_NAME,
    DEFAULT_PRIVATE_KEY_FILE,
    DEFAULT_REGISTRY_NAME,
    LAUNCH_SUCCEED_MESSAGE,
)
from aea.configurations.loader import ConfigLoader, ConfigLoaders
from aea.exceptions import enforce
from aea.helpers.base import cd, send_control_c, win_popen_kwargs
from aea.helpers.io import open_file
from aea.mail.base import Envelope
from aea.test_tools.click_testing import CliRunner, Result
from aea.test_tools.constants import DEFAULT_AUTHOR
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.generic import (
    nested_set_config,
    read_envelope_from_file,
    write_envelope_to_file,
)


_default_logger = logging.getLogger(__name__)

CLI_LOG_OPTION = ["-v", "OFF"]

DEFAULT_PROCESS_TIMEOUT = 120
DEFAULT_LAUNCH_TIMEOUT = 10


class BaseAEATestCase(ABC):  # pylint: disable=too-many-public-methods
    """Base class for AEA test cases."""

    runner: CliRunner  # CLI runner
    last_cli_runner_result: Optional[Result] = None
    author: str = DEFAULT_AUTHOR  # author
    subprocesses: List[subprocess.Popen] = []  # list of launched subprocesses
    threads: List[Thread] = []  # list of started threads
    packages_dir_path: Path = Path(DEFAULT_REGISTRY_NAME)
    package_registry_src: Path = Path(".")
    use_packages_dir: bool = True
    package_registry_src_rel: Path = Path(os.getcwd(), packages_dir_path)
    old_cwd: Path  # current working directory path
    t: Path  # temporary directory path
    current_agent_context: str = ""  # the name of the current agent
    agents: Set[str] = set()  # the set of created agents
    stdout: Dict[int, str]  # dict of process.pid: string stdout
    stderr: Dict[int, str]  # dict of process.pid: string stderr
    _is_teardown_class_called: bool = False
    capture_log: bool = False
    cli_log_options: List[str] = []
    method_list: List[str] = []

    @classmethod
    def set_agent_context(cls, agent_name: str) -> None:
        """Set the current agent context."""
        cls.current_agent_context = agent_name

    @classmethod
    def unset_agent_context(cls) -> None:
        """Unset the current agent context."""
        cls.current_agent_context = ""

    @classmethod
    def set_config(
        cls, dotted_path: str, value: Any, type_: Optional[str] = None
    ) -> Result:
        """
        Set a config.

        Run from agent's directory.

        :param dotted_path: str dotted path to config param.
        :param value: a new value to set.
        :param type_: the type

        :return: Result
        """
        if type_ is None:
            type_ = type(value).__name__

        return cls.run_cli_command(
            "config",
            "set",
            dotted_path,
            str(value),
            "--type",
            type_,
            cwd=cls._get_cwd(),
        )

    @classmethod
    def nested_set_config(cls, dotted_path: str, value: Any) -> None:
        """Force set config."""
        with cd(cls._get_cwd()):
            nested_set_config(dotted_path, value)

    @classmethod
    def disable_aea_logging(cls) -> None:
        """
        Disable AEA logging of specific agent.

        Run from agent's directory.
        """
        config_update_dict = {
            "agent.logging_config.disable_existing_loggers": "False",
            "agent.logging_config.version": "1",
        }
        for path, value in config_update_dict.items():
            cls.run_cli_command("config", "set", path, value, cwd=cls._get_cwd())

    @classmethod
    def run_cli_command(cls, *args: str, cwd: str = ".", **kwargs: str) -> Result:
        """
        Run AEA CLI command.

        :param args: CLI args
        :param cwd: the working directory from where to run the command.
        :param kwargs: other keyword arguments to click.CliRunner.invoke.
        :raises AEATestingException: if command fails.

        :return: Result
        """
        with cd(cwd):
            result = cls.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, *args],
                standalone_mode=False,
                catch_exceptions=False,
                **kwargs,
            )
            cls.last_cli_runner_result = result
            if result.exit_code != 0:  # pragma: nocover
                raise AEATestingException(
                    "Failed to execute AEA CLI command with args {}.\n"
                    "Exit code: {}\nException: {}".format(
                        args, result.exit_code, result.exception
                    )
                )
            return result

    @classmethod
    def _run_python_subprocess(cls, *args: str, cwd: str = ".") -> subprocess.Popen:
        """
        Run python with args as subprocess.

        :param args: CLI args
        :param cwd: the current working directory

        :return: subprocess object.
        """
        kwargs = dict(
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=os.environ.copy(),
            cwd=cwd,
        )
        kwargs.update(win_popen_kwargs())

        process = subprocess.Popen(  # type: ignore # nosec # mypy fails on **kwargs
            [sys.executable, *args], **kwargs,
        )
        cls.subprocesses.append(process)
        return process

    @classmethod
    def start_subprocess(cls, *args: str, cwd: str = ".") -> subprocess.Popen:
        """
        Run python with args as subprocess.

        :param args: CLI args
        :param cwd: the current working directory

        :return: subprocess object.
        """
        process = cls._run_python_subprocess(*args, cwd=cwd)
        cls._start_output_read_thread(process)
        cls._start_error_read_thread(process)
        return process

    @classmethod
    def start_thread(cls, target: Callable, **kwargs: subprocess.Popen) -> Thread:
        """
        Start python Thread.

        :param target: target method.
        :param kwargs: thread keyword arguments
        :return: thread
        """
        if "process" in kwargs:
            thread = Thread(target=target, args=(kwargs["process"],))
        else:
            thread = Thread(target=target)
        thread.start()
        cls.threads.append(thread)
        return thread

    @classmethod
    def create_agents(
        cls, *agents_names: str, is_local: bool = True, is_empty: bool = False
    ) -> None:
        """
        Create agents in current working directory.

        :param agents_names: str agent names.
        :param is_local: a flag for local folder add True by default.
        :param is_empty: optional boolean flag for skip adding default dependencies.
        """
        cli_args = ["create", "--local", "--empty"]
        if not is_local:  # pragma: nocover
            cli_args.remove("--local")
        if not is_empty:  # pragma: nocover
            cli_args.remove("--empty")
        for name in set(agents_names):
            cls.run_cli_command(*cli_args, name)
            cls.agents.add(name)

    @classmethod
    def fetch_agent(
        cls, public_id: str, agent_name: str, is_local: bool = True
    ) -> None:
        """
        Create agents in current working directory.

        :param public_id: str public id
        :param agent_name: str agent name.
        :param is_local: a flag for local folder add True by default.
        """
        cli_args = ["fetch", "--local"]
        if not is_local:  # pragma: nocover
            cli_args.remove("--local")
        cls.run_cli_command(*cli_args, public_id, "--alias", agent_name)
        cls.agents.add(agent_name)

    @classmethod
    def difference_to_fetched_agent(cls, public_id: str, agent_name: str) -> List[str]:
        """
        Compare agent against the one fetched from public id.

        :param public_id: str public id
        :param agent_name: str agent name.

        :return: list of files differing in the projects
        """
        # for pydocstyle
        def is_allowed_diff_in_agent_config(
            path_to_fetched_aea: str, path_to_manually_created_aea: str
        ) -> Tuple[
            bool, Union[Dict[str, str], List[Any]], Union[Dict[str, str], List[Any]]
        ]:
            with open_file(
                os.path.join(path_to_fetched_aea, "aea-config.yaml"), "r"
            ) as file:
                content1 = list(yaml.safe_load_all(file))  # load all contents
            with open_file(
                os.path.join(path_to_manually_created_aea, "aea-config.yaml"), "r"
            ) as file:
                content2 = list(yaml.safe_load_all(file))

            content1_agentconfig = content1[0]
            content2_agentconfig = content2[0]
            content1_agentconfig_copy = copy.deepcopy(content1_agentconfig)

            # check only agent part
            for key, value in content1_agentconfig_copy.items():
                if content2_agentconfig[key] == value:
                    content1_agentconfig.pop(key)
                    content2_agentconfig.pop(key)
            allowed_diff_keys = [
                "aea_version",
                "author",
                "description",
                "version",
                "connection_private_key_paths",
                "private_key_paths",
                "dependencies",
                "required_ledgers",
            ]
            result = all(
                [key in allowed_diff_keys for key in content1_agentconfig.keys()]
            )
            result = result and all(
                [key in allowed_diff_keys for key in content2_agentconfig.keys()]
            )
            if not result:
                return result, content1_agentconfig, content2_agentconfig

            # else, additionally check the other YAML pages
            # (i.e. the component configuration overrides)
            content1_component_overrides = content1[1:]
            content2_component_overrides = content2[1:]

            if len(content1_component_overrides) != len(content2_component_overrides):
                return False, content1_component_overrides, content2_component_overrides

            diff_1, diff_2 = [], []
            for index, (override_1, override_2) in enumerate(
                zip(content1_component_overrides, content2_component_overrides)
            ):
                if override_1 != override_2:
                    result = False
                    diff_1.append((index, override_1))
                    diff_2.append((index, override_2))

            return result, diff_1, diff_2

        path_to_manually_created_aea = os.path.join(cls.t, agent_name)
        new_cwd = os.path.join(cls.t, "fetch_dir")
        os.mkdir(new_cwd)
        fetched_agent_name = agent_name
        path_to_fetched_aea = os.path.join(new_cwd, fetched_agent_name)
        registry_tmp_dir = os.path.join(new_cwd, cls.packages_dir_path)
        shutil.copytree(str(cls.package_registry_src_rel), str(registry_tmp_dir))
        with cd(new_cwd):
            cls.run_cli_command(
                "fetch", "--local", public_id, "--alias", fetched_agent_name
            )
        comp = dircmp(path_to_manually_created_aea, path_to_fetched_aea)
        file_diff = comp.diff_files
        result, diff1, diff2 = is_allowed_diff_in_agent_config(
            path_to_fetched_aea, path_to_manually_created_aea
        )
        if result:
            if "aea-config.yaml" in file_diff:  # pragma: nocover
                file_diff.remove("aea-config.yaml")  # won't match!
        else:
            file_diff.append(
                "Difference in aea-config.yaml: " + str(diff1) + " vs. " + str(diff2)
            )

        with suppress(OSError, IOError):
            shutil.rmtree(new_cwd)

        return file_diff

    @classmethod
    def delete_agents(cls, *agents_names: str) -> None:
        """
        Delete agents in current working directory.

        :param agents_names: str agent names.
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
        return cls._start_cli_process("run", *args)

    @classmethod
    def run_interaction(cls) -> subprocess.Popen:
        """
        Run interaction as subprocess.

        Run from agent's directory.

        :return: subprocess object.
        """
        return cls._start_cli_process("interact")

    @classmethod
    def _start_cli_process(cls, *args: str) -> subprocess.Popen:
        """
        Start cli subprocess with args specified.

        :param args: CLI args
        :return: subprocess object.
        """
        process = cls._run_python_subprocess(
            "-m", "aea.cli", *cls.cli_log_options, *args, cwd=cls._get_cwd()
        )
        cls._start_output_read_thread(process)
        cls._start_error_read_thread(process)
        return process

    @classmethod
    def terminate_agents(
        cls, *subprocesses: subprocess.Popen, timeout: int = 20,
    ) -> None:
        """
        Terminate agent subprocesses.

        Run from agent's directory.

        :param subprocesses: the subprocesses running the agents
        :param timeout: the timeout for interruption
        """
        if not subprocesses:
            subprocesses = tuple(cls.subprocesses)
        for process in subprocesses:
            process.poll()
            if process.returncode is None:  # stop only pending processes
                send_control_c(process)
        for process in subprocesses:
            process.wait(timeout=timeout)

    @classmethod
    def is_successfully_terminated(cls, *subprocesses: subprocess.Popen) -> bool:
        """Check if all subprocesses terminated successfully."""
        if not subprocesses:
            subprocesses = tuple(cls.subprocesses)

        all_terminated = all([process.returncode == 0 for process in subprocesses])
        return all_terminated

    @classmethod
    def initialize_aea(cls, author: str) -> None:
        """Initialize AEA locally with author name."""
        cls.run_cli_command("init", "--local", "--author", author, cwd=cls._get_cwd())

    @classmethod
    def add_item(cls, item_type: str, public_id: str, local: bool = True) -> Result:
        """
        Add an item to the agent.

        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.
        :param local: a flag for local folder add True by default.

        :return: Result
        """
        cli_args = ["add", "--local", item_type, public_id]
        if not local:  # pragma: nocover
            cli_args.remove("--local")
        return cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def remove_item(cls, item_type: str, public_id: str) -> Result:
        """
        Remove an item from the agent.

        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.

        :return: Result
        """
        cli_args = ["remove", item_type, public_id]
        return cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def scaffold_item(
        cls, item_type: str, name: str, skip_consistency_check: bool = False
    ) -> Result:
        """
        Scaffold an item for the agent.

        Run from agent's directory.

        :param item_type: str item type.
        :param name: name of the item.
        :param skip_consistency_check: if True, skip consistency check.

        :return: Result
        """
        flags = ["-s"] if skip_consistency_check else []
        if item_type == "protocol":
            return cls.run_cli_command(
                *flags, "scaffold", item_type, "-y", name, cwd=cls._get_cwd()
            )
        return cls.run_cli_command(
            *flags, "scaffold", item_type, name, cwd=cls._get_cwd()
        )

    @classmethod
    def fingerprint_item(cls, item_type: str, public_id: str) -> Result:
        """
        Fingerprint an item for the agent.

        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.

        :return: Result
        """
        return cls.run_cli_command(
            "fingerprint", item_type, public_id, cwd=cls._get_cwd()
        )

    @classmethod
    def eject_item(cls, item_type: str, public_id: str) -> Result:
        """
        Eject an item in the agent in quiet mode (i.e. no interaction).

        Run from agent's directory.

        :param item_type: str item type.
        :param public_id: public id of the item.

        :return: None
        """
        cli_args = ["eject", "--quiet", item_type, public_id]
        return cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def run_install(cls) -> Result:
        """
        Execute AEA CLI install command.

        Run from agent's directory.

        :return: Result
        """
        return cls.run_cli_command("install", cwd=cls._get_cwd())

    @classmethod
    def generate_private_key(
        cls,
        ledger_api_id: str = DEFAULT_LEDGER,
        private_key_file: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Result:
        """
        Generate AEA private key with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param private_key_file: the private key file.
        :param password: the password.

        :return: Result
        """
        cli_args = ["generate-key", ledger_api_id]
        if private_key_file is not None:  # pragma: nocover
            cli_args.append(private_key_file)
        cli_args += _get_password_option_args(password)
        return cls.run_cli_command(*cli_args, cwd=cls._get_cwd())

    @classmethod
    def add_private_key(
        cls,
        ledger_api_id: str = DEFAULT_LEDGER,
        private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE,
        connection: bool = False,
        password: Optional[str] = None,
    ) -> Result:
        """
        Add private key with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param private_key_filepath: private key filepath.
        :param connection: whether or not the private key filepath is for a connection.
        :param password: the password to encrypt private keys.

        :return: Result
        """
        password_option = _get_password_option_args(password)
        if connection:
            return cls.run_cli_command(
                "add-key",
                ledger_api_id,
                private_key_filepath,
                "--connection",
                *password_option,
                cwd=cls._get_cwd(),
            )
        return cls.run_cli_command(
            "add-key",
            ledger_api_id,
            private_key_filepath,
            *password_option,
            cwd=cls._get_cwd(),
        )

    @classmethod
    def remove_private_key(
        cls, ledger_api_id: str = DEFAULT_LEDGER, connection: bool = False,
    ) -> Result:
        """
        Remove private key with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param connection: whether or not the private key filepath is for a connection.

        :return: Result
        """
        args = ["remove-key", ledger_api_id] + (["--connection"] if connection else [])
        return cls.run_cli_command(*args, cwd=cls._get_cwd())

    @classmethod
    def replace_private_key_in_file(
        cls, private_key: str, private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE
    ) -> None:
        """
        Replace the private key in the provided file with the provided key.

        :param private_key: the private key
        :param private_key_filepath: the filepath to the private key file
        :raises: exception if file does not exist
        """
        with cd(cls._get_cwd()):  # pragma: nocover
            with open_file(private_key_filepath, "wt") as f:
                f.write(private_key)

    @classmethod
    def generate_wealth(
        cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None
    ) -> Result:
        """
        Generate wealth with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param password: the password.

        :return: Result
        """
        password_option = _get_password_option_args(password)
        return cls.run_cli_command(
            "generate-wealth",
            ledger_api_id,
            *password_option,
            "--sync",
            cwd=cls._get_cwd(),
        )

    @classmethod
    def get_wealth(
        cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None
    ) -> str:
        """
        Get wealth with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param password: the password to encrypt/decrypt private keys.

        :return: command line output
        """
        password_option = _get_password_option_args(password)
        cls.run_cli_command(
            "get-wealth", ledger_api_id, *password_option, cwd=cls._get_cwd()
        )
        if cls.last_cli_runner_result is None:
            raise ValueError("Runner result not set!")  # pragma: nocover
        return str(cls.last_cli_runner_result.stdout_bytes, "utf-8")

    @classmethod
    def get_address(
        cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None
    ) -> str:
        """
        Get address with CLI command.

        Run from agent's directory.

        :param ledger_api_id: ledger API ID.
        :param password: the password to encrypt/decrypt private keys.

        :return: command line output
        """
        password_option = _get_password_option_args(password)
        cls.run_cli_command(
            "get-address", ledger_api_id, *password_option, cwd=cls._get_cwd()
        )
        if cls.last_cli_runner_result is None:
            raise ValueError("Runner result not set!")  # pragma: nocover
        return str(cls.last_cli_runner_result.stdout_bytes, "utf-8").strip()

    @classmethod
    def replace_file_content(cls, src: Path, dest: Path) -> None:  # pragma: nocover
        """
        Replace the content of the source file to the destination file.

        :param src: the source file.
        :param dest: the destination file.
        """
        enforce(
            src.is_file() and dest.is_file(), "Source or destination is not a file."
        )
        dest.write_text(src.read_text())

    @classmethod
    def change_directory(cls, path: Path) -> None:
        """
        Change current working directory.

        :param path: path to the new working directory.
        """
        os.chdir(Path(path))

    @classmethod
    def _terminate_subprocesses(cls) -> None:
        """Terminate all launched subprocesses."""
        for process in cls.subprocesses:
            if not process.returncode == 0:
                poll = process.poll()
                if poll is None:
                    process.terminate()
                    process.wait(2)
        cls.subprocesses = []

    @classmethod
    def _join_threads(cls) -> None:
        """Join all started threads."""
        for thread in cls.threads:
            thread.join()
        cls.threads = []

    @classmethod
    def _read_out(
        cls, process: subprocess.Popen
    ) -> None:  # pragma: nocover # runs in thread!
        for line in TextIOWrapper(process.stdout, encoding="utf-8"):
            cls._log_capture("stdout", process.pid, line)
            cls.stdout[process.pid] += line

    @classmethod
    def _read_err(
        cls, process: subprocess.Popen
    ) -> None:  # pragma: nocover # runs in thread!
        if process.stderr is not None:
            for line in TextIOWrapper(process.stderr, encoding="utf-8"):
                cls._log_capture("stderr", process.pid, line)
                cls.stderr[process.pid] += line

    @classmethod
    def _log_capture(cls, name: str, pid: int, line: str) -> None:  # pragma: nocover
        if not cls.capture_log:
            return
        sys.stdout.write(f"[{pid}]{name}>{line}")
        sys.stdout.flush()

    @classmethod
    def _start_output_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start an output reading thread.

        :param process: target process passed to a thread args.
        """
        cls.stdout[process.pid] = ""
        cls.start_thread(target=cls._read_out, process=process)

    @classmethod
    def _start_error_read_thread(cls, process: subprocess.Popen) -> None:
        """
        Start an error reading thread.

        :param process: target process passed to a thread args.
        """
        cls.stderr[process.pid] = ""
        cls.start_thread(target=cls._read_err, process=process)

    @classmethod
    def _get_cwd(cls) -> str:
        """Get the current working directory."""
        return str(cls.t / cls.current_agent_context)

    @classmethod
    def send_envelope_to_agent(cls, envelope: Envelope, agent: str) -> None:
        """Send an envelope to an agent, using the stub connection."""
        # check added cause sometimes fails on win with permission error
        dir_path = Path(cls.t / agent)
        enforce(dir_path.exists(), "Dir path does not exist.")
        enforce(dir_path.is_dir(), "Dir path is not a directory.")
        write_envelope_to_file(envelope, str(cls.t / agent / DEFAULT_INPUT_FILE_NAME))

    @classmethod
    def read_envelope_from_agent(cls, agent: str) -> Envelope:
        """Read an envelope from an agent, using the stub connection."""
        return read_envelope_from_file(str(cls.t / agent / DEFAULT_OUTPUT_FILE_NAME))

    @classmethod
    def missing_from_output(
        cls,
        process: subprocess.Popen,
        strings: Sequence[str],
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
            _default_logger.info(
                "Non-empty missing strings, stderr:\n{}".format(cls.stderr[process.pid])
            )
            _default_logger.info("=====================")
            _default_logger.info(
                "Non-empty missing strings, stdout:\n{}".format(cls.stdout[process.pid])
            )
            _default_logger.info("=====================")
        return missing_strings

    @classmethod
    def is_running(
        cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT
    ) -> bool:
        """
        Check if the AEA is launched and running (ready to process messages).

        :param process: agent subprocess.
        :param timeout: the timeout to wait for launch to complete
        :return: bool indicating status
        """
        missing_strings = cls.missing_from_output(
            process, (LAUNCH_SUCCEED_MESSAGE,), timeout, is_terminating=False
        )

        return missing_strings == []

    @classmethod
    def invoke(cls, *args: str) -> Result:
        """Call the cli command."""
        with cd(cls._get_cwd()):
            result = cls.runner.invoke(
                cli, args, standalone_mode=False, catch_exceptions=False
            )
        return result

    @classmethod
    def load_agent_config(cls, agent_name: str) -> AgentConfig:
        """Load agent configuration."""
        if agent_name not in cls.agents:
            raise AEATestingException(
                f"Cannot find agent '{agent_name}' in the current test case."
            )
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        config_file_name = _get_default_configuration_file_name_from_type(
            PackageType.AGENT
        )
        configuration_file_path = Path(cls.t, agent_name, config_file_name)
        with open_file(configuration_file_path) as file_input:
            agent_config = loader.load(file_input)
        return agent_config

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        cls.method_list = [
            func
            for func in dir(cls)
            if callable(getattr(cls, func))
            and not func.startswith("__")
            and func.startswith("test_")
        ]
        cls.runner = CliRunner()
        cls.old_cwd = Path(os.getcwd())
        cls.subprocesses = []
        cls.threads = []

        cls.t = Path(tempfile.mkdtemp())
        cls.change_directory(cls.t)

        cls.package_registry_src = cls.old_cwd / cls.package_registry_src_rel
        if cls.use_packages_dir:
            registry_tmp_dir = cls.t / cls.packages_dir_path
            shutil.copytree(str(cls.package_registry_src), str(registry_tmp_dir))

        cls.initialize_aea(cls.author)
        cls.stdout = {}
        cls.stderr = {}

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        cls.change_directory(cls.old_cwd)
        cls.terminate_agents(*cls.subprocesses)
        cls._terminate_subprocesses()
        cls._join_threads()
        cls.unset_agent_context()
        cls.last_cli_runner_result = None
        cls.packages_dir_path = Path(DEFAULT_REGISTRY_NAME)
        cls.use_packages_dir = True
        cls.agents = set()
        cls.current_agent_context = ""
        cls.stdout = {}
        cls.stderr = {}

        with suppress(OSError, IOError):
            shutil.rmtree(cls.t)

        cls._is_teardown_class_called = True


def _get_password_option_args(password: Optional[str]) -> List[str]:
    """
    Get password option arguments.

    :param password: the password (optional).
    :return: empty list if password is None, else ['--password', password].
    """
    return [] if password is None else ["--password", password]


class AEATestCaseEmpty(BaseAEATestCase):
    """
    Test case for a default AEA project.

    This test case will create a default AEA project.
    """

    agent_name = ""
    IS_LOCAL = True
    IS_EMPTY = False

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        super(AEATestCaseEmpty, cls).setup_class()
        cls.agent_name = "agent_" + "".join(random.choices(string.ascii_lowercase, k=5))
        cls.create_agents(cls.agent_name, is_local=cls.IS_LOCAL, is_empty=cls.IS_EMPTY)
        cls.set_agent_context(cls.agent_name)

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        super(AEATestCaseEmpty, cls).teardown_class()
        cls.agent_name = ""


class AEATestCaseEmptyFlaky(AEATestCaseEmpty):
    """
    Test case for a default AEA project.

    This test case will create a default AEA project.

    Use for flaky tests with the flaky decorator.
    """

    run_count: int = 0

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        super(AEATestCaseEmptyFlaky, cls).setup_class()
        if len(cls.method_list) > 1:  # pragma: nocover
            raise ValueError(f"{cls.__name__} can only contain one test method!")
        cls.run_count += 1

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        super(AEATestCaseEmptyFlaky, cls).teardown_class()


class AEATestCaseMany(BaseAEATestCase):
    """Test case for many AEA projects."""

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        super(AEATestCaseMany, cls).setup_class()

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        super(AEATestCaseMany, cls).teardown_class()


class AEATestCaseManyFlaky(AEATestCaseMany):
    """
    Test case for many AEA projects which are flaky.

    Use for flaky tests with the flaky decorator.
    """

    run_count: int = 0

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        super(AEATestCaseManyFlaky, cls).setup_class()
        if len(cls.method_list) > 1:  # pragma: nocover
            raise ValueError(f"{cls.__name__} can only contain one test method!")
        cls.run_count += 1

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        super(AEATestCaseManyFlaky, cls).teardown_class()


class AEATestCase(BaseAEATestCase):
    """
    Test case from an existing AEA project.

    Subclass this class and set `path_to_aea` properly. By default,
    it is assumed the project is inside the current working directory.
    """

    agent_name = ""
    path_to_aea: Path = Path(".")
    packages_dir_path: Path = Path("..", DEFAULT_REGISTRY_NAME)
    agent_configuration: Optional[AgentConfig] = None
    t: Path  # temporary directory path

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test class."""
        # make paths absolute
        cls.path_to_aea = cls.path_to_aea.absolute()
        # load agent configuration
        with Path(cls.path_to_aea, DEFAULT_AEA_CONFIG_FILE).open(
            mode="r", encoding="utf-8"
        ) as fp:
            loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
            agent_configuration = loader.load(fp)
        cls.agent_configuration = agent_configuration
        cls.agent_name = agent_configuration.agent_name

        # this will create a temporary directory and move into it
        cls.use_packages_dir = False
        super(AEATestCase, cls).setup_class()

        # copy the content of the agent into the temporary directory
        shutil.copytree(str(cls.path_to_aea), str(cls.t / cls.agent_name))
        cls.set_agent_context(cls.agent_name)

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        cls.agent_name = ""
        cls.path_to_aea = Path(".")
        cls.agent_configuration = None
        super(AEATestCase, cls).teardown_class()
