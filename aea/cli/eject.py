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
from typing import Dict, cast

import click

from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import (
    set_cli_author,
    try_to_load_agent_config,
    update_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    copy_package_directory,
    get_package_path,
    is_item_present,
    update_item_public_id_in_init,
)
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    DEFAULT_VERSION,
    PublicId,
)


@click.group()
@click.pass_context
@check_aea_project
def eject(click_context: click.core.Context):
    """Eject an installed item."""
    set_cli_author(click_context)


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
    if not is_item_present(ctx, item_type, public_id):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} not found in agent's vendor items."
        )
    src = get_package_path(ctx, item_type, public_id)
    dst = get_package_path(ctx, item_type, public_id, is_vendor=False)
    if is_item_present(ctx, item_type, public_id, is_vendor=False):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} is already in a non-vendor item."
        )

    ctx.clean_paths.append(dst)
    copy_package_directory(Path(src), dst)

    try_to_load_agent_config(ctx)

    # we know cli_author is set because of the above checks.
    cli_author: str = cast(str, ctx.config.get("cli_author"))
    new_public_id = PublicId(
        author=cli_author, name=public_id.name, version=DEFAULT_VERSION
    )
    update_item_config(
        item_type, Path(dst), author=new_public_id.author, version=new_public_id.version
    )
    update_item_public_id_in_init(item_type, Path(dst), new_public_id)
    supported_items = getattr(ctx.agent_config, item_type_plural)
    for p_id in supported_items:
        if p_id.author == public_id.author and p_id.name == public_id.name:
            present_public_id = p_id
            break
    supported_items.add(new_public_id)
    supported_items.remove(present_public_id)
    component_type = ComponentType(item_type)
    _update_custom_configurations(
        ctx.agent_config.component_configurations,
        ComponentId(component_type, present_public_id),
        ComponentId(component_type, new_public_id),
    )
    update_item_config(
        "agent",
        Path(ctx.cwd),
        **{
            item_type_plural: supported_items,
            "component_configurations": ctx.agent_config.component_configurations,
        },
    )

    shutil.rmtree(src)
    fingerprint_item(ctx, item_type, new_public_id)
    click.echo(
        f"Successfully ejected {item_type} {public_id} to {dst} as {new_public_id}."
    )


def _update_custom_configurations(
    component_configurations: Dict[ComponentId, Dict],
    old_component_id: ComponentId,
    new_component_id: ComponentId,
):
    """
    Update custom configurations of the AEA configuration.

    Namely, if the public id of the ejected package has a custom configuration
    in the AEA configuration, then replace the identifier with the new
    one (change the author name and the version).

    This function does side-effect on the 'component_configurations' input.

    :param component_configurations: the dictionary of component configurations.
    :param old_component_id: the component id to replace.
    :param new_component_id: the component id to add.
    :return: None
    """
    if old_component_id not in component_configurations:
        return

    old_value = component_configurations.pop(old_component_id)
    component_configurations[new_component_id] = old_value
