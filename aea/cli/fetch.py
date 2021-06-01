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
from pathlib import Path
from typing import Optional, cast

import click

from aea.cli.add import add_item
from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import clean_after
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import try_get_item_source_path
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    AGENTS,
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.exceptions import enforce
from aea.helpers.io import open_file


@click.command(name="fetch")
@registry_flag(
    help_local="For fetching agent from local folder.",
    help_remote="For fetching agent from remote registry.",
)
@click.option(
    "--alias", type=str, required=False, help="Provide a local alias for the agent.",
)
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(
    click_context: click.Context,
    public_id: PublicId,
    alias: str,
    local: bool,
    remote: bool,
) -> None:
    """Fetch an agent from the registry."""
    ctx = cast(Context, click_context.obj)
    do_fetch(ctx, public_id, local, remote, alias)


def do_fetch(
    ctx: Context,
    public_id: PublicId,
    local: bool,
    remote: bool,
    alias: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """
    Run the Fetch command.

    :param ctx: the CLI context.
    :param public_id: the public id.
    :param local: whether to fetch from local
    :param remote: whether to fetch from remote
    :param alias: the agent alias.
    :param target_dir: the target directory, in case fetching locally.
    """
    enforce(
        not (local and remote), "'local' and 'remote' options are mutually exclusive."
    )
    if not local and not remote:
        try:
            ctx.registry_path
        except ValueError as e:
            click.echo(f"{e}\nTrying remote registry (`--remote`).")
            remote = True
    is_mixed = not local and not remote
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", is_mixed)
    if remote:
        fetch_agent(ctx, public_id, alias=alias, target_dir=target_dir)
    elif local:
        fetch_agent_locally(ctx, public_id, alias=alias, target_dir=target_dir)
    else:
        fetch_mixed(ctx, public_id, alias=alias, target_dir=target_dir)


def _is_version_correct(ctx: Context, agent_public_id: PublicId) -> bool:
    """
    Compare agent version to the one in public ID.

    :param ctx: Context object.
    :param agent_public_id: public ID of an agent.

    :return: bool is version correct.
    """
    return ctx.agent_config.public_id.same_prefix(agent_public_id) and (
        agent_public_id.package_version.is_latest
        or ctx.agent_config.version == agent_public_id.version
    )


@clean_after
def fetch_agent_locally(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """
    Fetch Agent from local packages.

    :param ctx: a Context object.
    :param public_id: public ID of agent to be fetched.
    :param alias: an optional alias.
    :param target_dir: the target directory to which the agent is fetched.
    """
    try:
        registry_path = ctx.registry_path
    except ValueError as e:
        raise click.ClickException(str(e))

    source_path = try_get_item_source_path(
        registry_path, public_id.author, AGENTS, public_id.name
    )
    enforce(
        ctx.config.get("is_local") is True or ctx.config.get("is_mixed") is True,
        "Please use `ctx.set_config('is_local', True)` or `ctx.set_config('is_mixed', True)` to fetch agent and all components locally.",
    )
    try_to_load_agent_config(ctx, agent_src_path=source_path)
    if not _is_version_correct(ctx, public_id):
        raise click.ClickException(
            "Wrong agent version in public ID: specified {}, found {}.".format(
                public_id.version, ctx.agent_config.version
            )
        )

    folder_name = target_dir or (public_id.name if alias is None else alias)
    target_path = os.path.join(ctx.cwd, folder_name)
    if os.path.exists(target_path):
        path = Path(target_path)
        raise click.ClickException(
            f'Item "{path.name}" already exists in target folder "{path.parent}".'
        )
    if target_dir is not None:
        os.makedirs(target_path)  # pragma: nocover

    ctx.clean_paths.append(target_path)
    copy_tree(source_path, target_path)

    ctx.cwd = target_path
    try_to_load_agent_config(ctx)

    if alias is not None:
        ctx.agent_config.agent_name = alias
        ctx.agent_loader.dump(
            ctx.agent_config,
            open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"),
        )

    _fetch_agent_deps(ctx)
    click.echo("Agent {} successfully fetched.".format(public_id.name))


def _fetch_agent_deps(ctx: Context) -> None:
    """
    Fetch agent dependencies.

    :param ctx: context object.
    """
    for item_type in (PROTOCOL, CONTRACT, CONNECTION, SKILL):
        item_type_plural = "{}s".format(item_type)
        required_items = getattr(ctx.agent_config, item_type_plural)
        for item_id in required_items:
            add_item(ctx, item_type, item_id)


def fetch_mixed(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """
    Fetch an agent in mixed mode.

    :param ctx: the Context.
    :param public_id: the public id.
    :param alias: the alias to the agent.
    :param target_dir: the target directory.
    """
    try:
        fetch_agent_locally(ctx, public_id, alias=alias, target_dir=target_dir)
    except click.ClickException as e:
        logger.debug(
            f"Fetch from local registry failed (reason={str(e)}), trying remote registry..."
        )
        fetch_agent(ctx, public_id, alias=alias, target_dir=target_dir)
