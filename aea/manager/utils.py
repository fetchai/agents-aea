# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Multiagent manager utils."""
import datetime
import multiprocessing
import os
import sys
import time
import venv  # type: ignore
from traceback import format_exc
from typing import Any, Callable

from aea.crypto.plugin import load_all_plugins
from aea.manager.project import Project


def get_lib_path(env_dir: str) -> str:
    """Get librarty path for env dir."""
    if sys.platform == "win32":  # pragma: nocover
        libpath = os.path.join(env_dir, "Lib", "site-packages")
    else:  # pragma: nocover
        libpath = os.path.join(
            env_dir, "lib", "python%d.%d" % sys.version_info[:2], "site-packages"
        )
    return libpath


def make_venv(env_dir: str, set_env: bool = False) -> None:
    """
    Make venv and update variable to use it.

    :param env_dir: str, path for new env dir
    :param set_env: bool. use evn within this python process (update, sys.executable and sys.path)
    """
    builder = venv.EnvBuilder(True, clear=True)
    ctx = builder.ensure_directories(env_dir)
    builder.create(env_dir)
    if set_env:  # pragma: nocover
        sys.executable = ctx.env_exe
        sys.path.insert(0, get_lib_path(env_dir))


def project_install_and_build(project: Project) -> None:
    """Install project dependencies and build required components."""
    project.install_pypi_dependencies()
    load_all_plugins(is_raising_exception=False)
    project.build()


def get_venv_dir_for_project(project: Project) -> str:
    """Get virtual env directory for project specified."""
    return os.path.join(project.path, "venv")


def project_check(project: Project) -> None:
    """Perform project loads well."""
    project.check()


def run_in_venv(env_dir: str, fn: Callable, timeout: float, *args: Any) -> Any:
    """Run python function in a dedicated process with virtual env specified."""
    manager = multiprocessing.Manager()
    result_queue = manager.Queue()
    process = multiprocessing.Process(
        target=_run_in_venv_handler,
        args=tuple([env_dir, fn, result_queue] + list(args)),
    )
    process.start()
    start_time = time.time()
    while process.is_alive():
        time.sleep(0.005)
        if timeout != 0 and (time.time() - start_time > timeout):  # pragma: nocover
            process.terminate()
            process.join(5)
            raise TimeoutError()
    process.join(5)
    result = result_queue.get_nowait()
    if isinstance(result, BaseException):
        raise result
    return result


def _run_in_venv_handler(
    env_dir: str, fn: Callable, queue: multiprocessing.Queue, *args: Any
) -> None:
    """Do actual function run in a dedicated process within virtual env."""
    result = None
    try:
        make_venv(env_dir, set_env=True)
        result = fn(*args)
    except Exception as e:  # pylint: disable=broad-except
        print(
            f"Exception in venv runner at {datetime.datetime.now()} for {fn}:\n{format_exc()}"
        )
        result = e
    queue.put_nowait(result)
