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

"""Implementation of the 'aea fetch' subcommand."""

import os
from distutils.dir_util import copy_tree
from typing import Optional, cast

import click

from aea.cli.add import add_item
from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import clean_after
from aea.cli.utils.package_utils import try_get_item_source_path
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, PublicId
from aea.configurations.constants import DEFAULT_REGISTRY_PATH


@click.command(name="fetch")
@click.option("--local", is_flag=True, help="For fetching agent from local folder.")
@click.option(
    "--alias", type=str, required=False, help="Provide a local alias for the agent.",
)
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(click_context, public_id, alias, local):
    """Fetch Agent from Registry."""
    ctx = cast(Context, click_context.obj)
    if local:
        fetch_agent_locally(ctx, public_id, alias)
    else:
        fetch_agent(ctx, public_id, alias)


def _is_version_correct(ctx: Context, agent_public_id: PublicId) -> bool:
    """
    Compare agent version to the one in public ID.

    :param ctx: Context object.
    :param public_id: public ID of an agent.

    :return: bool is version correct.
    """
    return ctx.agent_config.version == agent_public_id.version


@clean_after
def fetch_agent_locally(
    ctx: Context, public_id: PublicId, alias: Optional[str] = None
) -> None:
    """
    Fetch Agent from local packages.

    :param ctx: a Context object.
    :param public_id: public ID of agent to be fetched.
    :param alias: an optional alias.
    :return: None
    """
    packages_path = os.path.basename(DEFAULT_REGISTRY_PATH)
    source_path = try_get_item_source_path(
        packages_path, public_id.author, "agents", public_id.name
    )

    try_to_load_agent_config(ctx, agent_src_path=source_path)
    if not _is_version_correct(ctx, public_id):
        raise click.ClickException(
            "Wrong agent version in public ID: specified {}, found {}.".format(
                public_id.version, ctx.agent_config.version
            )
        )

    folder_name = public_id.name if alias is None else alias
    target_path = os.path.join(ctx.cwd, folder_name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(public_id.name)
        )

    ctx.clean_paths.append(target_path)
    copy_tree(source_path, target_path)

    ctx.cwd = target_path
    try_to_load_agent_config(ctx)

    if alias is not None:
        ctx.agent_config.agent_name = alias
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )

    # add dependencies
    _fetch_agent_deps(ctx)
    click.echo("Agent {} successfully fetched.".format(public_id.name))


def _fetch_agent_deps(ctx: Context) -> None:
    """
    Fetch agent dependencies.

    :param ctx: context object.

    :return: None
    :raises: ClickException re-raises if occures in add_item call.
    """
    ctx.set_config("is_local", True)

    for item_type in ("protocol", "contract", "connection", "skill"):
        item_type_plural = "{}s".format(item_type)
        required_items = getattr(ctx.agent_config, item_type_plural)
        for item_id in required_items:
            try:
                add_item(ctx, item_type, item_id)
            except click.ClickException as e:
                raise click.ClickException(
                    "Failed to add {} dependency {}: {}".format(
                        item_type, item_id, str(e)
                    )
                )
