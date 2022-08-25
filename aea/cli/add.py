# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Implementation of the 'aea add' subcommand."""

import shutil
from pathlib import Path
from typing import Union, cast

import click

from aea.cli.registry.add import fetch_package
from aea.cli.registry.settings import REGISTRY_LOCAL, REMOTE_IPFS
from aea.cli.utils.click_utils import component_flag, registry_flag
from aea.cli.utils.config import get_default_remote_registry, load_item_config
from aea.cli.utils.constants import DUMMY_PACKAGE_ID
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import (
    copy_package_directory,
    find_item_in_distribution,
    find_item_locally,
    get_item_id_present,
    get_package_path,
    is_distributed_item,
    is_fingerprint_correct,
    is_item_present,
    is_item_with_hash_present,
    register_item,
)
from aea.configurations.base import (
    ConnectionConfig,
    ContractConfig,
    PackageConfiguration,
    SkillConfig,
)
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL
from aea.configurations.data_types import PublicId
from aea.helpers.ipfs.base import IPFSHashOnly


try:
    from aea_cli_ipfs.exceptions import HashNotProvided  # type: ignore
    from aea_cli_ipfs.registry import fetch_ipfs  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except ImportError:
    IS_IPFS_PLUGIN_INSTALLED = False


@click.command()
@registry_flag()
@component_flag(wrap_public_id=True)
@click.pass_context
@check_aea_project
def add(
    click_context: click.Context,
    component_type: str,
    public_id: PublicId,
    registry: str,
) -> None:
    """Add a package to the agent."""
    ctx = cast(Context, click_context.obj)
    ctx.registry_type = registry
    add_item(ctx, component_type, public_id)


@clean_after
def add_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Add an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    """

    from_hash = item_public_id == DUMMY_PACKAGE_ID
    present_item_id = None
    if from_hash:
        click.echo(f"Adding item from hash: {item_public_id.hash}")
        present_item_id = is_item_with_hash_present(
            ctx.cwd, ctx.agent_config, item_public_id.hash
        )
    else:
        click.echo(f"Adding {item_type} '{item_public_id}'...")
        if is_item_present(ctx.cwd, ctx.agent_config, item_type, item_public_id):
            present_item_id = get_item_id_present(
                ctx.agent_config, item_type, item_public_id
            )

    if present_item_id is not None:
        raise click.ClickException(
            "A {} with id '{}' already exists. Aborting...".format(
                item_type, present_item_id.without_hash()
            )
        )

    dest_path = get_package_path(ctx.cwd, item_type, item_public_id)
    ctx.clean_paths.append(dest_path)

    if ctx.registry_type == REGISTRY_LOCAL:
        package_path = find_item_locally_or_distributed(
            ctx, item_type, item_public_id, dest_path
        )
    else:
        package_path = fetch_item_remote(ctx, item_type, item_public_id, dest_path)

    if from_hash:
        (package_path_temp,) = list(package_path.parent.iterdir())
        item_config = load_item_config(item_type, package_path_temp)
        item_public_id = item_config.public_id
        package_path = Path(get_package_path(ctx.cwd, item_type, item_public_id))
        if package_path.is_dir():
            shutil.rmtree(package_path_temp.parent.parent)
            raise click.ClickException(
                f"Package with id {item_public_id} already exists."
            )
        ctx.clean_paths.append(package_path)
        shutil.move(str(package_path_temp), package_path)

    item_config = load_item_config(item_type, package_path)
    if not ctx.config.get("skip_consistency_check") and not is_fingerprint_correct(
        package_path, item_config
    ):  # pragma: no cover
        raise click.ClickException("Failed to add an item with incorrect fingerprint.")
    _add_item_deps(ctx, item_type, item_config)

    try:
        package_hash = item_public_id.hash
    except (ValueError, AttributeError):
        package_hash = IPFSHashOnly().hash_directory(str(package_path))

    register_item(
        ctx,
        item_type,
        PublicId.from_json(
            {**item_config.public_id.json, "package_hash": package_hash}
        ),
    )
    click.echo(f"Successfully added {item_type} '{item_config.public_id}'.")


def _add_item_deps(
    ctx: Context, item_type: str, item_config: PackageConfiguration
) -> None:
    """
    Add item dependencies. Calls add_item recursively.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_config: item configuration object.
    """
    if item_type in {CONNECTION, SKILL}:
        item_config = cast(Union[SkillConfig, ConnectionConfig], item_config)
        # add missing protocols
        for protocol_public_id in item_config.protocols:
            if protocol_public_id not in ctx.agent_config.protocols:
                add_item(ctx, PROTOCOL, protocol_public_id)

    if item_type == SKILL:
        item_config = cast(SkillConfig, item_config)
        # add missing contracts
        for contract_public_id in item_config.contracts:
            if contract_public_id not in ctx.agent_config.contracts:
                add_item(ctx, CONTRACT, contract_public_id)

        # add missing connections
        for connection_public_id in item_config.connections:
            if connection_public_id not in ctx.agent_config.connections:
                add_item(ctx, CONNECTION, connection_public_id)

        # add missing skill
        for skill_public_id in item_config.skills:
            if skill_public_id not in ctx.agent_config.skills:
                add_item(ctx, SKILL, skill_public_id)

    if item_type == CONTRACT:
        item_config = cast(ContractConfig, item_config)
        # add missing contracts
        for contract_public_id in item_config.contracts:
            if contract_public_id not in ctx.agent_config.contracts:
                add_item(ctx, CONTRACT, contract_public_id)


def fetch_item_remote(
    ctx: Context, item_type: str, item_public_id: PublicId, dest_path: str
) -> Path:
    """Fetch item remote."""

    if get_default_remote_registry() == REMOTE_IPFS:
        try:
            return cast(Path, fetch_ipfs(item_type, item_public_id, dest_path))
        except HashNotProvided:
            click.echo(f"Hash was not provided for: {item_public_id}")
            click.echo("Will try with http repository.")

    return fetch_package(
        item_type,
        public_id=item_public_id,
        cwd=ctx.cwd,
        dest=dest_path,
    )


def find_item_locally_or_distributed(
    ctx: Context, item_type: str, item_public_id: PublicId, dest_path: str
) -> Path:
    """
    Unify find item locally both in case it is distributed or not.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param dest_path: the path to the destination.
    :return: the path to the found package.
    """
    is_distributed = is_distributed_item(item_public_id)
    if is_distributed:  # pragma: nocover
        source_path = find_item_in_distribution(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)
    else:
        source_path, _ = find_item_locally(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)
    return package_path


def fetch_item_mixed(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    dest_path: str,
) -> Path:
    """
    Find item, mixed mode.That is, give priority to local registry, and fall back to remote registry in case of failure.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param dest_path: the path to the destination.
    :return: the path to the found package.
    """
    try:
        package_path = find_item_locally_or_distributed(
            ctx, item_type, item_public_id, dest_path
        )
    except click.ClickException as e:
        logger.debug(
            f"Fetch from local registry failed (reason={str(e)}), trying remote registry..."
        )
        # the following might raise exception, but we don't catch it this time
        package_path = fetch_package(
            item_type, public_id=item_public_id, cwd=ctx.cwd, dest=dest_path
        )
    return package_path
