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
from pathlib import Path
from shutil import copyfile
from typing import cast

import click

from aea.cli.registry.publish import publish_agent
from aea.cli.registry.utils import get_package_meta
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.config import validate_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.exceptions import AEAConfigException
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.base import CRUDCollection, PublicId
from aea.configurations.constants import (
    AGENT,
    AGENTS,
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOLS,
    SKILLS,
)


@click.command(name="publish")
@registry_flag(
    help_local="For publishing agent to local folder.",
    help_remote="For publishing agent to remote registry.",
)
@click.pass_context
@check_aea_project
def publish(click_context, local, remote):  # pylint: disable=unused-argument
    """Publish the agent to the registry."""
    ctx = cast(Context, click_context.obj)
    _validate_pkp(ctx.agent_config.private_key_paths)
    _validate_config(ctx)
    if remote:
        publish_agent(ctx)
    else:
        _save_agent_locally(ctx, is_mixed=not local and not remote)


def _validate_config(ctx: Context) -> None:
    """
    Validate agent config.

    :param ctx: Context object.

    :return: None
    :raises ClickException: if validation is failed.
    """
    try:
        validate_item_config(AGENT, Path(ctx.cwd))
    except AEAConfigException as e:  # pragma: no cover
        raise click.ClickException("Failed to validate agent config. {}".format(str(e)))


def _validate_pkp(private_key_paths: CRUDCollection) -> None:
    """
    Prevent to publish agents with non-empty private_key_paths.

    :param private_key_paths: private_key_paths from agent config.
    :raises: ClickException if private_key_paths is not empty.

    :return: None.
    """
    if private_key_paths.read_all() != []:
        raise click.ClickException(
            "You are not allowed to publish agents with non-empty private_key_paths. Use the `aea remove-key` command to remove key paths from `private_key_paths: {}` in `aea-config.yaml`."
        )


def _check_is_item_in_registry_mixed(
    public_id: PublicId, item_type_plural: str, registry_path: str
) -> None:
    """Check first locally, then on remote registry, if a package is present."""
    try:
        _check_is_item_in_local_registry(public_id, item_type_plural, registry_path)
    except click.ClickException:
        try:
            click.echo("Couldn't find item locally. Trying on remote registry...")
            _check_is_item_in_remote_registry(public_id, item_type_plural)
            click.echo("Found!")
        except click.ClickException as e:
            raise click.ClickException(
                f"Package not found neither in local nor in remote registry: {str(e)}"
            )


def _check_is_item_in_remote_registry(
    public_id: PublicId, item_type_plural: str
) -> None:
    """
    Check if an item is in the remote registry.

    :param public_id: the public id.
    :param item_type_plural: the type of the item.
    :return: None
    :raises click.ClickException: if the item is not present.
    """
    get_package_meta(item_type_plural[:-1], public_id)


def _check_is_item_in_local_registry(public_id, item_type_plural, registry_path):
    try:
        try_get_item_source_path(
            registry_path, public_id.author, item_type_plural, public_id.name
        )
    except click.ClickException as e:
        raise click.ClickException(
            f"Dependency is missing. {str(e)}\nPlease push it first and then retry."
        )


def _save_agent_locally(ctx: Context, is_mixed: bool = False) -> None:
    """
    Save agent to local packages.

    :param ctx: the context

    :return: None
    """
    for item_type_plural in (CONNECTIONS, CONTRACTS, PROTOCOLS, SKILLS):
        dependencies = getattr(ctx.agent_config, item_type_plural)
        for public_id in dependencies:
            if is_mixed:
                _check_is_item_in_registry_mixed(
                    PublicId.from_str(str(public_id)),
                    item_type_plural,
                    ctx.agent_config.registry_path,
                )
            else:
                _check_is_item_in_local_registry(
                    PublicId.from_str(str(public_id)),
                    item_type_plural,
                    ctx.agent_config.registry_path,
                )

    item_type_plural = AGENTS

    target_dir = try_get_item_target_path(
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
        f'Agent "{ctx.agent_config.name}" successfully saved in packages folder.'
    )
