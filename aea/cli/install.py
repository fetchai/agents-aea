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
import os
import pprint
import subprocess  # nosec
import sys
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional, cast

import click

from aea.cli.common import Context, check_aea_project, logger
from aea.configurations.base import Dependency
from aea.exceptions import AEAException


def _package_spec(dependency_name: str, dependency: Dependency) -> str:
    """Get string spec of package.

    :param dependency_name: name of the package
    :param dependency: dependency

    :return: package spec string
    """
    package: List[str] = []
    index = dependency.get("index", None)
    git_url = dependency.get("git", None)
    revision = dependency.get("ref", "")
    version_constraint = dependency.get("version", "")
    if git_url is not None:
        package += ["-i", index] if index is not None else []
        package += ["git+" + git_url + "@" + revision + "#egg=" + dependency_name]
    else:
        package += ["-i", index] if index is not None else []
        package += [dependency_name + version_constraint]

    return " ".join(package)


def _install_dependency(dependency_name: str, dependency: Dependency):
    click.echo("Installing {}...".format(pprint.pformat(dependency_name)))
    try:
        package = _package_spec(dependency_name, dependency)
        command = [sys.executable, "-m", "pip", "install", *package.split(" ")]
        logger.debug("Calling '{}'".format(" ".join(command)))
        return_code = _try_install(command)
        if return_code == 1:
            # try a second time
            return_code = _try_install(command)
        assert return_code == 0, "Return code != 0."
    except Exception as e:
        raise AEAException(
            "An error occurred while installing {}, {}: {}".format(
                dependency_name, dependency, str(e)
            )
        )


def _try_install(install_command: List[str]) -> int:
    """
    Try executing install command.

    :param return_code: the return code of the subprocess
    """
    try:
        print(install_command)
        subp = subprocess.Popen(install_command)  # nosec
        subp.wait(120.0)
        return_code = subp.returncode
    finally:
        poll = subp.poll()
        if poll is None:  # pragma: no cover
            subp.terminate()
            subp.wait(2)
    return return_code


def _install_from_requirement(file: str):
    try:
        subp = subprocess.Popen(  # nosec
            [sys.executable, "-m", "pip", "install", "-r", file]
        )  # nosec
        subp.wait(30.0)
        assert subp.returncode == 0, "Return code != 0."
    except Exception:
        raise AEAException(
            "An error occurred while installing requirement file {}. Stopping...".format(
                file
            )
        )
    finally:
        poll = subp.poll()
        if poll is None:  # pragma: no cover
            subp.terminate()
            subp.wait(2)


def _install_dependencies(dependencies: Dict[str, Dependency]) -> None:
    """
    Install multiple dependencies at once.

    :param: dependencies list of tuples name, dependency

    :return: None
    """
    if not dependencies:
        return

    try:
        f = NamedTemporaryFile(delete=False)
        for name, d in dependencies.items():
            f.write(_package_spec(name, d).encode("utf-8"))
            f.write(b"\n")
            f.flush()
        f.close()
        subp = subprocess.Popen(  # nosec
            [sys.executable, "-m", "pip", "install", "-r", f.name],
            env={"GIT_TERMINAL_PROMPT": "0"},
        )  # nosec
        subp.wait()
        assert subp.returncode == 0, "Return code != 0."
    except Exception:
        raise AEAException(
            "An error occurred while installing dependencies. Stopping..."
        )
    finally:
        os.unlink(f.name)


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

    try:
        if requirement:
            logger.debug("Installing the dependencies in '{}'...".format(requirement))
            _install_from_requirement(requirement)
        else:
            logger.debug("Installing all the dependencies...")
            dependencies = ctx.get_dependencies()
            _install_dependencies(dependencies)

    except AEAException as e:
        raise click.ClickException(str(e))
