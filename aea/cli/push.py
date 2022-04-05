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
"""Implementation of the 'aea push' subcommand."""
import os
from pathlib import Path
from shutil import copytree
from typing import cast

import click
from click.exceptions import ClickException

from aea.cli.registry.push import check_package_public_id
from aea.cli.registry.settings import REGISTRY_CONFIG_KEY, REGISTRY_HTTP, REGISTRY_LOCAL
from aea.cli.utils.click_utils import component_flag, registry_flag_
from aea.cli.utils.config import get_or_create_cli_config, load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.base import PublicId
from aea.configurations.data_types import ExtendedPublicId


try:
    from aea_cli_ipfs.core import IPFSTool

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:
    IS_IPFS_PLUGIN_INSTALLED = False


@click.command()
@click.pass_context
@registry_flag_()
@component_flag(wrap_public_id=False)
@click.argument("path", type=click.Path(exists=True, dir_okay=True))
def push(
    click_context: click.Context, component_type: str, path: Path, registry: str,
) -> None:
    """Push a non-vendor package of the agent to the registry."""
    ctx = cast(Context, click_context.obj)
    component_path = Path(path)
    item_config = load_item_config(component_type, component_path)

    if registry == REGISTRY_LOCAL:
        push_item_local(ctx, component_type, component_path, item_config.public_id)
    elif registry == REGISTRY_HTTP:
        push_item_http()
    else:
        push_item_ipfs(component_path, item_config.public_id)


def push_item_local(
    ctx: Context, item_type: str, component_path: Path, item_id: ExtendedPublicId
) -> None:
    """Push items to the local registry."""
    item_type_plural = item_type + "s"

    try:
        registry_path = ctx.registry_path
    except ValueError:  # pragma: nocover
        registry_path = (
            get_or_create_cli_config()
            .get(REGISTRY_CONFIG_KEY, {})
            .get("settings", {})
            .get(REGISTRY_LOCAL, {})
            .get("default_packages_path")
        )
        if registry_path is None:
            raise click.ClickException(f"Registry path was not provided.")
        registry_path = cast(str, registry_path)

    target_path = try_get_item_target_path(
        registry_path, item_id.author, item_type_plural, item_id.name,
    )
    copytree(component_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )


def push_item_http() -> None:
    """Push items to the http registry."""


def push_item_ipfs(component_path: Path, public_id: ExtendedPublicId) -> None:
    """Push items to the ipfs registry."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Please install ipfs plugin using `pip3 install open-aea-cli-ipfs`"
        )

    ipfs_tool = IPFSTool()
    _, package_hash, _ = ipfs_tool.add(component_path)
    click.echo("Pushed component with:")
    click.echo(f"\tPublicId: {public_id}")
    click.echo(f"\tPackage hash: {package_hash}")


def _save_item_locally(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Save item to local packages.

    :param ctx: click context
    :param item_type: str type of item (connection/protocol/skill).
    :param item_id: the public id of the item.
    """
    item_type_plural = item_type + "s"
    try:
        # try non vendor first
        source_path = try_get_item_source_path(
            ctx.cwd, None, item_type_plural, item_id.name
        )
    except ClickException:
        # failed on user's packages
        #  try vendors
        source_path = try_get_item_source_path(
            os.path.join(ctx.cwd, "vendor"),
            item_id.author,
            item_type_plural,
            item_id.name,
        )

    check_package_public_id(source_path, item_type, item_id)

    try:
        registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))
    target_path = try_get_item_target_path(
        registry_path, item_id.author, item_type_plural, item_id.name,
    )
    copytree(source_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )
