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
"""Implementation of the 'aea upgrade' subcommand."""
import pprint
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, cast

import click

import aea
from aea.cli.add import add_item
from aea.cli.eject import _eject_item
from aea.cli.registry.fetch import fetch_agent
from aea.cli.registry.utils import get_latest_version_available_in_registry
from aea.cli.remove import (
    ItemRemoveHelper,
    RemoveItem,
    remove_unused_component_configurations,
)
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import (
    dump_item_config,
    get_non_vendor_package_path,
    load_item_config,
    set_cli_author,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    get_item_public_id_by_author_name,
    is_item_present,
    update_aea_version_range,
    update_references,
)
from aea.configurations.base import ComponentId, PackageId, PackageType, PublicId
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_VERSION,
    PROTOCOL,
    SKILL,
    VENDOR,
)
from aea.exceptions import enforce
from aea.helpers.base import delete_directory_contents, find_topological_order


@click.group(invoke_without_command=True)
@click.option("-y", "--yes", is_flag=True)
@registry_flag()
@click.pass_context
@check_aea_project(  # pylint: disable=unused-argument,no-value-for-parameter
    check_aea_version=False
)
def upgrade(
    click_context: click.Context, local: bool, remote: bool, yes: bool
) -> None:  # pylint: disable=unused-argument
    """Upgrade the packages of the agent."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", not (local or remote))
    ctx.set_config("yes_by_default", yes)
    set_cli_author(click_context)

    if click_context.invoked_subcommand is None:
        upgrade_project(ctx)


@upgrade.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId) -> None:
    """Upgrade a connection of the agent."""
    upgrade_item(ctx, CONNECTION, connection_public_id)


@upgrade.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId) -> None:
    """Upgrade a contract of the agent."""
    upgrade_item(ctx, CONTRACT, contract_public_id)


@upgrade.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id: PublicId) -> None:
    """Upgrade a protocol of the agent."""
    upgrade_item(ctx, PROTOCOL, protocol_public_id)


@upgrade.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId) -> None:
    """Upgrade a skill of the agent."""
    upgrade_item(ctx, SKILL, skill_public_id)


def update_agent_config(ctx: Context) -> None:
    """
    Update agent configurations.

    In particular:
    - update aea_version in case current framework version is different
    - update author name if it is different

    :param ctx: the context.
    """
    update_aea_version_range(ctx.agent_config)
    cli_author = ctx.config.get("cli_author")
    if cli_author and ctx.agent_config.author != cli_author:
        click.echo(f"Updating author from {ctx.agent_config.author} to {cli_author}")
        ctx.agent_config._author = cli_author  # pylint: disable=protected-access
        ctx.agent_config.version = DEFAULT_VERSION

    ctx.dump_agent_config()


def update_aea_version_in_nonvendor_packages(cwd: str) -> None:
    """
    Update aea_version in non-vendor packages.

    :param cwd: the current working directory.
    """
    for package_path in get_non_vendor_package_path(Path(cwd)):
        package_type = PackageType(package_path.parent.name[:-1])
        package_config = load_item_config(package_type.value, package_path)
        update_aea_version_range(package_config)
        dump_item_config(package_config, package_path)


@clean_after
def upgrade_project(ctx: Context) -> None:  # pylint: disable=unused-argument
    """Perform project upgrade."""
    click.echo("Starting project upgrade...")
    yes_by_default = ctx.config.get("yes_by_default", False)

    # check if there is a newer version of the same project
    project_upgrader = ProjectUpgrader(ctx, yes_by_default=yes_by_default)
    if project_upgrader.upgrade():
        click.echo("Upgrade completed.")
        return

    old_component_ids = ctx.agent_config.package_dependencies
    item_remover = ItemRemoveHelper(ctx, ignore_non_vendor=True)
    agent_items = item_remover.get_agent_dependencies_with_reverse_dependencies()

    eject_helper = InteractiveEjectHelper(
        ctx, agent_items, yes_by_default=yes_by_default
    )
    eject_helper.get_latest_versions()
    if len(eject_helper.item_to_new_version) == 0:
        click.echo("Everything is already up to date!")
        return
    if not eject_helper.can_eject():
        click.echo("Abort.")
        return
    eject_helper.eject()

    update_agent_config(ctx)
    update_aea_version_in_nonvendor_packages(ctx.cwd)

    # compute the upgraders and the shared dependencies.
    required_by_relation = eject_helper.get_updated_inverse_adjacency_list()
    item_to_new_version = eject_helper.item_to_new_version
    upgraders, shared_deps_to_remove = _compute_upgraders_and_shared_deps_to_remove(
        ctx, required_by_relation, item_to_new_version
    )

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

    def __init__(self, version: str) -> None:
        """Init exception."""
        super().__init__(version)
        self.version = version


class IsRequiredException(UpgraderException):
    """Package can not be upgraded cause required by another."""

    def __init__(self, required_by: Iterable[PackageId]) -> None:
        """Init exception."""
        super().__init__(required_by)
        self.required_by = required_by


class ProjectUpgrader:
    """Helper class to upgrade agent project if was previously fetched from registry."""

    _TEMP_ALIAS = "fetched_agent"

    def __init__(self, ctx: Context, yes_by_default: bool = False) -> None:
        """Initialize the class."""
        self.ctx = ctx
        self.yes_by_default = yes_by_default

        self._current_aea_version = aea.__version__

    def upgrade(self) -> bool:
        """
        Upgrade the project by fetching from remote registry.

        :return: True if the upgrade succeeded, False otherwise.
        """
        agent_config = self.ctx.agent_config
        agent_package_id = agent_config.package_id
        click.echo(
            f"Checking if there is a newer remote version of agent package '{agent_package_id.public_id}'..."
        )
        try:
            new_item = get_latest_version_available_in_registry(
                self.ctx,
                str(agent_package_id.package_type),
                agent_package_id.public_id.to_latest(),
                aea_version=self._current_aea_version,
            )
        except click.ClickException:
            click.echo("Package not found, continuing with normal upgrade.")
            return False

        if new_item.package_version <= agent_config.public_id.package_version:  # type: ignore
            click.echo(
                f"Latest version found is '{new_item.version}' which is smaller or equal than current version '{agent_config.public_id.package_version}'. Continuing..."
            )
            return False

        current_path = Path(self.ctx.cwd).absolute()
        user_wants_to_upgrade = self._ask_user_if_wants_to_upgrade(
            new_item, current_path
        )
        if not user_wants_to_upgrade:
            return False

        click.echo(f"Upgrading project to version '{new_item.version}'")

        try:
            delete_directory_contents(current_path)
        except OSError as e:  # pragma: nocover
            raise click.ClickException(
                f"Cannot remote path {current_path}. Error: {str(e)}."
            )

        fetch_agent(self.ctx, new_item, alias=self._TEMP_ALIAS)
        self.ctx.cwd = str(current_path)
        self._unpack_fetched_agent()
        return True

    def _unpack_fetched_agent(self) -> None:
        """Unpack fetched agent in current directory and remove temporary directory."""
        current_path = Path(self.ctx.cwd)
        fetched_agent_dir = current_path / self._TEMP_ALIAS
        for subpath in fetched_agent_dir.iterdir():
            shutil.move(str(subpath), current_path)
        shutil.rmtree(str(fetched_agent_dir))

    def _ask_user_if_wants_to_upgrade(
        self, new_item: PublicId, current_path: Path
    ) -> bool:
        """
        Ask if the user wants to upgrade the project.

        :param new_item: the public id of the new item.
        :param current_path: the current path.
        :return: the user's answer (a boolean).
        """
        message = (
            f"Found a newer version of this project: {new_item.package_version}. "
            f"Would you like to replace this project with it? \n"
            f"Warning: the content in the current directory {current_path} will be removed"
        )
        return _try_to_confirm(message, self.yes_by_default)


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

        self._current_aea_version = aea.__version__

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
            self.ctx.cwd, self.ctx.agent_config, self.item_type, self.item_public_id
        ) and not is_item_present(
            self.ctx.cwd,
            self.ctx.agent_config,
            self.item_type,
            self.item_public_id,
            is_vendor=False,
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

    def check_in_requirements(self) -> None:
        """Check if we are trying to upgrade some component dependency."""
        if self.in_requirements:
            raise IsRequiredException(self.in_requirements)

    def check_is_non_vendor(self) -> None:
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
                self.ctx,
                self.item_type,
                self.item_public_id,
                aea_version=self._current_aea_version,
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
        yes_by_default: bool = False,
    ) -> None:
        """
        Initialize the class.

        :param ctx: the CLI context.
        :param inverse_adjacency_list: adjacency list of inverse dependency graph.
        :param yes_by_default: if True, never ask the user for confirmation.
        """
        self.ctx = ctx
        self.inverse_adjacency_list = deepcopy(inverse_adjacency_list)
        self.adjacency_list = self._reverse_adjacency_list(self.inverse_adjacency_list)
        self.yes_by_default = yes_by_default

        self._current_aea_version = aea.__version__
        self.to_eject: List[PackageId] = []
        self.item_to_new_version: Dict[PackageId, str] = {}

    def get_latest_versions(self) -> None:
        """
        Get latest versions for every project package.

        Stores the result in 'item_to_new_version'.
        """
        for package_id in self.adjacency_list.keys():
            try:
                new_item = get_latest_version_available_in_registry(
                    self.ctx,
                    str(package_id.package_type),
                    package_id.public_id.to_latest(),
                    aea_version=self._current_aea_version,
                )
            except click.ClickException:  # pragma: nocover
                continue
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

    def eject(self) -> None:
        """Eject packages."""
        for package_id in self.to_eject:
            click.echo(f"Ejecting {package_id}...")
            _eject_item(self.ctx, str(package_id.package_type), package_id.public_id)

    def get_updated_inverse_adjacency_list(self) -> Dict[PackageId, Set[PackageId]]:
        """Update inverse adjacency list by removing ejected packages."""
        result = {}
        for package_id, deps in self.inverse_adjacency_list.items():
            if package_id in self.to_eject:
                continue
            result[package_id] = deps.difference(self.to_eject)
        return result

    def can_eject(self) -> bool:
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
                continue  # pragma: nocover

            # if we are here, it means we need to eject the package.
            answer = self._prompt(package_id, dependencies_to_upgrade)
            should_eject = answer
            if not should_eject:
                return False
            click.echo(f"Package '{package_id}' scheduled for ejection.")
            self.to_eject.append(package_id)
        return True

    def _prompt(
        self, package_id: PackageId, dependencies_to_upgrade: Set[PackageId]
    ) -> bool:
        """
        Ask the user permission for ejection of a package.

        :param package_id: the package id.
        :param dependencies_to_upgrade: the dependencies to upgrade.
        :return: True or False, depending on the answer of the user.
        """
        package_type = str(package_id.package_type).capitalize()
        message = (
            f"{package_type} {package_id.public_id} prevents the upgrade of "
            f"the following vendor packages:\n"
            f"{pprint.pformat(dependencies_to_upgrade)}\n"
            f"as there isn't a compatible version available on the AEA registry. "
            f"Would you like to eject it?"
        )
        return _try_to_confirm(message, self.yes_by_default)


def _try_to_confirm(message: str, yes_by_default: bool) -> bool:
    """
    Try to prompt a question to the user.

    The actual effect of this function will be determined by "yes_by_default".

    In particular:
    - if "yes_by_default" is True, never prompt and return True.
    - if "yes_by_default" is False, ask to the user.

    :param message: the message
    :param yes_by_default: bool to override confirm
    :return: result
    """
    return click.confirm(message) if not yes_by_default else True


@clean_after
def upgrade_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Upgrade an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
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


def _compute_upgraders_and_shared_deps_to_remove(
    ctx: Context,
    required_by_relation: Dict[PackageId, Set[PackageId]],
    item_to_new_version: Dict[PackageId, str],
) -> Tuple[Dict[PackageId, ItemUpgrader], Set[PackageId]]:
    """
    Compute upgraders and shared dependencies to remove.

    :param ctx: the CLI Context
    :param required_by_relation: from a package id to the package ids it is required by.
    :param item_to_new_version: from a package id to its new version available.
    :return: the list of upgraders and the shared dependencies to remove.
    """
    upgraders: Dict[PackageId, ItemUpgrader] = {}
    shared_deps: Set[PackageId] = set()
    shared_deps_to_remove = set()
    items_to_upgrade_dependencies = set()
    for package_id, required_by in required_by_relation.items():
        item_upgrader = ItemUpgrader(
            ctx, str(package_id.package_type), package_id.public_id.to_latest()
        )

        # if the package is required by at least another package, don't upgrade.
        is_required_by_other = len(required_by) != 0
        if is_required_by_other:
            continue

        is_not_in_requirements = not item_upgrader.in_requirements
        is_vendor = not item_upgrader.is_non_vendor
        to_be_upgraded = package_id in item_to_new_version

        if is_not_in_requirements and is_vendor and to_be_upgraded:
            upgraders[package_id] = item_upgrader

        items_to_upgrade_dependencies.add(package_id)
        items_to_upgrade_dependencies.update(item_upgrader.dependencies)
        shared_deps.update(item_upgrader.deps_can_not_be_removed.keys())

    for dep in shared_deps:
        if required_by_relation[dep] - items_to_upgrade_dependencies:
            # shared dependencies not resolved, nothing to do next
            continue  # pragma: nocover
        # add it to remove
        shared_deps_to_remove.add(dep)
    return upgraders, shared_deps_to_remove
