# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""Implementation of the 'aea delete' subcommand."""

from typing import List, cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project


@click.command()
@click.pass_context
@check_aea_project
def freeze(click_context: click.Context) -> None:
    """Get the dependencies of the agent."""
    deps = _get_deps(click_context)
    for dependency in deps:
        click.echo(dependency)


def _get_deps(click_context: click.core.Context) -> List[str]:
    """
    Get dependencies list.

    :param click_context: click context object.

    :return: list of str dependencies.
    """
    ctx = cast(Context, click_context.obj)
    deps = []
    for dependency_name, dependency_data in sorted(
        ctx.get_dependencies().items(), key=lambda x: x[0]
    ):
        deps.append(dependency_name + dependency_data.version)
    return deps
