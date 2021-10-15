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

from typing import Optional, cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.loggers import logger
from aea.configurations.data_types import Dependencies
from aea.configurations.pypi import is_satisfiable, is_simple_dep, to_set_specifier
from aea.exceptions import AEAException
from aea.helpers.install_dependency import call_pip, install_dependencies


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
def install(click_context: click.Context, requirement: Optional[str]) -> None:
    """Install the dependencies of the agent."""
    ctx = cast(Context, click_context.obj)
    do_install(ctx, requirement)


def do_install(ctx: Context, requirement: Optional[str] = None) -> None:
    """
    Install necessary dependencies.

    :param ctx: context object.
    :param requirement: optional str requirement.

    :raises ClickException: if AEAException occurs.
    """
    try:
        if requirement:
            logger.debug("Installing the dependencies in '{}'...".format(requirement))
            _install_from_requirement(requirement)
        else:
            logger.debug("Installing all the dependencies...")
            dependencies = ctx.get_dependencies()

            logger.debug("Preliminary check on satisfiability of version specifiers...")
            unsat_dependencies = _find_unsatisfiable_dependencies(dependencies)
            if len(unsat_dependencies) != 0:
                raise AEAException(
                    "cannot install the following dependencies "
                    + "as the joint version specifier is unsatisfiable:\n - "
                    + "\n -".join(
                        [
                            f"{name}: {to_set_specifier(dep)}"
                            for name, dep in unsat_dependencies.items()
                        ]
                    )
                )
            install_dependencies(list(dependencies.values()), logger=logger)
    except AEAException as e:
        raise click.ClickException(str(e))


def _find_unsatisfiable_dependencies(dependencies: Dependencies) -> Dependencies:
    """
    Find unsatisfiable dependencies.

    It only checks among 'simple' dependencies (i.e. if it has no field specified,
    or only the 'version' field set.)

    :param dependencies: the dependencies to check.
    :return: the unsatisfiable dependencies.
    """
    return {
        name: dep
        for name, dep in dependencies.items()
        if is_simple_dep(dep) and not is_satisfiable(to_set_specifier(dep))
    }


def _install_from_requirement(file: str, install_timeout: float = 300) -> None:
    """
    Install from requirements.

    :param file: requirement.txt file path
    :param install_timeout: timeout to wait pip to install

    :raises AEAException: if an error occurs during installation.
    """
    try:
        call_pip(["install", "-r", file], timeout=install_timeout)
    except Exception:
        raise AEAException(
            "An error occurred while installing requirement file {}. Stopping...".format(
                file
            )
        )
