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
"""Helper to install python dependecies."""
import subprocess  # nosec
import sys
from logging import Logger
from typing import List

from aea.configurations.base import Dependency
from aea.exceptions import AEAException, enforce


def install_dependency(
    dependency_name: str, dependency: Dependency, logger: Logger
) -> None:
    """
    Install python dependency to the current python environment.

    :param dependency_name: name of the python package
    :param dependency: Dependency specification

    :return: None
    """
    try:
        pip_args = dependency.get_pip_install_args()
        command = [sys.executable, "-m", "pip", "install", *pip_args]
        logger.debug("Calling '{}'".format(" ".join(command)))
        return_code = run_install_subprocess(command)
        if return_code == 1:
            # try a second time
            return_code = run_install_subprocess(command)
        enforce(return_code == 0, "Return code != 0.")
    except Exception as e:
        raise AEAException(
            "An error occurred while installing {}, {}: {}".format(
                dependency_name, dependency, str(e)
            )
        )


def run_install_subprocess(
    install_command: List[str], install_timeout: float = 300
) -> int:
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
