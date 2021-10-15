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
"""Helper to install python dependencies."""
import subprocess  # nosec
import sys
from itertools import chain
from logging import Logger
from subprocess import PIPE  # nosec
from typing import List

from aea.configurations.base import Dependency
from aea.exceptions import AEAException, enforce


def install_dependency(
    dependency_name: str,
    dependency: Dependency,
    logger: Logger,
    install_timeout: float = 300,
) -> None:
    """
    Install python dependency to the current python environment.

    :param dependency_name: name of the python package
    :param dependency: Dependency specification
    :param logger: the logger
    :param install_timeout: timeout to wait pip to install
    """
    try:
        pip_args = dependency.get_pip_install_args()
        logger.debug("Calling 'pip install {}'".format(" ".join(pip_args)))
        call_pip(["install", *pip_args], timeout=install_timeout, retry=True)
    except Exception as e:
        raise AEAException(
            f"An error occurred while installing {dependency_name}, {dependency}: {e}"
        )


def install_dependencies(
    dependencies: List[Dependency], logger: Logger, install_timeout: float = 300,
) -> None:
    """
    Install python dependencies to the current python environment.

    :param dependencies: dict of dependency name and specification
    :param logger: the logger
    :param install_timeout: timeout to wait pip to install
    """
    try:
        pip_args = list(chain(*[d.get_pip_install_args() for d in dependencies]))
        pip_args = [("--extra-index" if i == "-i" else i) for i in pip_args]
        logger.debug("Calling 'pip install {}'".format(" ".join(pip_args)))
        call_pip(["install", *pip_args], timeout=install_timeout, retry=True)
    except Exception as e:
        raise AEAException(
            f"An error occurred while installing with pip install {' '.join(pip_args)}: {e}"
        )


def call_pip(pip_args: List[str], timeout: float = 300, retry: bool = False) -> None:
    """
    Run pip install command.

    :param pip_args: list strings of the command
    :param timeout: timeout to wait pip to install
    :param retry: bool, try one more time if command failed
    """
    command = [sys.executable, "-m", "pip", *pip_args]

    result = subprocess.run(  # nosec
        command, stdout=PIPE, stderr=PIPE, timeout=timeout, check=False
    )
    if result.returncode == 1 and retry:
        # try a second time
        result = subprocess.run(  # nosec
            command, stdout=PIPE, stderr=PIPE, timeout=timeout, check=False
        )
    enforce(
        result.returncode == 0,
        f"pip install failed. Return code != 0: stderr is {str(result.stderr)}",
    )


def run_install_subprocess(
    install_command: List[str], install_timeout: float = 300
) -> int:  # pragma: nocover
    """
    Try executing install command.

    :param install_command: list strings of the command
    :param install_timeout: timeout to wait pip to install
    :return: the return code of the subprocess
    """
    try:
        subp = subprocess.Popen(install_command)  # nosec
        subp.wait(install_timeout)
        return_code = subp.returncode
    finally:
        poll = subp.poll()
        if poll is None:  # pragma: no cover
            subp.terminate()
            subp.wait(30)
    return return_code
