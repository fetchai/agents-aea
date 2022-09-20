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
from typing import Dict, Optional, Union, cast

import click
from click.exceptions import ClickException

from aea.cli.registry.push import check_package_public_id, push_item
from aea.cli.registry.settings import REGISTRY_LOCAL, REMOTE_HTTP, REMOTE_IPFS
from aea.cli.utils.click_utils import (
    PublicIdOrPathParameter,
    component_flag,
    registry_flag,
)
from aea.cli.utils.config import (
    get_default_remote_registry,
    get_ipfs_node_multiaddr,
    get_registry_path_from_cli_config,
    load_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.data_types import PublicId
from aea.helpers.cid import to_v1


try:
    from aea_cli_ipfs.core import IPFSTool  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:
    IS_IPFS_PLUGIN_INSTALLED = False


@click.command()
@registry_flag()
@component_flag(wrap_public_id=False)
@click.argument("public_id_or_path", type=PublicIdOrPathParameter())
@click.pass_context
def push(
    click_context: click.Context,
    component_type: str,
    public_id_or_path: Union[PublicId, Path],
    registry: str,
) -> None:
    """Push a non-vendor package of the agent to the registry."""

    if isinstance(public_id_or_path, PublicId):
        push_from_public_id(
            click_context, component_type, cast(PublicId, public_id_or_path), registry
        )
    else:
        push_item_from_path(
            click_context, component_type, cast(Path, public_id_or_path), registry
        )


@check_aea_project
def push_from_public_id(
    context: click.Context, component_type: str, public_id: PublicId, registry: str
) -> None:
    """Push from public id."""
    ctx = cast(Context, context.obj)
    if registry == REGISTRY_LOCAL:
        _save_item_locally(ctx, component_type, public_id)
    else:
        if get_default_remote_registry() == REMOTE_IPFS:
            raise click.ClickException(
                "IPFS registry not supported while pushing an item using public id."
            )

        push_item(ctx, component_type, public_id)


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
        registry_path,
        item_id.author,
        item_type_plural,
        item_id.name,
    )
    copytree(source_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )


def push_item_from_path(
    context: click.Context,
    component_type: str,
    path: Path,
    registry: str,
    package_type_config_class: Optional[Dict] = None,
) -> None:
    """Push item from path."""

    ctx = cast(Context, context.obj)
    component_path = Path(path)
    item_config = load_item_config(
        component_type,
        component_path,
        package_type_config_class=package_type_config_class,
    )

    if registry == REGISTRY_LOCAL:
        push_item_local(ctx, component_type, component_path, item_config.public_id)
    else:
        if get_default_remote_registry() == REMOTE_HTTP:
            raise click.ClickException(
                "Pushing using HTTP is not supported using path parameter."
            )

        push_item_ipfs(component_path, item_config.public_id)


def push_item_local(
    ctx: Context, item_type: str, component_path: Path, item_id: PublicId
) -> None:
    """Push items to the local registry."""
    registry_path: Optional[str]
    item_type_plural = item_type + "s"

    try:
        registry_path = ctx.registry_path
    except ValueError:  # pragma: nocover
        registry_path = get_registry_path_from_cli_config()
        if registry_path is None:
            raise click.ClickException("Registry path was not provided.")
        registry_path = cast(str, registry_path)

    target_path = try_get_item_target_path(
        registry_path,
        item_id.author,
        item_type_plural,
        item_id.name,
    )
    copytree(component_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )


def push_item_ipfs(component_path: Path, public_id: PublicId) -> None:
    """Push items to the ipfs registry."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Please install ipfs plugin using `pip3 install open-aea-cli-ipfs`"
        )

    if len(list(component_path.glob("**/__pycache__"))) > 0:
        raise click.ClickException(
            f"Please remove all cache files from {component_path}"
        )

    ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
    _, package_hash, _ = ipfs_tool.add(str(component_path))
    package_hash = to_v1(package_hash)

    click.echo("Pushed component with:")
    click.echo(f"\tPublicId: {public_id}")
    click.echo(f"\tPackage hash: {package_hash}")
