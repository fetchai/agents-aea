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

"""Implementation of the 'aea eject' subcommand."""
import shutil
from pathlib import Path
from typing import cast

import click
from packaging.version import Version

import aea
from aea.cli.fingerprint import fingerprint_item
from aea.cli.remove import ItemRemoveHelper
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import (
    load_item_config,
    set_cli_author,
    try_to_load_agent_config,
    update_item_config,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    copy_package_directory,
    create_symlink_packages_to_vendor,
    create_symlink_vendor_to_local,
    fingerprint_all,
    get_package_path,
    is_item_present,
    replace_all_import_statements,
    update_item_public_id_in_init,
    update_references,
)
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    PackageId,
    PackageType,
    PublicId,
)
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_VERSION,
    PROTOCOL,
    SKILL,
)
from aea.configurations.utils import get_latest_component_id_from_prefix
from aea.helpers.base import (
    compute_specifier_from_version,
    find_topological_order,
    reachable_nodes,
)
from aea.helpers.ipfs.base import IPFSHashOnly


@click.group()
@click.option(
    "--with-symlinks",
    is_flag=True,
    help="Add symlinks from vendor to non-vendor and packages to vendor folders.",
)
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
def eject(click_context: click.core.Context, quiet: bool, with_symlinks: bool) -> None:
    """Eject a vendor package of the agent."""
    click_context.obj.set_config("quiet", quiet)
    click_context.obj.set_config("with_symlinks", with_symlinks)
    set_cli_author(click_context)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, public_id: PublicId) -> None:
    """Eject a vendor connection."""
    quiet = ctx.config.get("quiet")
    with_symlinks = ctx.config.get("with_symlinks")
    _eject_item(ctx, CONNECTION, public_id, quiet=quiet, with_symlinks=with_symlinks)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, public_id: PublicId) -> None:
    """Eject a vendor contract."""
    quiet = ctx.config.get("quiet")
    with_symlinks = ctx.config.get("with_symlinks")
    _eject_item(ctx, CONTRACT, public_id, quiet=quiet, with_symlinks=with_symlinks)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, public_id: PublicId) -> None:
    """Eject a vendor protocol."""
    quiet = ctx.config.get("quiet")
    with_symlinks = ctx.config.get("with_symlinks")
    _eject_item(ctx, PROTOCOL, public_id, quiet=quiet, with_symlinks=with_symlinks)


@eject.command()
@click.argument("public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, public_id: PublicId) -> None:
    """Eject a vendor skill."""
    quiet = ctx.config.get("quiet")
    with_symlinks = ctx.config.get("with_symlinks")
    _eject_item(ctx, SKILL, public_id, quiet=quiet, with_symlinks=with_symlinks)


@clean_after
def _eject_item(
    ctx: Context,
    item_type: str,
    public_id: PublicId,
    quiet: bool = True,
    with_symlinks: bool = False,
) -> None:
    """
    Eject item from installed (vendor) to custom folder.

    :param ctx: context object.
    :param item_type: item type.
    :param public_id: item public ID.
    :param quiet: if false, the function will ask the user in case of recursive eject.
    :param with_symlinks: if eject should create symlinks.

    :raises ClickException: if item is absent at source path or present at destination path.
    """
    # we know cli_author is set because of the above checks.
    cli_author: str = cast(str, ctx.config.get("cli_author"))
    item_type_plural = item_type + "s"

    if not is_item_present(
        ctx.cwd,
        ctx.agent_config,
        item_type,
        public_id,
        is_vendor=True,
        with_version=True,
    ):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} not found in agent's vendor items."
        )

    src = get_package_path(ctx.cwd, item_type, public_id)
    dst = get_package_path(ctx.cwd, item_type, public_id, is_vendor=False)

    if is_item_present(
        ctx.cwd, ctx.agent_config, item_type, public_id, is_vendor=False
    ):  # pragma: no cover
        raise click.ClickException(
            f"{item_type.title()} {public_id} is already a non-vendor package."
        )
    configuration = load_item_config(item_type, Path(src))

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
    reverse_reachable_dependencies = reachable_nodes(
        reverse_dependencies, {package_id.without_hash()}
    )
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
    current_version = Version(aea.__version__)
    new_aea_range = (
        configuration.aea_version
        if configuration.aea_version_specifiers.contains(current_version)
        else compute_specifier_from_version(current_version)
    )

    item_config_update = dict(
        author=new_public_id.author,
        version=new_public_id.version,
        aea_version=new_aea_range,
    )

    update_item_config(item_type, Path(dst), None, **item_config_update)
    update_item_public_id_in_init(item_type, Path(dst), new_public_id)
    shutil.rmtree(src)

    replace_all_import_statements(
        Path(ctx.cwd), ComponentType(item_type), public_id, new_public_id
    )
    fingerprint_item(ctx, item_type, new_public_id)
    package_hash = IPFSHashOnly.hash_directory(dst)
    public_id_with_hash = PublicId(
        new_public_id.author, new_public_id.name, new_public_id.version, package_hash
    )

    # update references in all the other packages
    component_type = ComponentType(item_type_plural[:-1])
    old_component_id = ComponentId(component_type, public_id)
    new_component_id = ComponentId(component_type, public_id_with_hash)
    update_references(ctx, {old_component_id: new_component_id})

    # need to reload agent configuration with the updated references
    try_to_load_agent_config(ctx)

    # replace import statements in all the non-vendor packages

    # fingerprint all (non-vendor) packages
    fingerprint_all(ctx)

    if with_symlinks:
        click.echo(
            "Adding symlinks from vendor to non-vendor and packages to vendor folders."
        )
        create_symlink_vendor_to_local(ctx, item_type, new_public_id)
        create_symlink_packages_to_vendor(ctx)

    click.echo(
        f"Successfully ejected {item_type} {public_id} to {dst} as {public_id_with_hash}."
    )
