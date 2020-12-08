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
"""Implementation of the 'aea build' subcommand."""
import ast
import sys
from pathlib import Path
from typing import cast

import click

from aea.aea_builder import AEABuilder
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.generic import run_cli_command_subprocess
from aea.configurations.base import PackageConfiguration
from aea.exceptions import enforce


@click.command()
@click.pass_context
@check_aea_project
def build(click_context):
    """Build the agent and its components."""
    ctx = cast(Context, click_context.obj)
    skip_consistency_check = ctx.config.get("skip_consistency_check", False)
    build_aea(ctx, skip_consistency_check)


def _check_valid_entrypoint(config: PackageConfiguration):
    """Check a configuration has a valid entrypoint."""
    enforce(
        config.build_entrypoint is not None,
        "Package has not a build entrypoint specified.",
    )
    config.build_entrypoint = cast(str, config.build_entrypoint)
    enforce(
        config.directory is not None,
        "Configuration is not associated to any directory.",
    )
    config.directory = cast(Path, config.directory)
    script_path = Path(config.directory) / config.build_entrypoint
    enforce(
        script_path.exists(),
        f"File '{config.build_entrypoint}' does not exists.",
        click.ClickException,
    )
    enforce(
        script_path.is_file(),
        f"'{config.build_entrypoint}' is not a file.",
        click.ClickException,
    )
    try:
        ast.parse(script_path.read_text())
    except SyntaxError as e:
        raise click.ClickException(
            f"The Python script at '{config.build_entrypoint}' has a syntax error: {e}"
        ) from e


def run_build_entrypoint(config: PackageConfiguration) -> None:
    """
    Run a build entrypoint script.

    :param config: the component configuration to build.
    :return: None
    """
    _check_valid_entrypoint(config)
    config.build_entrypoint = cast(str, config.build_entrypoint)

    command = [sys.executable, config.build_entrypoint]
    command_str = " ".join(command)
    click.echo(f"Running command '{command_str}'")
    try:
        run_cli_command_subprocess(command)
    except click.ClickException as e:
        raise click.ClickException(
            f"An error occurred while running command '{command_str}': {str(e)}"
        )


def build_aea(ctx: Context, skip_consistency_check: bool) -> None:
    """
    Build an AEA.

    That is, run the 'build entrypoint' script of each AEA package of the project.

    :param ctx: the CLI context.
    :param skip_consistency_check: the skip consistency check boolean.
    :return: None
    """
    try:
        builder = AEABuilder.from_aea_project(
            Path("."), skip_consistency_check=skip_consistency_check
        )
        for (
            config
        ) in (
            builder._package_dependency_manager._dependencies.values()  # type: ignore # pylint: disable=protected-access
        ):
            if not config.build_entrypoint:
                continue
            click.echo(f"Building package {config.component_id}...")
            run_build_entrypoint(config)

        if ctx.agent_config.build_entrypoint:
            click.echo("Building AEA package...")
            run_build_entrypoint(ctx.agent_config)
    except click.ClickException as e:
        raise e from None
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("Build completed!")
