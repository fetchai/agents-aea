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
import re
import shutil
from pathlib import Path
from typing import cast

import click

from aea.cli.fingerprint import fingerprint_item
from aea.cli.remove import ItemRemoveHelper
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import (
    get_non_vendor_package_path,
    load_item_config,
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
    update_references,
)
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    DEFAULT_VERSION,
    PackageId,
    PackageType,
    PublicId,
)
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    IMPORT_TEMPLATE_1,
    IMPORT_TEMPLATE_2,
    PROTOCOL,
    SKILL,
)
from aea.configurations.utils import get_latest_component_id_from_prefix
from aea.helpers.base import find_topological_order, reachable_nodes


@click.group()
@click.option(
    "-q",
    "--quiet",
    "quiet",
    is_flag=True,
    required=False,
    default=False,
    help="If provided, the command will not ask the user for confirmation.",
)
@click.pass_context
@check_aea_project
def eject(click_context: click.core.Context, quiet):
    """Eject an installed item."""
    click_context.obj.set_config("quiet", quiet)
    set_cli_author(click_context)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, public_id: PublicId):
    """Eject an installed connection."""
    quiet = ctx.config.get("quiet")
    _eject_item(ctx, CONNECTION, public_id, quiet=quiet)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, public_id: PublicId):
    """Eject an installed contract."""
    quiet = ctx.config.get("quiet")
    _eject_item(ctx, CONTRACT, public_id, quiet=quiet)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, public_id: PublicId):
    """Eject an installed protocol."""
    quiet = ctx.config.get("quiet")
    _eject_item(ctx, PROTOCOL, public_id, quiet=quiet)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, public_id: PublicId):
    """Eject an installed skill."""
    quiet = ctx.config.get("quiet")
    _eject_item(ctx, SKILL, public_id, quiet=quiet)


@clean_after
def _eject_item(ctx: Context, item_type: str, public_id: PublicId, quiet: bool = True):
    """
    Eject item from installed (vendor) to custom folder.

    :param ctx: context object.
    :param item_type: item type.
    :param public_id: item public ID.
    :param quiet: if false, the function will ask the user in case of recursive eject.

    :return: None
    :raises: ClickException if item is absent at source path or present at destenation path.
    """
    # we know cli_author is set because of the above checks.
    cli_author: str = cast(str, ctx.config.get("cli_author"))
    item_type_plural = item_type + "s"
    if not is_item_present(
        ctx, item_type, public_id, is_vendor=True, with_version=True
    ):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} not found in agent's vendor items."
        )
    src = get_package_path(ctx, item_type, public_id)
    dst = get_package_path(ctx, item_type, public_id, is_vendor=False)
    if is_item_present(ctx, item_type, public_id, is_vendor=False):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} is already a non-vendor package."
        )

    if public_id.package_version.is_latest:
        # get 'concrete' public id, in case it is 'latest'
        component_prefix = ComponentType(item_type), public_id.author, public_id.name
        component_id = get_latest_component_id_from_prefix(
            ctx.agent_config, component_prefix
        )
        # component id is necessarily found, due to the checks above.
        public_id = cast(ComponentId, component_id).public_id

    package_id = PackageId(PackageType(item_type), public_id)

    click.echo(
        f"Ejecting item {package_id.package_type.value} {str(package_id.public_id)}"
    )

    # first, eject all the vendor packages that depend on this
    item_remover = ItemRemoveHelper(ctx, ignore_non_vendor=True)
    reverse_dependencies = (
        item_remover.get_agent_dependencies_with_reverse_dependencies()
    )
    reverse_reachable_dependencies = reachable_nodes(reverse_dependencies, {package_id})
    # the reversed topological order of a graph
    # is the topological order of the reverse graph.
    eject_order = list(reversed(find_topological_order(reverse_reachable_dependencies)))
    eject_order.remove(package_id)
    if len(eject_order) > 0 and not quiet:
        click.echo(f"The following vendor packages will be ejected: {eject_order}")
        answer = click.confirm("Do you want to proceed?")
        if not answer:
            click.echo("Aborted.")
            return

    for dependency_package_id in eject_order:
        # 'dependency_package_id' depends on 'package_id',
        # so we need to eject it first
        _eject_item(
            ctx,
            dependency_package_id.package_type.value,
            dependency_package_id.public_id,
            quiet=True,
        )

    # copy the vendor package into the non-vendor packages
    ctx.clean_paths.append(dst)
    copy_package_directory(Path(src), dst)

    new_public_id = PublicId(cli_author, public_id.name, DEFAULT_VERSION)
    update_item_config(
        item_type, Path(dst), author=new_public_id.author, version=new_public_id.version
    )
    update_item_public_id_in_init(item_type, Path(dst), new_public_id)
    shutil.rmtree(src)

    # update references in all the other packages
    component_type = ComponentType(item_type_plural[:-1])
    old_component_id = ComponentId(component_type, public_id)
    new_component_id = ComponentId(component_type, new_public_id)
    update_references(ctx, {old_component_id: new_component_id})

    # need to reload agent configuration with the updated references
    try_to_load_agent_config(ctx)

    # replace import statements in all the non-vendor packages
    _replace_all_import_statements(
        Path(ctx.cwd), ComponentType(item_type), public_id, new_public_id
    )

    # fingerprint all (non-vendor) packages
    _fingerprint_all(ctx)

    click.echo(
        f"Successfully ejected {item_type} {public_id} to {dst} as {new_public_id}."
    )


def _replace_all_import_statements(
    aea_project_path: Path,
    item_type: ComponentType,
    old_public_id: PublicId,
    new_public_id: PublicId,
):
    """
    Replace all import statements in Python modules of all the non-vendor packages.

    The function looks for two patterns:
    - from packages.<author>.<item_type_plural>.<name>
    - import packages.<author>.<item_type_plural>.<name>

    :param aea_project_path: path to the AEA project.
    :param item_type: the item type.
    :param old_public_id: the old public id.
    :param new_public_id: the new public id.
    :return: None
    """
    old_formats = dict(
        author=old_public_id.author, type=item_type.to_plural(), name=old_public_id.name
    )
    new_formats = dict(
        author=new_public_id.author, type=item_type.to_plural(), name=new_public_id.name
    )
    old_import_1 = IMPORT_TEMPLATE_1.format(**old_formats)
    old_import_2 = IMPORT_TEMPLATE_2.format(**old_formats)
    new_import_1 = IMPORT_TEMPLATE_1.format(**new_formats)
    new_import_2 = IMPORT_TEMPLATE_2.format(**new_formats)

    pattern_1 = re.compile(rf"^{old_import_1}", re.MULTILINE)
    pattern_2 = re.compile(rf"^{old_import_2}", re.MULTILINE)

    for package_path in get_non_vendor_package_path(aea_project_path):
        for python_module in package_path.rglob("*.py"):
            content = python_module.read_text()
            content = pattern_1.sub(new_import_1, content)
            content = pattern_2.sub(new_import_2, content)
            python_module.write_text(content)


def _fingerprint_all(ctx: Context) -> None:
    """
    Fingerprint all non-vendor packages.

    :param ctx: the CLI context.
    :return: None
    """
    aea_project_path = Path(ctx.cwd)
    for package_path in get_non_vendor_package_path(aea_project_path):
        item_type = package_path.parent.name[:-1]
        config = load_item_config(item_type, package_path)
        fingerprint_item(ctx, item_type, config.public_id)
