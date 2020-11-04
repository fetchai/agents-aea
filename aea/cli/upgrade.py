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
from functools import singledispatch
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, cast

import click

from aea.cli.fetch import fetch_local_or_mixed
from aea.cli.registry.utils import get_latest_version_available_in_registry
from aea.cli.remove import (
    ItemRemoveHelper,
    RemoveItem,
    remove_unused_component_configurations,
)
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import get_non_vendor_package_path
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    get_item_public_id_by_author_name,
    is_item_present,
)
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    PackageId,
    PackageType,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.loader import ConfigLoaders


@click.group(invoke_without_command=True)
@registry_flag(
    help_local="For fetching packages only from local folder.",
    help_remote="For fetching packages only from remote registry.",
)
@click.pass_context
@check_aea_project
def upgrade(click_context, local, remote):  # pylint: disable=unused-argument
    """Upgrade agent's component."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", not (local or remote))

    if click_context.invoked_subcommand is None:
        upgrade_project(ctx)


@upgrade.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId):
    """Upgrade a connection at the configuration file."""
    upgrade_item(ctx, "connection", connection_public_id)


@upgrade.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId):
    """Upgrade a contract at the configuration file."""
    upgrade_item(ctx, "contract", contract_public_id)


@upgrade.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id):
    """Upgrade a protocol for the agent."""
    upgrade_item(ctx, "protocol", protocol_public_id)


@upgrade.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId):
    """Upgrade a skill for the agent."""
    upgrade_item(ctx, "skill", skill_public_id)


@clean_after
def upgrade_project(ctx: Context) -> None:  # pylint: disable=unused-argument
    """Perform project upgrade."""
    click.echo("Starting project upgrade...")

    item_remover = ItemRemoveHelper(ctx.agent_config)
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
            click.echo(
                f"Removing shared dependencies: {', '.join(map(str, shared_deps_to_remove))}..."
            )
            for dep in shared_deps_to_remove:  # pragma: nocover
                if ItemUpgrader(
                    ctx, str(dep.package_type), dep.public_id
                ).is_non_vendor:
                    # non vendor package, do not remove!
                    continue
                RemoveItem(
                    ctx,
                    str(dep.package_type),
                    dep.public_id,
                    with_dependencies=False,
                    force=True,
                ).remove_item()
            click.echo("Shared dependencies removed.")

        for upgrader in upgraders:
            upgrader.remove_item()
            upgrader.add_item()

        _update_references(ctx)

    click.echo("Finished project upgrade. Everything is up to date now!")
    click.echo(
        'Please manually update package versions in your non-vendor packages as well as in "default_connection" and "default_routing"'
    )


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
        return ItemRemoveHelper(self.ctx.agent_config).check_remove(
            self.item_type, self.current_item_public_id
        )

    @property
    def is_non_vendor(self) -> bool:
        """Check is package specified is non vendor."""
        path = ItemRemoveHelper.get_component_directory(
            PackageId(self.item_type, self.item_public_id)
        )
        return "vendor" not in Path(path).parts[:2]

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
        )
        remove_item.remove()
        click.echo(f"Item { self.item_type} {self.item_public_id} removed!")

    def add_item(self) -> None:
        """Add new package version to agent."""
        click.echo(f"Adding item {self.item_type} {self.item_public_id}.")
        fetch_local_or_mixed(self.ctx, str(self.item_type), self.item_public_id)


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
            item_upgrader = ItemUpgrader(ctx, item_type, item_public_id)
            click.echo(
                f"Upgrading {item_type} '{item_public_id.author}/{item_public_id.name}' from version '{item_upgrader.current_item_public_id.version}' to '{item_public_id.version}' for the agent '{ctx.agent_config.agent_name}'..."
            )
            version = item_upgrader.check_upgrade_is_required()

            item_upgrader.remove_item()
            item_upgrader.add_item()

            _update_references(ctx)

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


def _update_references(ctx: Context):
    """
    Update references after upgrade.

    First, compute the replacements; then,
    both in agent configuration and in non-vendor package configurations,
    replace the old public ids.
    """
    # index from component type to replacements
    # a replacement is a map from (package_author, package_name) to public id with the new version
    replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]] = {}
    for dependency_id in ctx.agent_config.package_dependencies:
        replacements.setdefault(dependency_id.component_type, {})[
            (dependency_id.author, dependency_id.name)
        ] = dependency_id.public_id

    _update_agent_configuration(ctx, replacements)
    _update_non_vendor_packages(ctx, replacements)


def _update_agent_configuration(
    ctx: Context, replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]]
):
    """Update agent configuration."""
    protocol_replacements = replacements.get(ComponentType.PROTOCOL, {})
    connection_replacements = replacements.get(ComponentType.CONNECTION, {})
    # update default routing
    for protocol_id, connection_id in list(ctx.agent_config.default_routing.items()):
        protocol_prefix = protocol_id.author, protocol_id.name
        connection_prefix = connection_id.author, connection_id.name

        # update protocol (if replacements provides it)
        new_protocol_id = protocol_replacements.get(protocol_prefix, protocol_id)
        old_value = ctx.agent_config.default_routing.pop(protocol_id)
        ctx.agent_config.default_routing[new_protocol_id] = old_value
        # in case needs to be used below
        protocol_id = new_protocol_id

        # update connection (if replacements provides it)
        new_connection_id = connection_replacements.get(
            connection_prefix, connection_id
        )
        ctx.agent_config.default_routing[protocol_id] = new_connection_id

    # update default connection
    if ctx.agent_config.default_connection is not None:
        default_connection_public_id = ctx.agent_config.default_connection
        default_connection_prefix = (
            default_connection_public_id.author,
            default_connection_public_id.name,
        )
        new_default_connection_public_id = replacements.get(
            ComponentType.CONNECTION, {}
        ).get(default_connection_prefix, default_connection_public_id)
        ctx.agent_config.default_connection = new_default_connection_public_id


def _update_non_vendor_packages(
    ctx: Context, replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]]
) -> None:
    """
    Update non-vendor packages.

    :param ctx: the CLI context
    :return: None
    """
    non_vendor_packages_paths = get_non_vendor_package_path(Path(ctx.cwd))
    for non_vendor_path in non_vendor_packages_paths:
        _update_non_vendor_package(non_vendor_path, replacements)


def _update_non_vendor_package(
    package_path: Path,
    replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
) -> None:
    """Update a single non-vendor package."""
    """
    A path to a non-vendor package in an AEA project is of the form:

        .../aea-project-path/package-type/package-name/

    so we need to get the second-to-last part of the path to infer the type.
    """
    type_plural = package_path.parts[-2]
    loader = ConfigLoaders.from_package_type(PackageType(type_plural[:-1]))
    path_to_config = (
        package_path / loader.configuration_class.default_configuration_filename
    )
    with path_to_config.open() as file_in:
        component_config = loader.load(file_in)
    update_dependencies(component_config, replacements)
    with path_to_config.open(mode="w") as file_out:
        loader.dump(component_config, file_out)


@singledispatch
def update_dependencies(
    _arg: ComponentConfiguration,
    _replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
):
    """Update dependencies in a component configuration."""


def _replace_component_id(
    config: ComponentConfiguration,
    types_to_update: Set[ComponentType],
    replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
):
    """Replace a component id."""
    for component_type in types_to_update:
        public_id_set = getattr(config, component_type.to_plural(), set())
        replacements_given_type = replacements.get(component_type, {})
        for old_public_id in list(public_id_set):
            old_prefix = (old_public_id.author, old_public_id.name)
            if old_prefix in replacements_given_type:
                new_public_id = replacements_given_type[old_prefix]
                public_id_set.discard(old_public_id)
                public_id_set.add(new_public_id)


@update_dependencies.register(ProtocolConfig)  # type: ignore
def _(
    _arg: ProtocolConfig,
    _replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
):
    pass


@update_dependencies.register(ConnectionConfig)  # type: ignore
def _(
    arg: ConnectionConfig,
    replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
):
    _replace_component_id(
        arg, {ComponentType.PROTOCOL, ComponentType.CONNECTION}, replacements
    )


@update_dependencies.register(ContractConfig)  # type: ignore
def _(  # type: ignore
    _arg: ContractConfig,
    _replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]],
):
    """Update contract config with new dependencies."""


@update_dependencies.register(SkillConfig)  # type: ignore
def _(
    arg: SkillConfig, replacements: Dict[ComponentType, Dict[Tuple[str, str], PublicId]]
):
    _replace_component_id(
        arg,
        {
            ComponentType.PROTOCOL,
            ComponentType.CONNECTION,
            ComponentType.CONTRACT,
            ComponentType.SKILL,
        },
        replacements,
    )
