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

from pathlib import Path
from typing import List, Optional, cast

import click

from aea import __version__
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.install import do_install
from aea.cli.utils.click_utils import ConnectionsOption
from aea.cli.utils.constants import AEA_LOGO
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.base import PublicId
from aea.exceptions import AEAPackageLoadingError
from aea.helpers.base import load_env_file


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
    ctx = cast(Context, click_context.obj)
    run_aea(ctx, connection_ids, env_file, is_install_deps)


def run_aea(
    ctx: Context, connection_ids: List[PublicId], env_file: str, is_install_deps: bool,
) -> None:
    """
    Prepare and run an agent.

    :param ctx: a context object.
    :param connection_ids: list of connections public IDs.
    :param env_file: a path to env file.
    :param is_install_deps: bool flag is install deps.

    :return: None
    :raises: ClickException if any Exception occures.
    """
    skip_consistency_check = ctx.config["skip_consistency_check"]
    _prepare_environment(ctx, env_file, is_install_deps)
    aea = _build_aea(connection_ids, skip_consistency_check)

    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo("Starting AEA '{}' in '{}' mode...".format(aea.name, aea.loop_mode))
    try:
        aea.start()
    except KeyboardInterrupt:  # pragma: no cover
        click.echo(" AEA '{}' interrupted!".format(aea.name))  # pragma: no cover
    except Exception as e:  # pragma: no cover
        raise click.ClickException(str(e))
    finally:
        click.echo("Stopping AEA '{}' ...".format(aea.name))
        aea.stop()
        click.echo("AEA '{}' stopped.".format(aea.name))


def _prepare_environment(ctx: Context, env_file: str, is_install_deps: bool) -> None:
    """
    Prepare the AEA project environment.

    :param ctx: a context object.
    :param env_file: the path to the envrionemtn file.
    :param is_install_deps: whether to install the dependencies
    """
    load_env_file(env_file)
    if is_install_deps:
        if Path("requirements.txt").exists():
            do_install(ctx, requirement="requirements.txt")
        else:
            do_install(ctx)


def _build_aea(
    connection_ids: Optional[List[PublicId]], skip_consistency_check: bool
) -> AEA:
    try:
        builder = AEABuilder.from_aea_project(
            Path("."), skip_consistency_check=skip_consistency_check
        )
        aea = builder.build(connection_ids=connection_ids)
        return aea
    except AEAPackageLoadingError as e:
        raise click.ClickException("Package loading error: {}".format(str(e)))
    except Exception as e:
        # TODO use an ad-hoc exception class for predictable errors
        #      all the other exceptions should be logged with ClickException
        raise click.ClickException(str(e))
