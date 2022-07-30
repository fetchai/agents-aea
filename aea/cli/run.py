# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Generator, List, Optional, Sequence, Tuple, cast

import click

from aea import __version__
from aea.aea import AEA
from aea.aea_builder import AEABuilder, DEFAULT_ENV_DOTFILE
from aea.cli.install import do_install
from aea.cli.utils.click_utils import ConnectionsOption, password_option
from aea.cli.utils.constants import AEA_LOGO, REQUIREMENTS
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import list_available_packages
from aea.configurations.base import ComponentType, PublicId
from aea.configurations.manager import AgentConfigManager
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.exceptions import AEAWalletNoAddressException
from aea.helpers.base import load_env_file
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.helpers.profiling import Profiling
from aea.protocols.base import Message, Protocol
from aea.protocols.dialogue.base import Dialogue, DialogueLabel
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
    "--memray",
    "memray_flag",
    is_flag=True,
    required=False,
    default=False,
    help="Enable memray tracing, create a bin file with the memory dump",
)
@click.option(
    "--exclude-connections",
    "exclude_connection_ids",
    cls=ConnectionsOption,
    required=False,
    default=None,
    help="The connection names to disable for running the agent. Must be declared in the agent's configuration file.",
)
@click.option(
    "--aev",
    "apply_environment_variables",
    required=False,
    is_flag=True,
    default=False,
    help="Populate Agent configs from Environment variables.",
)
@click.pass_context
@check_aea_project
def run(
    click_context: click.Context,
    connection_ids: List[PublicId],
    exclude_connection_ids: List[PublicId],
    env_file: str,
    is_install_deps: bool,
    apply_environment_variables: bool,
    profiling: int,
    memray_flag: bool,
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

    profiling_context = (
        _profiling_context(period=profiling) if profiling > 0 else nullcontext()
    )

    memray_context = nullcontext()
    if memray_flag:
        try:
            import memray  # type: ignore # pylint: disable=import-error,import-outside-toplevel

            memray_context = memray.Tracker("memray_profiling.bin")
        except ModuleNotFoundError:
            click.echo(
                "WARNING: memray module is not installed. Memray tracing will be disabled."
            )

    with profiling_context, memray_context:
        run_aea(
            ctx,
            connection_ids,
            env_file,
            is_install_deps,
            apply_environment_variables,
            password,
        )


def _calculate_connection_ids(
    ctx: Context, exclude_connections: List[PublicId]
) -> List[PublicId]:
    """Calculate resulting list of connection ids to run."""
    agent_config_manager = AgentConfigManager.load(ctx.cwd)

    exclude_connections_set = {
        connection.without_hash() for connection in exclude_connections
    }

    agent_connections = {
        connection.without_hash()
        for connection in agent_config_manager.agent_config.connections
    }
    not_existing_connections = exclude_connections_set - agent_connections

    if not_existing_connections:
        raise ValueError(
            f"Connections to exclude: {', '.join(map(str, not_existing_connections))} are not defined in agent configuration!"
        )

    connection_ids = list(agent_connections - exclude_connections_set)
    return connection_ids


@contextmanager
def _profiling_context(period: int) -> Generator:
    """Start profiling context."""
    TYPES_TO_TRACK = [
        Message,
        Dialogue,
        DialogueLabel,
        Handler,
        Model,
        Behaviour,
        Skill,
        Connection,
        Contract,
        Protocol,
    ]

    profiler = Profiling(
        period=period,
        types_to_track=TYPES_TO_TRACK,
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


def print_table(rows: Sequence) -> None:
    """Print a formatted table."""
    head, *rows = rows
    col_lengths = list(map(len, head))

    for row in rows:
        col_lengths = list(map(max, zip(col_lengths, map(len, row))))  # type: ignore

    def _format_row(row: Tuple) -> str:
        """Format row."""
        cols = [
            s + (" " * (max(0, line - len(s)))) for line, s in zip(col_lengths, row)
        ]
        return "| " + " | ".join(cols) + " |"

    table_length = len(_format_row(head))
    separator = "=" * table_length

    click.echo(separator)
    click.echo(_format_row(head))
    click.echo(separator)
    for row in rows:
        click.echo(_format_row(row))
    click.echo(separator)
    click.echo()


def _print_instantiated_components(aea: AEA) -> None:
    """Print table of only components."""
    components: List[str] = [
        "ComponentId",
    ]

    for component_type in [
        ComponentType.PROTOCOL,
        ComponentType.CONNECTION,
        ComponentType.CONTRACT,
        ComponentType.SKILL,
    ]:
        components += [
            str(component.component_id)
            for component in aea.resources.component_registry.fetch_by_type(
                component_type
            )
        ]

    click.echo("All instantiated components")
    print_table([(c,) for c in components])


def _print_all_available_packages(ctx: Context) -> None:
    """Print hashes for all available packages"""
    ipfs_hash = IPFSHashOnly()
    rows = [("Package", "IPFSHash")]

    for package_id, package_path in list_available_packages(ctx.cwd):
        package_hash = ipfs_hash.hash_directory(str(package_path))
        rows.append((str(package_id), package_hash))

    click.echo("All available packages.")
    print_table(rows)


def _print_addresses(aea: AEA) -> None:
    """Print all the addresses used by agent."""

    addresses = [
        ("Name", "Address"),
        *((k, v) for k, v in aea.context.addresses.items()),
    ]

    click.echo("All available addresses.")
    print_table(addresses)


def run_aea(
    ctx: Context,
    connection_ids: List[PublicId],
    env_file: str,
    is_install_deps: bool,
    apply_environment_variables: bool = False,
    password: Optional[str] = None,
) -> None:
    """
    Prepare and run an agent.

    :param ctx: a context object.
    :param connection_ids: list of connections public IDs.
    :param env_file: a path to env file.
    :param is_install_deps: bool flag is install dependencies.
    :param apply_environment_variables: bool flag is load environment variables.
    :param password: the password to encrypt/decrypt the private key.

    :raises ClickException: if any Exception occurs.
    """
    skip_consistency_check = ctx.config["skip_consistency_check"]
    _prepare_environment(ctx, env_file, is_install_deps)
    aea = _build_aea(
        connection_ids, skip_consistency_check, apply_environment_variables, password
    )

    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    _print_all_available_packages(ctx)
    _print_instantiated_components(aea)
    _print_addresses(aea)

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
    apply_environment_variables: bool = False,
    password: Optional[str] = None,
) -> AEA:
    """Build the AEA."""
    try:
        builder = AEABuilder.from_aea_project(
            Path("."),
            skip_consistency_check=skip_consistency_check,
            apply_environment_variables=apply_environment_variables,
            password=password,
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
