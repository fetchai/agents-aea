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
"""Implementation of the 'aea remove' subcommand."""

import os
import shutil
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple, cast

import click

from aea.aea_builder import AEABuilder
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import get_item_public_id_by_author_name
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    DEFAULT_AEA_CONFIG_FILE,
    PackageConfiguration,
    PackageId,
    PublicId,
)


@click.group()
@click.option(
    "-w",
    "--with-dependencies",
    is_flag=True,
    help="Remove obsolete dependencies not required anymore.",
)
@click.pass_context
@check_aea_project
def remove(click_context, with_dependencies):  # pylint: disable=unused-argument
    """Remove a resource from the agent."""
    ctx = cast(Context, click_context.obj)
    if with_dependencies:
        ctx.set_config("with_dependencies", True)


@remove.command()
@click.argument("connection_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """
    Remove a connection from the agent.

    It expects the public id of the connection to remove from the local registry.
    """
    remove_item(ctx, "connection", connection_id)


@remove.command()
@click.argument("contract_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_id):
    """
    Remove a contract from the agent.

    It expects the public id of the contract to remove from the local registry.
    """
    remove_item(ctx, "contract", contract_id)


@remove.command()
@click.argument("protocol_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """
    Remove a protocol from the agent.

    It expects the public id of the protocol to remove from the local registry.
    """
    remove_item(ctx, "protocol", protocol_id)


@remove.command()
@click.argument("skill_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """
    Remove a skill from the agent.

    It expects the public id of the skill to remove from the local registry.
    """
    remove_item(ctx, "skill", skill_id)


class ItemRemoveHelper:
    """Helper to check dependencies on removing component from agent config."""

    def __init__(self, agent_config: AgentConfig) -> None:
        """Init helper."""
        self._agent_config = agent_config

    def get_agent_dependencies_with_reverse_dependencies(
        self,
    ) -> Dict[PackageId, Set[PackageId]]:
        """
        Get all reverse dependencies in agent.

        :return: dict with PackageId: and set of PackageIds that uses this package

        Return example:
        {
            PackageId(protocol, fetchai/pck1:0.1.0): {
                PackageId(skill, fetchai/pck2:0.2.0),
                PackageId(skill, fetchai/pck3:0.3.0)
            },
            PackageId(connection, fetchai/pck4:0.1.0): set(),
            PackageId(skill, fetchai/pck5:0.1.0): set(),
            PackageId(skill, fetchai/pck6:0.2.0): set()}
        )
        """
        return self.get_item_dependencies_with_reverse_dependencies(
            self._agent_config, None
        )

    @classmethod
    def get_item_config(cls, package_id: PackageId) -> PackageConfiguration:
        """Get item config for item,_type and public_id."""

        item_config = load_item_config(
            str(package_id.package_type),
            package_path=cls.get_component_directory(package_id),
        )
        if (package_id.author != item_config.author) or (
            package_id.name != item_config.name
        ):
            raise click.ClickException(
                f"Error loading {package_id} configuration, author/name do not match: {item_config.public_id}"
            )
        return item_config

    @staticmethod
    def get_component_directory(package_id: PackageId) -> Path:
        """Return path for package."""
        try:
            return AEABuilder.find_component_directory_from_component_id(
                Path("."),
                ComponentId(str(package_id.package_type), package_id.public_id),
            )

        except ValueError:
            raise click.ClickException(
                f"Can not find folder for the package: {package_id.package_type} {package_id.public_id}"
            )

    @staticmethod
    def _get_item_requirements(
        item: PackageConfiguration,
    ) -> Generator[PackageId, None, None]:
        """
        List all the requiemenents for item provided.

        :return: generator with package ids: (type, public_id)
        """
        for item_type in map(str, ComponentType):
            items = getattr(item, f"{item_type}s", set())
            for item_public_id in items:
                yield PackageId(item_type, item_public_id)

    def get_item_dependencies_with_reverse_dependencies(
        self, item: PackageConfiguration, package_id: Optional[PackageId] = None
    ) -> Dict[PackageId, Set[PackageId]]:
        """
        Get item dependencies.

        It's recursive and provides all the sub dependencies.

        :return: dict with PackageId: and set of PackageIds that uses this package
        """
        result: defaultdict = defaultdict(set)

        for dep_package_id in self._get_item_requirements(item):
            if package_id is None:
                _ = result[dep_package_id]  # init default dict value
            else:
                result[dep_package_id].add(package_id)

            if not self.is_present_in_agent_config(dep_package_id):  # pragma: nocover
                continue

            dep_item = self.get_item_config(dep_package_id)
            for item_key, deps in self.get_item_dependencies_with_reverse_dependencies(
                dep_item, dep_package_id
            ).items():
                result[item_key] = result[item_key].union(deps)

        return result

    def is_present_in_agent_config(self, package_id: PackageId) -> bool:
        """Check item is in agent config."""
        current_item = get_item_public_id_by_author_name(
            self._agent_config,
            str(package_id.package_type),
            package_id.public_id.author,
            package_id.public_id.name,
        )
        return bool(current_item)

    def check_remove(
        self, item_type: str, item_public_id: PublicId
    ) -> Tuple[Set[PackageId], Set[PackageId], Dict[PackageId, Set[PackageId]]]:
        """
        Check item can be removed from agent.

        required by - set of components that requires this component
        can be deleted - set of dependencies used only by component so can be deleted
        can not be deleted  - dict - keys - packages can not be deleted, values are set of packages requireed by.

        :return: Tuple[required by, can be deleted, can not be deleted.]
        """
        package_id = PackageId(item_type, item_public_id)
        item = self.get_item_config(package_id)
        agent_deps = self.get_agent_dependencies_with_reverse_dependencies()
        item_deps = self.get_item_dependencies_with_reverse_dependencies(
            item, package_id
        )
        can_be_removed = set()
        can_not_be_removed = dict()

        for dep_key, deps in item_deps.items():
            if agent_deps[dep_key] == deps:
                can_be_removed.add(dep_key)
            else:
                can_not_be_removed[dep_key] = agent_deps[dep_key] - deps

        return agent_deps[package_id], can_be_removed, can_not_be_removed


@contextmanager
def remove_unused_component_configurations(ctx: Context):
    """
    Remove all component configurations for items not registered and dump agent config.

    Context manager!
    Clean all configurations on enter, restore actual configurations and dump agent config.
    """
    saved_configuration = ctx.agent_config.component_configurations
    ctx.agent_config.component_configurations = {}
    try:
        yield
    finally:
        saved_configuration_by_component_prefix = {
            key.component_prefix: value for key, value in saved_configuration.items()
        }
        for component_id in ctx.agent_config.package_dependencies:
            if component_id.component_prefix in saved_configuration_by_component_prefix:
                ctx.agent_config.component_configurations[
                    component_id
                ] = saved_configuration_by_component_prefix[
                    component_id.component_prefix
                ]

    with open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as f:
        ctx.agent_loader.dump(ctx.agent_config, f)


class RemoveItem:
    """Implementation of item remove from the project."""

    def __init__(
        self,
        ctx: Context,
        item_type: str,
        item_id: PublicId,
        with_dependencies: bool,
        force: bool = False,
    ) -> None:
        """
        Init remove item tool.

        :param ctx: click context.
        :param item_type: str, package type
        :param item_id: PublicId of the item to remove.
        :param force: bool. if True remove even required by another package.

        :return: None
        """
        self.ctx = ctx
        self.force = force
        self.item_type = item_type
        self.item_id = item_id
        self.with_dependencies = with_dependencies
        self.item_type_plural = "{}s".format(item_type)
        self.item_name = item_id.name

        self.current_item = self.get_current_item()
        self.required_by: Set[PackageId] = set()
        self.dependencies_can_be_removed: Set[PackageId] = set()
        try:
            (
                self.required_by,
                self.dependencies_can_be_removed,
                *_,
            ) = ItemRemoveHelper(self.agent_config).check_remove(
                self.item_type, self.current_item
            )
        except FileNotFoundError:  # pragma: nocover
            pass  # item registered but not present on filesystem

    def get_current_item(self) -> PublicId:
        """Return public id of the item already presents in agent config."""
        current_item = get_item_public_id_by_author_name(
            self.ctx.agent_config,
            self.item_type,
            self.item_id.author,
            self.item_id.name,
        )
        if not current_item:  # pragma: nocover # actually checked in check_item_present
            raise click.ClickException(
                "The {} '{}' is not supported.".format(self.item_type, self.item_id)
            )
        return current_item

    def remove(self) -> None:
        """Remove item and it's dependencies if specified."""
        click.echo(
            "Removing {item_type} '{item_name}' from the agent '{agent_name}'...".format(
                agent_name=self.agent_name,
                item_type=self.item_type,
                item_name=self.item_name,
            )
        )
        self.remove_item()
        if self.with_dependencies:
            self.remove_dependencies()
        click.echo(
            "{item_type} '{item_name}' was removed from the agent '{agent_name}'...".format(
                agent_name=self.agent_name,
                item_type=self.item_type,
                item_name=self.item_name,
            )
        )

    @property
    def agent_items(self) -> Set[PublicId]:
        """Return items registered with agent of the same type as item."""
        return getattr(self.agent_config, self.item_type_plural, set)

    @property
    def is_required_by(self) -> bool:
        """Is required by any other registered component in the agent."""
        return bool(self.required_by)

    def remove_item(self) -> None:
        """
        Remove item.

        Removed from the filesystem.
        Removed from the agent configuration

        Does not remove dependencies, please use `remove_dependencies`.
        """
        if (not self.force) and self.is_required_by:
            raise click.ClickException(
                f"Package {self.item_type} {self.item_id} can not be removed because it is required by {','.join(map(str, self.required_by))}"
            )
        self._remove_package()
        self._remove_from_config()

    @property
    def cwd(self) -> str:
        """Get current workdir."""
        return self.ctx.cwd

    @property
    def agent_config(self) -> AgentConfig:
        """Get agent config from context."""
        return self.ctx.agent_config

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self.ctx.agent_config.agent_name

    def _get_item_folder(self) -> Path:
        """Get item package folder."""
        return Path(self.cwd) / ItemRemoveHelper.get_component_directory(
            PackageId(self.item_type, self.item_id)
        )

    def _remove_package(self) -> None:
        """Remove package from filesystem."""
        item_folder = self._get_item_folder()
        try:
            shutil.rmtree(item_folder)
        except BaseException:
            raise click.ClickException(
                f"An error occurred during {item_folder} removing."
            )

    def _remove_from_config(self) -> None:
        """Remove item from agent config."""
        current_item = self.get_current_item()
        logger.debug(
            "Removing the {} from {}".format(self.item_type, DEFAULT_AEA_CONFIG_FILE)
        )
        self.agent_items.remove(current_item)
        self.agent_config.component_configurations.pop(
            ComponentId(self.item_type, current_item), None
        )
        self._dump_agent_config()

    def _dump_agent_config(self) -> None:
        """Save agent config to the filesystem."""
        with open(os.path.join(self.ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as f:
            self.ctx.agent_loader.dump(self.agent_config, f)

    def remove_dependencies(self) -> None:
        """Remove all the dependecies related only to the package."""
        if not self.dependencies_can_be_removed:
            return
        click.echo(
            f"Removing obsolete dependencies for {self.agent_name}: {self.dependencies_can_be_removed}..."
        )
        for dependency in self.dependencies_can_be_removed:
            RemoveItem(
                self.ctx,
                str(dependency.package_type),
                dependency.public_id,
                with_dependencies=False,
                force=True,
            ).remove_item()
            click.echo(
                f"{str(dependency.package_type).capitalize()} {dependency.public_id} was removed from {self.agent_name}."
            )


def remove_item(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Remove an item from the configuration file and agent, given the public id.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_id: item public ID.

    :return: None
    :raises ClickException: if some error occures.
    """
    with remove_unused_component_configurations(ctx):
        RemoveItem(
            ctx, item_type, item_id, cast(bool, ctx.config.get("with_dependencies"))
        ).remove()
