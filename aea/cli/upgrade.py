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
"""Implementation of the 'aea upgrade' subcommand."""
from contextlib import suppress
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, cast

import click

from aea.cli.add import add_item
from aea.cli.registry.utils import get_latest_version_available_in_registry
from aea.cli.remove import (
    ItemRemoveHelper,
    RemoveItem,
    remove_unused_component_configurations,
)
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    get_item_public_id_by_author_name,
    is_item_present,
    update_references,
)
from aea.configurations.base import ComponentId, PackageId, PackageType, PublicId
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL, VENDOR
from aea.exceptions import enforce


@click.group(invoke_without_command=True)
@registry_flag(
    help_local="For fetching packages only from local folder.",
    help_remote="For fetching packages only from remote registry.",
)
@click.pass_context
@check_aea_project
def upgrade(click_context, local, remote):  # pylint: disable=unused-argument
    """Upgrade the packages of the agent."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", not (local or remote))

    if click_context.invoked_subcommand is None:
        upgrade_project(ctx)


@upgrade.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId):
    """Upgrade a connection of the agent."""
    upgrade_item(ctx, CONNECTION, connection_public_id)


@upgrade.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId):
    """Upgrade a contract of the agent."""
    upgrade_item(ctx, CONTRACT, contract_public_id)


@upgrade.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id):
    """Upgrade a protocol of the agent."""
    upgrade_item(ctx, PROTOCOL, protocol_public_id)


@upgrade.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId):
    """Upgrade a skill of the agent."""
    upgrade_item(ctx, SKILL, skill_public_id)


@clean_after
def upgrade_project(ctx: Context) -> None:  # pylint: disable=unused-argument
    """Perform project upgrade."""
    click.echo("Starting project upgrade...")

    old_component_ids = ctx.agent_config.package_dependencies
    item_remover = ItemRemoveHelper(ctx, ignore_non_vendor=True)
    agent_items = item_remover.get_agent_dependencies_with_reverse_dependencies()
    items_to_upgrade = set()
    upgraders: List[ItemUpgrader] = []
    shared_deps: Set[PackageId] = set()
    shared_deps_to_remove = set()
    items_to_upgrade_dependencies = set()

    for package_id, deps in agent_items.items():
        item_upgrader = ItemUpgrader(
            ctx, str(package_id.package_type), package_id.public_id.to_latest()
        )

        if deps:
            continue

        with suppress(UpgraderException):
            new_version = item_upgrader.check_upgrade_is_required()
            items_to_upgrade.add((package_id, new_version))
            upgraders.append(item_upgrader)

        items_to_upgrade_dependencies.add(package_id)
        items_to_upgrade_dependencies.update(item_upgrader.dependencies)
        shared_deps.update(item_upgrader.deps_can_not_be_removed.keys())

    if not items_to_upgrade:
        click.echo("Everything is already up to date!")
        return

    for dep in shared_deps:
        if agent_items[dep] - items_to_upgrade_dependencies:
            # shared deps not resolved, nothing to do next
            continue  # pragma: nocover
        # add it to remove
        shared_deps_to_remove.add(dep)

    with remove_unused_component_configurations(ctx):
        if shared_deps_to_remove:
            for dep in shared_deps_to_remove:  # pragma: nocover
                if ItemUpgrader(
                    ctx, str(dep.package_type), dep.public_id
                ).is_non_vendor:
                    # non vendor package, do not remove!
                    continue
                click.echo(
                    f"Removing shared dependency {str(dep.package_type)} '{dep.public_id}'..."
                )
                RemoveItem(
                    ctx,
                    str(dep.package_type),
                    dep.public_id,
                    with_dependencies=False,
                    force=True,
                ).remove_item()
                click.echo(
                    f"Successfully removed {str(dep.package_type)} '{dep.public_id}'."
                )

        for upgrader in upgraders:
            upgrader.remove_item()
            upgrader.add_item()

        # load new package dependencies
        replacements = _compute_replacements(ctx, old_component_ids)
        update_references(ctx, replacements)

    click.echo("Finished project upgrade. Everything is up to date now!")


class UpgraderException(Exception):
    """Base upgrader exception."""


class NotAddedException(UpgraderException):
    """Item was not found in agent cause not added."""


class AlreadyActualVersionException(UpgraderException):
    """Actual version already installed."""

    def __init__(self, version: str):
        """Init exception."""
        super().__init__(version)
        self.version = version


class IsRequiredException(UpgraderException):
    """Package can not be upgraded cause required by another."""

    def __init__(self, required_by: Iterable[PackageId]):
        """Init exception."""
        super().__init__(required_by)
        self.required_by = required_by


class ItemUpgrader:
    """Tool to upgrade agent's item ."""

    def __init__(self, ctx: Context, item_type: str, item_public_id: PublicId) -> None:
        """
        Init item upgrader.

        :param ctx: context
        :param item_type: str, type of the package
        :param item_public_id: item to upgrade.
        """
        self.ctx = ctx
        self.ctx.set_config("with_dependencies", True)
        self.item_type = item_type
        self.item_public_id = item_public_id
        self.component_id = ComponentId(self.item_type, self.item_public_id)
        self.current_item_public_id = self.get_current_item()
        (
            self.in_requirements,
            self.deps_can_be_removed,
            self.deps_can_not_be_removed,
        ) = self.get_dependencies()
        self.dependencies: Set[PackageId] = set()
        self.dependencies.update(self.deps_can_be_removed)
        self.dependencies.update(self.deps_can_not_be_removed)

    def get_current_item(self) -> PublicId:
        """Return public id of the item already presents in agent config."""
        self.check_item_present()
        current_item = get_item_public_id_by_author_name(
            self.ctx.agent_config,
            self.item_type,
            self.item_public_id.author,
            self.item_public_id.name,
        )
        if not current_item:  # pragma: nocover # actually checked in check_item_present
            raise ValueError("Item not found!")
        return current_item

    def check_item_present(self) -> None:
        """Check item going to be upgraded already registered in agent."""
        if not is_item_present(
            self.ctx, self.item_type, self.item_public_id
        ) and not is_item_present(
            self.ctx, self.item_type, self.item_public_id, is_vendor=False
        ):
            raise NotAddedException()

    def get_dependencies(
        self,
    ) -> Tuple[Set[PackageId], Set[PackageId], Dict[PackageId, Set[PackageId]]]:
        """
        Return dependency details for item.

        :return: same as for ItemRemoveHelper.check_remove
        """
        return ItemRemoveHelper(self.ctx, ignore_non_vendor=True).check_remove(
            self.item_type, self.current_item_public_id
        )

    @property
    def is_non_vendor(self) -> bool:
        """Check is package specified is non vendor."""
        path = ItemRemoveHelper.get_component_directory(
            PackageId(self.item_type, self.item_public_id)
        )
        return VENDOR not in Path(path).parts[:2]

    def check_upgrade_is_required(self) -> str:
        """
        Check upgrade is required otherwise raise UpgraderException.

        :return: new version  of the package.
        """
        if self.in_requirements:
            # check if we trying to upgrade some component dependency
            raise IsRequiredException(self.in_requirements)

        if self.is_non_vendor:
            raise AlreadyActualVersionException(self.current_item_public_id.version)

        if self.item_public_id.version != "latest":
            new_item = self.item_public_id
        else:
            new_item = get_latest_version_available_in_registry(
                self.ctx, self.item_type, self.item_public_id
            )

        if self.current_item_public_id.version == new_item.version:
            raise AlreadyActualVersionException(new_item.version)

        return new_item.version

    def remove_item(self) -> None:
        """Remove item from agent."""
        remove_item = RemoveItem(
            self.ctx,
            self.item_type,
            self.item_public_id,
            with_dependencies=True,
            force=True,
            ignore_non_vendor=True,
        )
        remove_item.remove()

    def add_item(self) -> None:
        """Add new package version to agent."""
        add_item(self.ctx, str(self.item_type), self.item_public_id)


