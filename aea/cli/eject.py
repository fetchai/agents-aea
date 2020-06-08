# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Implementation of the 'aea eject' subcommand."""

import shutil
from pathlib import Path

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import try_to_load_agent_config, update_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    copy_package_directory,
    get_package_path,
    is_item_present,
)
from aea.configurations.base import DEFAULT_VERSION, PublicId


@click.group()
@click.pass_context
@check_aea_project
def eject(click_context: click.core.Context):
    """Eject an installed item."""


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, public_id: PublicId):
    """Eject an installed connection."""
    _eject_item(ctx, "connection", public_id)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, public_id: PublicId):
    """Eject an installed contract."""
    _eject_item(ctx, "contract", public_id)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, public_id: PublicId):
    """Eject an installed protocol."""
    _eject_item(ctx, "protocol", public_id)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, public_id: PublicId):
    """Eject an installed skill."""
    _eject_item(ctx, "skill", public_id)


@clean_after
def _eject_item(ctx: Context, item_type: str, public_id: PublicId):
    """
    Eject item from installed (vendor) to custom folder.

    :param ctx: context object.
    :param item_type: item type.
    :param public_id: item public ID.

    :return: None
    :raises: ClickException if item is absent at source path or present at destenation path.
    """
    item_type_plural = item_type + "s"
    supported_items = getattr(ctx.agent_config, item_type_plural)
    if (
        not is_item_present(ctx, item_type, public_id)
        or public_id not in supported_items
    ):  # pragma: no cover
        raise click.ClickException(
            "{} {} not found in agent items.".format(item_type.title(), public_id)
        )
    src = get_package_path(ctx, item_type, public_id)
    dst = get_package_path(ctx, item_type, public_id, is_vendor=False)
    if is_item_present(ctx, item_type, public_id, is_vendor=False):  # pragma: no cover
        raise click.ClickException(
            "{} {} is already in a non-vendor item.".format(
                item_type.title(), public_id
            )
        )

    ctx.clean_paths.append(dst)
    copy_package_directory(Path(src), dst)

    try_to_load_agent_config(ctx)
    new_public_id = PublicId(
        author=ctx.agent_config.author, name=public_id.name, version=DEFAULT_VERSION
    )
    update_item_config(
        item_type, Path(dst), author=new_public_id.author, version=new_public_id.version
    )
    supported_items.add(new_public_id)
    supported_items.remove(public_id)
    update_item_config("agent", Path(ctx.cwd), **{item_type_plural: supported_items})

    shutil.rmtree(src)
    click.echo("Successfully ejected {} {} to {}.".format(item_type, public_id, dst))
