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

"""Implementation of the 'aea publish' subcommand."""

import os
from shutil import copyfile
from typing import cast

import click

from aea.cli.common import (
    Context,
    DEFAULT_AEA_CONFIG_FILE,
    _try_get_item_source_path,
    _try_get_vendorized_item_target_path,
    check_aea_project,
    pass_ctx,
)
from aea.cli.registry.publish import publish_agent
from aea.configurations.base import PublicId


@click.command(name="publish")
@click.option("--registry", is_flag=True, help="For publishing agent to Registry.")
@click.pass_context
@check_aea_project
def publish(click_context, registry):
    """Publish Agent to Registry."""
    ctx = cast(Context, click_context.obj)
    if not registry:
        # TODO: check agent dependencies are available in local packages dir.
        _save_agent_locally(ctx)
    else:
        publish_agent(ctx)


def _check_is_item_in_local_registry(public_id, item_type_plural, registry_path):
    try:
        _try_get_item_source_path(
            registry_path, public_id.author, item_type_plural, public_id.name
        )
    except click.ClickException as e:
        raise click.ClickException(
            "Dependency is missing. {} "
            "Please push it first and then retry.".format(e)
        )


def _save_agent_locally(ctx: Context) -> None:
    """
    Save agent to local packages.

    :param ctx: the context

    :return: None
    """
    for item_type_plural in ("connections", "contracts", "protocols", "skills"):
        dependencies = getattr(ctx.agent_config, item_type_plural)
        for public_id in dependencies:
            _check_is_item_in_local_registry(
                PublicId.from_str(str(public_id)),
                item_type_plural,
                ctx.agent_config.registry_path,
            )

    item_type_plural = "agents"

    target_dir = _try_get_vendorized_item_target_path(
        ctx.agent_config.registry_path,
        ctx.agent_config.author,
        item_type_plural,
        ctx.agent_config.name,
    )
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    source_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    target_path = os.path.join(target_dir, DEFAULT_AEA_CONFIG_FILE)
    copyfile(source_path, target_path)
    click.echo(
        'Agent "{}" successfully saved in packages folder.'.format(
            ctx.agent_config.name
        )
    )
