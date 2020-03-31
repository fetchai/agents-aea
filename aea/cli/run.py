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

"""Implementation of the 'aea run' subcommand."""

import sys
from pathlib import Path
from typing import List, Optional

import click

from aea import __version__
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.common import (
    AEA_LOGO,
    ConnectionsOption,
    check_aea_project,
    logger,
)
from aea.cli.install import install
from aea.configurations.base import PublicId
from aea.helpers.base import load_env_file

AEA_DIR = str(Path("."))


def _prepare_environment(click_context, env_file: str, is_install_deps: bool) -> None:
    """
    Prepare the AEA project environment.

    :param click_context: the click context
    :param env_file: the path to the envrionemtn file.
    :param is_install_deps: whether to install the dependencies
    """
    load_env_file(env_file)
    if is_install_deps:
        if Path("requirements.txt").exists():
            click_context.invoke(install, requirement="requirements.txt")
        else:
            click_context.invoke(install)


def _build_aea(connection_ids: Optional[List[PublicId]]) -> AEA:
    try:
        builder = AEABuilder.from_aea_project(Path("."))
        aea = builder.build(connection_ids=connection_ids)
        return aea
    except Exception as e:
        # TODO use an ad-hoc exception class for predictable errors
        #      all the other exceptions should be logged with logger.exception
        logger.error(str(e))
        sys.exit(1)


def _run_aea(aea: AEA) -> None:
    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo("{} starting ...".format(aea.name))
    try:
        aea.start()
    except KeyboardInterrupt:
        click.echo(" {} interrupted!".format(aea.name))  # pragma: no cover
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
    finally:
        click.echo("{} stopping ...".format(aea.name))
        aea.stop()


@click.command()
@click.option(
    "--connections",
    "connection_ids",
    cls=ConnectionsOption,
    required=False,
    default=None,
    help="The connection names to use for running the agent. Must be declared in the agent's configuration file.",
)
@click.option(
    "--env",
    "env_file",
    type=click.Path(),
    required=False,
    default=".env",
    help="Specify an environment file (default: .env)",
)
@click.option(
    "--install-deps",
    "is_install_deps",
    is_flag=True,
    required=False,
    default=False,
    help="Install all the dependencies before running the agent.",
)
@click.pass_context
@check_aea_project
def run(
    click_context, connection_ids: List[PublicId], env_file: str, is_install_deps: bool
):
    """Run the agent."""
    _prepare_environment(click_context, env_file, is_install_deps)
    aea = _build_aea(connection_ids)
    _run_aea(aea)
