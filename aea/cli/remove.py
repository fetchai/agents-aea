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
"""Implementation of the 'aea remove' subcommand."""
import os
import shutil
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple, cast

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import load_item_config, try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import (
    get_item_public_id_by_author_name,
    is_item_present,
)
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    PackageConfiguration,
    PackageId,
    PublicId,
)
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.configurations.manager import find_component_directory_from_component_id
from aea.helpers.io import open_file


@click.group()
@click.option(
    "-w",
    "--with-dependencies",
    is_flag=True,
    help="Remove obsolete dependencies not required anymore.",
)
@click.pass_context
@check_aea_project(check_aea_version=False)  # type: ignore  # pylint: disable=no-value-for-parameter
def remove(
    click_context: click.Context, with_dependencies: bool
) -> None:  # pylint: disable=unused-argument
    """Remove a package from the agent."""
    ctx = cast(Context, click_context.obj)
    if with_dependencies:
        ctx.set_config("with_dependencies", True)


@remove.command()
@click.argument("connection_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id: PublicId) -> None:
    """Remove a connection from the agent."""
    remove_item(ctx, CONNECTION, connection_id)


@remove.command()
@click.argument("contract_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_id: PublicId) -> None:
    """Remove a contract from the agent."""
    remove_item(ctx, CONTRACT, contract_id)


@remove.command()
@click.argument("protocol_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id: PublicId) -> None:
    """Remove a protocol from the agent."""
    remove_item(ctx, PROTOCOL, protocol_id)


@remove.command()
@click.argument("skill_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id: PublicId) -> None:
    """Remove a skill from the agent."""
    remove_item(ctx, SKILL, skill_id)


class ItemRemoveHelper:
    """Helper to check dependencies on removing component from agent config."""

    def __init__(self, ctx: Context, ignore_non_vendor: bool = False) -> None:
        """Init helper."""
        self._ctx = ctx
        self._agent_config = ctx.agent_config
        self._ignore_non_vendor = ignore_non_vendor

    def get_agent_dependencies_with_reverse_dependencies(
        self,
    ) -> Dict[PackageId, Set[PackageId]]:
        """
        Get all reverse dependencies in agent.

        :return: dict with PackageId: and set of PackageIds that uses this package

        Return example:
        {
            PackageId(protocol, open_aea/pck1:0.1.0): {
                PackageId(skill, open_aea/pck2:0.2.0),
                PackageId(skill, open_aea/pck3:0.3.0)
            },
            PackageId(connection, open_aea/pck4:0.1.0): set(),
            PackageId(skill, open_aea/pck5:0.1.0): set(),
            PackageId(skill, open_aea/pck6:0.2.0): set()}
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
            return find_component_directory_from_component_id(
                Path("."),
                ComponentId(str(package_id.package_type), package_id.public_id),
            )

        except ValueError:
            raise click.ClickException(
                f"Can not find folder for the package: {package_id.package_type} {package_id.public_id}"
            )

    def _get_item_requirements(
        self, item: PackageConfiguration, ignore_non_vendor: bool = False
    ) -> Generator[PackageId, None, None]:
        """
        List all the requirements for item provided.

        :param item: the item package configuration
        :param ignore_non_vendor: whether or not to ignore vendor packages
        :yield: package ids: (type, public_id)
        """
        for item_type in map(str, ComponentType):
            items = getattr(item, f"{item_type}s", set())
            for item_public_id in items:
                if ignore_non_vendor and is_item_present(
                    self._ctx.cwd,
                    self._ctx.agent_config,
                    item_type,
                    item_public_id,
                    is_vendor=False,
                ):
                    continue
                yield PackageId(item_type, item_public_id)

    def get_item_dependencies_with_reverse_dependencies(
        self, item: PackageConfiguration, package_id: Optional[PackageId] = None
    ) -> Dict[PackageId, Set[PackageId]]:
        """
        Get item dependencies.

        It's recursive and provides all the sub dependencies.

        :param item: the item package configuration
        :param package_id: the package id.
        :return: dict with PackageId: and set of PackageIds that uses this package
        """
        result: defaultdict = defaultdict(set)

        for dep_package_id in self._get_item_requirements(
            item, self._ignore_non_vendor
        ):
            if package_id is None:
                _ = result[dep_package_id.without_hash()]  # init default dict value
            else:
                result[dep_package_id.without_hash()].add(package_id.without_hash())

            if not self.is_present_in_agent_config(
                dep_package_id.without_hash()
            ):  # pragma: nocover
                continue

            dep_item = self.get_item_config(dep_package_id)
            for item_key, deps in self.get_item_dependencies_with_reverse_dependencies(
                dep_item, dep_package_id
            ).items():
                result[item_key.without_hash()] = result[item_key].union(deps)

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
        can not be deleted  - dict - keys - packages can not be deleted, values are set of packages required by.

        :param item_type: the item type.
        :param item_public_id: the item public id.
        :return: Tuple[required by, can be deleted, can not be deleted.]
        """
        package_id = PackageId(item_type, item_public_id).without_hash()
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
def remove_unused_component_configurations(ctx: Context) -> Generator:
    """
    Remove all component configurations for items not registered and dump agent config.

    Context manager!
    Clean all configurations on enter, restore actual configurations and dump agent config.

    :param ctx: click context
    :yield: None
    """
    saved_configuration = ctx.agent_config.component_configurations
    ctx.agent_config.component_configurations = {}
    try:
        yield
    finally:
        saved_configuration_by_component_prefix = {
            key.component_prefix: value for key, value in saved_configuration.items()
        }
        # need to reload agent configuration with the updated references
        try_to_load_agent_config(ctx)
        for component_id in ctx.agent_config.package_dependencies:
            if component_id.component_prefix in saved_configuration_by_component_prefix:
                ctx.agent_config.component_configurations[
                    component_id
                ] = saved_configuration_by_component_prefix[
                    component_id.component_prefix
                ]

    with open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as f:
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
        ignore_non_vendor: bool = False,
    ) -> None:
        """
        Init remove item tool.

        :param ctx: click context.
        :param item_type: str, package type
        :param item_id: PublicId of the item to remove.
        :param with_dependencies: whether or not to remove dependencies.
        :param force: bool. if True remove even required by another package.
        :param ignore_non_vendor: bool. if True, ignore non-vendor packages when computing inverse dependencies. The effect of this flag is ignored if force = True
        """
        self.ctx = ctx
        self.force = force
        self.ignore_non_vendor = ignore_non_vendor
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
            ) = ItemRemoveHelper(
                self.ctx, ignore_non_vendor=self.ignore_non_vendor
            ).check_remove(
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
        click.echo(f"Removing {self.item_type} '{self.current_item}'...")
        self.remove_item()
        if self.with_dependencies:
            self.remove_dependencies()
        click.echo(f"Successfully removed {self.item_type} '{self.current_item}'.")

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
    def agent_name(self) -> str:  # pragma: nocover
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
        self.ctx.dump_agent_config()

    def remove_dependencies(self) -> None:
        """Remove all the dependencies related only to the package."""
        if not self.dependencies_can_be_removed:
            return
        for dependency in self.dependencies_can_be_removed:
            click.echo(
                f"Removing obsolete dependency {str(dependency.package_type)} '{str(dependency.public_id)}'..."
            )
            RemoveItem(
                self.ctx,
                str(dependency.package_type),
                dependency.public_id,
                with_dependencies=False,
                force=True,
            ).remove_item()
            click.echo(
                f"Successfully removed {str(dependency.package_type)} '{dependency.public_id}'."
            )


def remove_item(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Remove an item from the configuration file and agent, given the public id.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_id: item public ID.
    """
    with remove_unused_component_configurations(ctx):
        RemoveItem(
            ctx, item_type, item_id, cast(bool, ctx.config.get("with_dependencies"))
        ).remove()
