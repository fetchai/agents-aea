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

"""Implementation of the 'aea install' subcommand."""

import pprint
import subprocess  # nosec
import sys
from typing import List, Optional, cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.loggers import logger
from aea.configurations.base import Dependency
from aea.exceptions import AEAException


@click.command()
@click.option(
    "-r",
    "--requirement",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
    default=None,
    help="Install from the given requirements file.",
)
@click.pass_context
@check_aea_project
def install(click_context, requirement: Optional[str]):
    """Install the dependencies."""
    ctx = cast(Context, click_context.obj)
    do_install(ctx, requirement)


def do_install(ctx: Context, requirement: Optional[str] = None) -> None:
    """
    Install necessary dependencies.

    :param ctx: context object.
    :param requirement: optional str requirement.

    :return: None
    :raises: ClickException if AEAException occurres.
    """
    try:
        if requirement:
            logger.debug("Installing the dependencies in '{}'...".format(requirement))
            _install_from_requirement(requirement)
        else:
            logger.debug("Installing all the dependencies...")
            dependencies = ctx.get_dependencies()
            for name, d in dependencies.items():
                _install_dependency(name, d)
    except AEAException as e:
        raise click.ClickException(str(e))


def _install_dependency(dependency_name: str, dependency: Dependency):
    click.echo("Installing {}...".format(pprint.pformat(dependency_name)))
    try:
        index = dependency.get("index", None)
        git_url = dependency.get("git", None)
        revision = dependency.get("ref", "")
        version_constraint = dependency.get("version", "")
        command = [sys.executable, "-m", "pip", "install"]
        if git_url is not None:
            command += ["-i", index] if index is not None else []
            command += ["git+" + git_url + "@" + revision + "#egg=" + dependency_name]
        else:
            command += ["-i", index] if index is not None else []
            command += [dependency_name + version_constraint]
        logger.debug("Calling '{}'".format(" ".join(command)))
        return_code = _run_install_subprocess(command)
        if return_code == 1:
            # try a second time
            return_code = _run_install_subprocess(command)
        assert return_code == 0, "Return code != 0."
    except Exception as e:
        raise AEAException(
            "An error occurred while installing {}, {}: {}".format(
                dependency_name, dependency, str(e)
            )
        )


def _run_install_subprocess(
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


def _install_from_requirement(file: str, install_timeout: float = 300) -> None:
    """
    Install from requirements.

    :param file: requirement.txt file path
    :param install_timeout: timeout to wait pip to install

    :return: None
    """
    try:
        returncode = _run_install_subprocess(
            [sys.executable, "-m", "pip", "install", "-r", file], install_timeout
        )
        assert returncode == 0, "Return code != 0."
    except Exception:
        raise AEAException(
            "An error occurred while installing requirement file {}. Stopping...".format(
                file
            )
        )