@clean_after
def upgrade_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Upgrade an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    try:
        with remove_unused_component_configurations(ctx):
            old_component_ids = ctx.agent_config.package_dependencies
            item_upgrader = ItemUpgrader(ctx, item_type, item_public_id)
            click.echo(
                f"Upgrading {item_type} '{item_public_id.author}/{item_public_id.name}' from version '{item_upgrader.current_item_public_id.version}' to '{item_public_id.version}' for the agent '{ctx.agent_config.agent_name}'..."
            )
            version = item_upgrader.check_upgrade_is_required()

            item_upgrader.remove_item()
            item_upgrader.add_item()

            replacements = _compute_replacements(ctx, old_component_ids)
            update_references(ctx, replacements)

        click.echo(
            f"The {item_type} '{item_public_id.author}/{item_public_id.name}' for the agent '{ctx.agent_config.agent_name}' has been successfully upgraded from version '{item_upgrader.current_item_public_id.version}' to '{version}'."
        )

    except NotAddedException:
        raise click.ClickException(
            f"A {item_type} with id '{item_public_id.author}/{item_public_id.name}' is not registered. Please use the `add` command. Aborting..."
        )
    except AlreadyActualVersionException as e:
        raise click.ClickException(
            f"The {item_type} with id '{item_public_id.author}/{item_public_id.name}' already has version '{e.version}'. Nothing to upgrade."
        )
    except IsRequiredException as e:
        raise click.ClickException(
            f"Can not upgrade {item_type} '{item_public_id.author}/{item_public_id.name}' because it is required by '{', '.join(map(str, e.required_by))}'"
        )


def _compute_replacements(
    ctx: Context, old_component_ids: Set[ComponentId]
) -> Dict[ComponentId, ComponentId]:
    """Compute replacements from old component ids to new components ids."""
    agent_config = load_item_config(PackageType.AGENT.value, Path(ctx.cwd))
    new_component_ids = list(agent_config.package_dependencies)
    replacements: Dict[ComponentId, ComponentId] = dict()
    for old_component_id in old_component_ids:
        same_prefix = list(filter(old_component_id.same_prefix, new_component_ids))
        enforce(len(same_prefix) < 2, "More than one component id found.")
        if len(same_prefix) > 0:
            replacements[old_component_id] = same_prefix[0]
    return replacements
