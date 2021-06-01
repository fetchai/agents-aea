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
from pathlib import Path
from typing import cast

import click

from aea.aea_builder import AEABuilder
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project


@click.command()
@click.pass_context
@check_aea_project
def build(click_context: click.Context) -> None:
    """Build the agent and its components."""
    ctx = cast(Context, click_context.obj)
    skip_consistency_check = ctx.config.get("skip_consistency_check", False)
    build_aea(skip_consistency_check)


def build_aea(skip_consistency_check: bool) -> None:
    """
    Build an AEA.

    That is, run the 'build entrypoint' script of each AEA package of the project.

    :param skip_consistency_check: the skip consistency check boolean.
    """
    try:
        builder = AEABuilder.from_aea_project(
            Path("."), skip_consistency_check=skip_consistency_check,
        )
        builder.call_all_build_entrypoints()
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo("Build completed!")
