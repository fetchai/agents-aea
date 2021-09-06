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
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional, cast

import click

from aea import __version__
from aea.aea import AEA
from aea.aea_builder import AEABuilder, DEFAULT_ENV_DOTFILE
from aea.cli.install import do_install
from aea.cli.utils.click_utils import ConnectionsOption, password_option
from aea.cli.utils.constants import AEA_LOGO, REQUIREMENTS
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.base import PublicId
from aea.configurations.manager import AgentConfigManager
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.exceptions import AEAWalletNoAddressException
from aea.helpers.base import load_env_file
from aea.helpers.profiling import Profiling
from aea.protocols.base import Message, Protocol
from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Behaviour, Handler, Model, Skill


@click.command()
@password_option()
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
    default=DEFAULT_ENV_DOTFILE,
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
@click.option(
    "--profiling",
    "profiling",
    required=False,
    default=0,
    help="Enable profiling, print profiling every amount of seconds",
)
@click.option(
    "--exclude-connections",
    "exclude_connection_ids",
    cls=ConnectionsOption,
    required=False,
    default=None,
    help="The connection names to disable for running the agent. Must be declared in the agent's configuration file.",
)
@click.pass_context
@check_aea_project
def run(
    click_context: click.Context,
    connection_ids: List[PublicId],
    exclude_connection_ids: List[PublicId],
    env_file: str,
    is_install_deps: bool,
    profiling: int,
    password: str,
) -> None:
    """Run the agent."""
    if connection_ids and exclude_connection_ids:
        raise click.ClickException(
            "Please use only one of --connections or --exclude-connections, not both!"
        )

    ctx = cast(Context, click_context.obj)
    profiling = int(profiling)
    if exclude_connection_ids:
        connection_ids = _calculate_connection_ids(ctx, exclude_connection_ids)

    if profiling > 0:
        with _profiling_context(period=profiling):
            run_aea(ctx, connection_ids, env_file, is_install_deps, password)
            return
    run_aea(ctx, connection_ids, env_file, is_install_deps, password)


def _calculate_connection_ids(
    ctx: Context, exclude_connections: List[PublicId]
) -> List[PublicId]:
    """Calculate resulting list of connection ids to run."""
    agent_config_manager = AgentConfigManager.load(ctx.cwd)
    not_existing_connections = (
        set(exclude_connections) - agent_config_manager.agent_config.connections
    )
    if not_existing_connections:
        raise ValueError(
            f"Connections to exclude: {', '.join(map(str, not_existing_connections))} are not defined in agent configuration!"
        )

    connection_ids = list(
        agent_config_manager.agent_config.connections - set(exclude_connections)
    )

    return connection_ids


@contextmanager
def _profiling_context(period: int) -> Generator:
    """Start profiling context."""
    OBJECTS_INSTANCES = [
        Message,
        Dialogue,
        Handler,
        Model,
        Behaviour,
        Skill,
        Connection,
        Contract,
        Protocol,
    ]
    OBJECTS_CREATED = [Message, Dialogue]

    profiler = Profiling(
        period=period,
        objects_instances_to_count=OBJECTS_INSTANCES,
        objects_created_to_count=OBJECTS_CREATED,
    )
    profiler.start()
    try:
        yield None
    except Exception:  # pylint: disable=try-except-raise # pragma: nocover
        raise
    finally:
        profiler.stop()
        profiler.wait_completed(sync=True, timeout=10)
        # hack to address faulty garbage collection output being printed
        import os  # pylint: disable=import-outside-toplevel
        import sys  # pylint: disable=import-outside-toplevel

        sys.stderr = open(os.devnull, "w")


def run_aea(
    ctx: Context,
    connection_ids: List[PublicId],
    env_file: str,
    is_install_deps: bool,
    password: Optional[str] = None,
) -> None:
    """
    Prepare and run an agent.

    :param ctx: a context object.
    :param connection_ids: list of connections public IDs.
    :param env_file: a path to env file.
    :param is_install_deps: bool flag is install dependencies.
    :param password: the password to encrypt/decrypt the private key.

    :raises ClickException: if any Exception occurs.
    """
    skip_consistency_check = ctx.config["skip_consistency_check"]
    _prepare_environment(ctx, env_file, is_install_deps)
    aea = _build_aea(connection_ids, skip_consistency_check, password)

    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo(
        "Starting AEA '{}' in '{}' mode...".format(aea.name, aea.runtime.loop_mode)
    )
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
    :param env_file: the path to the environment file.
    :param is_install_deps: whether to install the dependencies
    """
    load_env_file(env_file)
    if is_install_deps:
        requirements_path = REQUIREMENTS if Path(REQUIREMENTS).exists() else None
        do_install(ctx, requirement=requirements_path)


def _build_aea(
    connection_ids: Optional[List[PublicId]],
    skip_consistency_check: bool,
    password: Optional[str] = None,
) -> AEA:
    """Build the AEA."""
    try:
        builder = AEABuilder.from_aea_project(
            Path("."), skip_consistency_check=skip_consistency_check, password=password
        )
        aea = builder.build(connection_ids=connection_ids, password=password)
        return aea
    except AEAWalletNoAddressException:
        error_msg = (
            "You haven't specified any private key for the AEA project.\n"
            "Please add one by using the commands `aea generate-key` and `aea add-key` for the ledger of your choice.\n"
        )
        raise click.ClickException(error_msg)
    except Exception as e:
        raise click.ClickException(str(e))
