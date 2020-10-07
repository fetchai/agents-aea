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
from collections import defaultdict
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple, cast

import click

from aea.cli.add import add_item
from aea.cli.registry.utils import get_latest_version_available_in_registry
from aea.cli.remove import remove_item
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    get_item_public_id_by_author_name,
    get_items,
    is_item_present,
)
from aea.configurations.base import (
    AgentConfig,
    ComponentType,
    PackageConfiguration,
    PackageId,
    PublicId,
)


class ItemRemoveHelper:
    """Helper to check dependencies on removing component from agent config."""

    def __init__(self, agent_config: AgentConfig) -> None:
        """Init helper."""
        self._agent_config = agent_config

    def get_agent_dependencies_with_reverse_dependencies(
        self,
    ) -> Dict[PackageId, Set[PackageId]]:
        """
        Get all reverse dependencices in agent.

        :return: dict with PackageId: and set of PackageIds that uses this package

        Return example:
        {
            PackageId(protocol, fetchai/default:0.6.0): {
                PackageId(skill, fetchai/echo:0.8.0),
                PackageId(skill, fetchai/error:0.6.0)
            },
            PackageId(connection, fetchai/stub:0.10.0): set(),
            PackageId(skill, fetchai/error:0.6.0): set(),
            PackageId(skill, fetchai/echo:0.8.0): set()}
        )
        """
        return self.get_item_dependencies_with_reverse_dependencies(
            self._agent_config, None
        )

    @staticmethod
    def get_item_config(package_id: PackageId) -> PackageConfiguration:
        """Get item config for item,_type and public_id."""
        return load_item_config(
            str(package_id.package_type),
            package_path=Path("vendor")
            / package_id.public_id.author
            / f"{str(package_id.package_type)}s"
            / package_id.public_id.name,
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
            dep_item = self.get_item_config(dep_package_id)
            for item_key, deps in self.get_item_dependencies_with_reverse_dependencies(
                dep_item, dep_package_id
            ).items():
                result[item_key] = result[item_key].union(deps)

        return result

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


@click.group(invoke_without_command=True)
@click.option("--local", is_flag=True, help="For upgrading from local folder.")
@click.pass_context
@check_aea_project
def upgrade(click_context, local):
    """Upgrade agent's component."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)

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
    click.echo("Upgrade project is not ready yet")


@clean_after
def upgrade_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Upgrade an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    agent_name = cast(str, ctx.agent_config.agent_name)
    if not _check_upgrade_is_required(ctx, item_type, item_public_id):
        raise click.ClickException(
            f"Item {item_type} {item_public_id.author}/{item_public_id.name} can not be upgraded. Aborting..."
        )

    current_item = get_item_public_id_by_author_name(
        ctx.agent_config, item_type, item_public_id.author, item_public_id.name
    )

    if (
        not current_item
    ):  # pragma: nocover  # just for mypy, it's actually checked above
        raise ValueError("No component present!")

    in_reqs, can_be_removed, can_not_be_removed = ItemRemoveHelper(
        ctx.agent_config
    ).check_remove(item_type, current_item)

    if in_reqs:
        # check if we trying to upgrade some component dependency
        raise click.ClickException(
            "Can not upgrade {} {}/{} cause it's required by {}".format(
                item_type,
                item_public_id.author,
                item_public_id.author,
                ", ".join(map(str, in_reqs)),
            )
        )

    del can_not_be_removed  # not going to remove what we can not remove

    click.echo(
        "Upgrading {} {}/{} from version {} to {} for the agent '{}'...".format(
            item_type,
            item_public_id.author,
            item_public_id.author,
            current_item.version,
            item_public_id.version,
            agent_name,
        )
    )

    remove_item(ctx, item_type, item_public_id)
    for dep_package_id in can_be_removed:
        click.echo(
            "Removing dependency {} {} for {} {}".format(
                dep_package_id.package_type,
                dep_package_id.public_id,
                item_type,
                current_item,
            )
        )
        remove_item(ctx, str(dep_package_id.package_type), dep_package_id.public_id)
    add_item(ctx, item_type, item_public_id)
    click.echo(
        "{}/{} for the agent '{}'  successfully upgraded to latest version".format(
            item_public_id.author, item_public_id.name, agent_name
        )
    )


def _check_upgrade_is_required(ctx: Context, item_type: str, item_public_id: PublicId):
    """
    Check item can be upgraded or not.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    registered_item_ids = get_items(ctx.agent_config, item_type)

    def is_item_with_version_present(public_id: PublicId) -> bool:
        if public_id.version == "latest":
            return False
        return public_id in registered_item_ids

    if not is_item_present(ctx, item_type, item_public_id):
        raise click.ClickException(
            "Error: A {} with id '{}/{}' is not registered. Please use `add` command. Aborting...".format(
                item_type, item_public_id.author, item_public_id.name
            ),
        )

    if is_item_with_version_present(item_public_id):
        raise click.ClickException(
            "The {} with id '{}/{}' already has version {}. Nothing to upgrade.".format(
                item_type,
                item_public_id.author,
                item_public_id.name,
                item_public_id.version,
            ),
        )

    current_item_public_id = get_item_public_id_by_author_name(
        ctx.agent_config, item_type, item_public_id.author, item_public_id.name
    )

    if (
        current_item_public_id is None
    ):  # pragma: nocover. already checked above, need for mypy only
        raise click.ClickException(f"Item {item_public_id} is not registered!")

    if item_public_id.version == "latest":
        item_public_id = get_latest_version_available_in_registry(
            ctx, item_type, item_public_id
        )

        if is_item_with_version_present(item_public_id):
            raise click.ClickException(
                "The {} with id '{}/{}' already has version {}. Nothing to upgrade.".format(
                    item_type,
                    item_public_id.author,
                    item_public_id.name,
                    item_public_id.version,
                )
            )

    return True
