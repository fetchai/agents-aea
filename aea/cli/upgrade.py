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
import pprint
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, cast

import click
from packaging.version import Version

import aea
from aea.cli.add import add_item
from aea.cli.eject import _eject_item
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
from aea.helpers.base import compute_specifier_from_version, find_topological_order


@click.group(invoke_without_command=True)
@click.option("--interactive/--no-interactive", default=True)
@registry_flag(
    help_local="For fetching packages only from local folder.",
    help_remote="For fetching packages only from remote registry.",
)
@click.pass_context
@check_aea_project(  # pylint: disable=unused-argument,no-value-for-parameter
    check_aea_version=False
)
def upgrade(
    click_context, local, remote, interactive
):  # pylint: disable=unused-argument
    """Upgrade the packages of the agent."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", not (local or remote))
    ctx.set_config("interactive", interactive)

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

    interactive = ctx.config.get("interactive", True)
    old_component_ids = ctx.agent_config.package_dependencies
    item_remover = ItemRemoveHelper(ctx, ignore_non_vendor=True)
    agent_items = item_remover.get_agent_dependencies_with_reverse_dependencies()
    items_to_upgrade = set()
    upgraders: Dict[PackageId, ItemUpgrader] = {}
    shared_deps: Set[PackageId] = set()
    shared_deps_to_remove = set()
    items_to_upgrade_dependencies = set()

    # update aea_version in case current framework version is
    version = Version(aea.__version__)
    if not ctx.agent_config.aea_version_specifiers.contains(version):
        old_aea_version_specifier = ctx.agent_config.aea_version
        new_aea_version_specifier = compute_specifier_from_version(version)
        click.echo(
            f"Upgrading version specifier from {old_aea_version_specifier} to {new_aea_version_specifier}."
        )
        ctx.agent_config.aea_version = new_aea_version_specifier
        ctx.dump_agent_config()

    eject_helper = InteractiveEjectHelper(ctx, agent_items, interactive=interactive)
    eject_helper.get_latest_versions()
    if len(eject_helper.item_to_new_version) == 0:
        click.echo("Everything is already up to date!")
        return
    if not eject_helper.can_eject():
        click.echo("Abort.")
        return
    eject_helper.eject()

    for package_id, deps in agent_items.items():
        if package_id in eject_helper.to_eject:
            continue

        deps.difference_update(eject_helper.to_eject)
        item_upgrader = ItemUpgrader(
            ctx, str(package_id.package_type), package_id.public_id.to_latest()
        )

        if deps:
            continue

        with suppress(UpgraderException):
            item_upgrader.check_in_requirements()
            item_upgrader.check_is_non_vendor()
            # we already computed the new version above
            # check whether the current package should be updated.
            # if so, add the upgrader to the upgraders for later use.
            if package_id in eject_helper.item_to_new_version:
                new_version = eject_helper.item_to_new_version[package_id]
                items_to_upgrade.add((package_id, new_version))
                upgraders[package_id] = item_upgrader

        items_to_upgrade_dependencies.add(package_id)
        items_to_upgrade_dependencies.update(item_upgrader.dependencies)
        shared_deps.update(item_upgrader.deps_can_not_be_removed.keys())

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

        for upgrader in upgraders.values():
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

    def check_in_requirements(self):
        """Check if we are trying to upgrade some component dependency."""
        if self.in_requirements:
            raise IsRequiredException(self.in_requirements)

    def check_is_non_vendor(self):
        """Check the package is not a vendor package."""
        if self.is_non_vendor:
            raise AlreadyActualVersionException(self.current_item_public_id.version)

    def check_not_at_latest_version(self) -> str:
        """
        Check the package is not at the actual version.

        :return: the version number.
        """
        if self.item_public_id.version != "latest":
            new_item = self.item_public_id
        else:
            new_item = get_latest_version_available_in_registry(
                self.ctx, self.item_type, self.item_public_id
            )

        if self.current_item_public_id.version == new_item.version:
            raise AlreadyActualVersionException(new_item.version)

        return new_item.version

    def check_upgrade_is_required(self) -> str:
        """
        Check upgrade is required otherwise raise UpgraderException.

        :return: new version  of the package.
        """
        self.check_in_requirements()
        self.check_is_non_vendor()
        return self.check_not_at_latest_version()

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


class InteractiveEjectHelper:
    """
    Helper class to interactively eject vendor packages.

    This is needed in the cases in which a vendor package
    prevents other packages to be upgraded.
    """

    def __init__(
        self,
        ctx: Context,
        inverse_adjacency_list: Dict[PackageId, Set[PackageId]],
        interactive: bool = True,
    ):
        """
        Initialize the class.

        :param ctx: the CLI context.
        :param inverse_adjacency_list: adjacency list of inverse dependency graph.
        :param interactive: if True, interactive.
        """
        self.ctx = ctx
        self.inverse_adjacency_list = deepcopy(inverse_adjacency_list)
        self.adjacency_list = self._reverse_adjacency_list(self.inverse_adjacency_list)
        self.interactive = interactive

        self.to_eject: List[PackageId] = []
        self.item_to_new_version: Dict[PackageId, str] = {}

    def get_latest_versions(self) -> None:
        """
        Get latest versions for every project package.

        Stores the result in 'item_to_new_version'.
        """
        for package_id in self.adjacency_list.keys():
            new_item = get_latest_version_available_in_registry(
                self.ctx, str(package_id.package_type), package_id.public_id.to_latest()
            )
            if package_id.public_id.version == new_item.version:
                continue
            new_version = new_item.version
            self.item_to_new_version[package_id] = new_version

    @staticmethod
    def _reverse_adjacency_list(
        adjacency_list: Dict[PackageId, Set[PackageId]]
    ) -> Dict[PackageId, Set[PackageId]]:
        """Compute the inverse of an adjacency list."""
        inverse_adjacency_list: Dict[PackageId, Set[PackageId]] = {}
        for v, neighbors in adjacency_list.items():
            inverse_adjacency_list.setdefault(v, set())
            for u in neighbors:
                inverse_adjacency_list.setdefault(u, set()).add(v)
        return inverse_adjacency_list

    def eject(self):
        """Eject packages."""
        for package_id in self.to_eject:
            _eject_item(self.ctx, str(package_id.package_type), package_id.public_id)

    def can_eject(self):
        """Ask to the user if packages can be ejected if needed."""
        to_upgrade = set(self.item_to_new_version.keys())
        order = find_topological_order(self.adjacency_list)
        for package_id in order:
            if package_id in self.item_to_new_version:
                # if dependency is going to be upgraded,
                # no need to do anything
                continue

            depends_on = self.adjacency_list[package_id]
            dependencies_to_upgrade = depends_on.intersection(to_upgrade)
            if len(dependencies_to_upgrade) == 0:
                # if dependencies of the package are not going to be upgraded,
                # no need to worry about its ejection.
                continue

            # if we are here, it means we need to eject the package.
            answer = False
            if self.interactive:
                answer = self._prompt(package_id, dependencies_to_upgrade)
            should_eject = answer
            if not should_eject:
                return False
            self.to_eject.append(package_id)
        return True

    @staticmethod
    def _prompt(package_id: PackageId, dependencies_to_upgrade: Set[PackageId]):
        """
        Ask the user permission for ejection of a package.

        :param package_id: the package id.
        :param dependencies_to_upgrade: the dependencies to upgrade.
        :return: True or False, depending on the answer of the user.
        """
        package_type = str(package_id.package_type).capitalize()
        message = (
            f"{package_type} {package_id.public_id} prevents the upgrade of "
            f"the following non-vendor packages:\n"
            f"{pprint.pformat(dependencies_to_upgrade)}\n"
            f"as there isn't an update available. "
            f"Would you like to eject it?"
        )
        answer = click.confirm(message, default=False)
        return answer


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
