# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Module with utils for CLI GUI."""

import io
import logging
import os
import subprocess  # nosec
import threading
from enum import Enum
from typing import List, Set, Tuple


class ProcessState(Enum):
    """The state of execution of the agent."""

    NOT_STARTED = "Not started yet"
    RUNNING = "Running"
    STOPPING = "Stopping"
    FINISHED = "Finished"
    FAILED = "Failed"


_processes = set()  # type: Set[subprocess.Popen]
lock = threading.Lock()


def _call_subprocess(*args, timeout=None, **kwargs):
    """
    Create a subprocess.Popen, but with error handling.

    :return the exit code, or -1 if the call raises exception.
    """
    process = subprocess.Popen(*args)  # nosec
    ret = -1
    try:
        ret = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logging.exception(
            "TimeoutError occurred when calling with args={} and kwargs={}".format(
                args, kwargs
            )
        )
    finally:
        _terminate_process(process)
    return ret


def is_agent_dir(dir_name: str) -> bool:
    """Return true if this directory contains an AEA project (an agent)."""
    if not os.path.isdir(dir_name):
        return False
    return os.path.isfile(os.path.join(dir_name, "aea-config.yaml"))


def call_aea_async(param_list: List[str], dir_arg: str) -> subprocess.Popen:
    """Call the aea in a subprocess."""
    # Should lock here to prevent multiple calls coming in at once and changing the current working directory weirdly
    with lock:
        old_cwd = os.getcwd()

        os.chdir(dir_arg)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        ret = subprocess.Popen(  # nosec
            param_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        _processes.add(ret)
        os.chdir(old_cwd)
    return ret


def read_tty(pid: subprocess.Popen, str_list: List[str]) -> None:
    """
    Read tty.

    :param pid: the process id
    :param str_list: the output list to append to.
    """
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        out = line.replace("\n", "")
        logging.info("stdout: {}".format(out))
        str_list.append(line)

    str_list.append("process terminated\n")


def read_error(pid: subprocess.Popen, str_list: List[str]) -> None:
    """
    Read error.

    :param pid: the process id
    :param str_list: the output list to append to.
    """
    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        out = line.replace("\n", "")
        logging.error("stderr: {}".format(out))
        str_list.append(line)

    str_list.append("process terminated\n")


def stop_agent_process(agent_id: str, app_context) -> Tuple[str, int]:
    """
    Stop an agent processs.

    :param agent_id: the agent id
    :param app_context: the app context
    """
    # Test if we have the process id
    if agent_id not in app_context.agent_processes:
        return (
            "detail: Agent {} is not running".format(agent_id),
            400,
        )  # 400 Bad request

    app_context.agent_processes[agent_id].terminate()
    app_context.agent_processes[agent_id].wait()
    del app_context.agent_processes[agent_id]

    return "stop_agent: All fine {}".format(agent_id), 200  # 200 (OK)


def _terminate_process(process: subprocess.Popen) -> None:
    """Try to process gracefully."""
    poll = process.poll()
    if poll is None:
        # send SIGTERM
        process.terminate()
        try:
            # wait for termination
            process.wait(3)
        except subprocess.TimeoutExpired:
            # send SIGKILL
            process.kill()


def terminate_processes() -> None:
    """Terminate all the (async) processes instantiated by the GUI."""
    logging.info("Cleaning up...")
    for process in _processes:  # pragma: no cover
        _terminate_process(process)


def get_process_status(process_id: subprocess.Popen) -> ProcessState:
    """
    Return the state of the execution.

    :param process_id: the process id
    """
    if process_id is None:  # pragma: nocover
        raise ValueError("Process id cannot be None!")

    return_code = process_id.poll()
    if return_code is None:
        return ProcessState.RUNNING
    if return_code <= 0:
        return ProcessState.FINISHED
    return ProcessState.FAILED
