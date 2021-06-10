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
"""Implementation of the 'aea publish' subcommand."""

import os
from abc import ABC, abstractmethod
from contextlib import suppress
from pathlib import Path
from shutil import copyfile
from typing import cast

import click

from aea.cli.push import _save_item_locally as _push_item_locally
from aea.cli.registry.publish import publish_agent
from aea.cli.registry.push import push_item as _push_item_remote
from aea.cli.registry.utils import get_package_meta
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.config import validate_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.exceptions import AEAConfigException
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.base import AgentConfig, CRUDCollection, PublicId
from aea.configurations.constants import (
    AGENT,
    AGENTS,
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    ITEM_TYPE_PLURAL_TO_TYPE,
    PROTOCOLS,
    SKILLS,
)


PUSH_ITEMS_FLAG = "--push-missing"


@click.command(name="publish")
@registry_flag(
    help_local="For publishing agent to local folder.",
    help_remote="For publishing agent to remote registry.",
)
@click.option(
    "--push-missing", is_flag=True, help="Push missing components to registry."
)
@click.pass_context
@check_aea_project
def publish(
    click_context: click.Context, local: bool, remote: bool, push_missing: bool
) -> None:  # pylint: disable=unused-argument
    """Publish the agent to the registry."""
    ctx = cast(Context, click_context.obj)
    _validate_pkp(ctx.agent_config.private_key_paths)
    _validate_config(ctx)

    if remote:
        _publish_agent_remote(ctx, push_missing=push_missing)
    else:
        _save_agent_locally(
            ctx, is_mixed=not local and not remote, push_missing=push_missing
        )


def _validate_config(ctx: Context) -> None:
    """
    Validate agent config.

    :param ctx: Context object.

    :raises ClickException: if validation is failed.
    """
    try:
        validate_item_config(AGENT, Path(ctx.cwd))
    except AEAConfigException as e:  # pragma: no cover
        raise click.ClickException("Failed to validate agent config. {}".format(str(e)))


def _validate_pkp(private_key_paths: CRUDCollection) -> None:
    """
    Prevent to publish agents with non-empty private_key_paths.

    :param private_key_paths: private_key_paths from agent config.
    :raises ClickException: if private_key_paths is not empty.
    """
    if private_key_paths.read_all() != []:
        raise click.ClickException(
            "You are not allowed to publish agents with non-empty private_key_paths. Use the `aea remove-key` command to remove key paths from `private_key_paths: {}` in `aea-config.yaml`."
        )


class BaseRegistry(ABC):
    """Base registry class."""

    @abstractmethod
    def check_item_present(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Check item present in registry.

        Raise ClickException if not found.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.

        :return: None
        """

    @abstractmethod
    def push_item(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Push item to registry.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.

        :return: None
        """

    def check_item_present_and_push(
        self, item_type_plural: str, public_id: PublicId
    ) -> None:
        """
        Check item present in registry and push if needed.

        Raise ClickException if not found.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.

        :return: None
        """

        with suppress(click.ClickException):
            return self.check_item_present(item_type_plural, public_id)

        try:
            self.push_item(item_type_plural, public_id)
        except Exception as e:
            raise click.ClickException(
                f"Failed to push missing item: {item_type_plural} {public_id}: {e}"
            ) from e

        try:
            self.check_item_present(item_type_plural, public_id)
        except Exception as e:
            raise click.ClickException(
                f"Failed to find item after push: {item_type_plural} {public_id}: {e}"
            ) from e


class LocalRegistry(BaseRegistry):
    """Local directory registry."""

    def __init__(self, ctx: Context):
        """Init registry."""
        self.ctx = ctx
        try:
            self.registry_path = ctx.registry_path
        except ValueError as e:  # pragma: nocover
            raise click.ClickException(str(e))

    def check_item_present(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Check item present in registry.

        Raise ClickException if not found.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.
        """
        try:
            try_get_item_source_path(
                self.registry_path, public_id.author, item_type_plural, public_id.name
            )
        except click.ClickException as e:
            raise click.ClickException(
                f"Dependency is missing. {str(e)}\nPlease push it first and then retry or use {PUSH_ITEMS_FLAG} flag to push automatically."
            )

    def push_item(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Push item to registry.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.
        """
        item_type = ITEM_TYPE_PLURAL_TO_TYPE[item_type_plural]
        _push_item_locally(self.ctx, item_type, public_id)


class MixedRegistry(LocalRegistry):
    """Mixed remote and local component registry."""

    def check_item_present(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Check item present in registry.

        Raise ClickException if not found.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.
        """
        item_type = ITEM_TYPE_PLURAL_TO_TYPE[item_type_plural]
        try:
            LocalRegistry.check_item_present(self, item_type_plural, public_id)
        except click.ClickException:
            click.echo(
                f"Can not find dependency locally: {item_type} {public_id}. Trying remote registry..."
            )

        try:
            RemoteRegistry(self.ctx).check_item_present(item_type_plural, public_id)
        except click.ClickException:
            raise click.ClickException(
                f"Can not find dependency locally or remotely: {item_type} {public_id}. Try to add flag `{PUSH_ITEMS_FLAG}` to push dependency package to the registry."
            )


class RemoteRegistry(BaseRegistry):
    """Remote components registry."""

    def __init__(self, ctx: Context) -> None:
        """Init registry."""
        self.ctx = ctx

    def check_item_present(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Check item present in registry.

        Raise ClickException if not found.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.
        """
        item_type = ITEM_TYPE_PLURAL_TO_TYPE[item_type_plural]
        try:
            get_package_meta(item_type, public_id)
        except click.ClickException as e:
            raise click.ClickException(
                f"Package not found in remote registry: {str(e)}. You can try to add {PUSH_ITEMS_FLAG} flag."
            )

    def push_item(self, item_type_plural: str, public_id: PublicId) -> None:
        """
        Push item to registry.

        :param item_type_plural: str, item type.
        :param public_id: PublicId of the item to check.
        """
        item_type = ITEM_TYPE_PLURAL_TO_TYPE[item_type_plural]
        _push_item_remote(self.ctx, item_type, public_id)


def _check_dependencies_in_registry(
    registry: BaseRegistry, agent_config: AgentConfig, push_missing: bool
) -> None:
    """Check all agent dependencies present in registry."""
    for item_type_plural in (PROTOCOLS, CONTRACTS, CONNECTIONS, SKILLS):
        dependencies = getattr(agent_config, item_type_plural)
        for public_id in dependencies:
            if push_missing:
                registry.check_item_present_and_push(item_type_plural, public_id)
            else:
                registry.check_item_present(item_type_plural, public_id)


def _save_agent_locally(
    ctx: Context, is_mixed: bool = False, push_missing: bool = False
) -> None:
    """
    Save agent to local packages.

    :param ctx: the context
    :param is_mixed: whether or not to fetch in mixed mode
    :param push_missing: bool. flag to push missing items
    """
    try:
        registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))

    registry = MixedRegistry(ctx) if is_mixed else LocalRegistry(ctx)

    _check_dependencies_in_registry(registry, ctx.agent_config, push_missing)

    item_type_plural = AGENTS

    target_dir = try_get_item_target_path(
        registry_path, ctx.agent_config.author, item_type_plural, ctx.agent_config.name,
    )
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    source_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    target_path = os.path.join(target_dir, DEFAULT_AEA_CONFIG_FILE)
    copyfile(source_path, target_path)
    click.echo(
        f'Agent "{ctx.agent_config.name}" successfully saved in packages folder.'
    )


def _publish_agent_remote(ctx: Context, push_missing: bool) -> None:
    """
    Push agent to remote registry.

    :param ctx: the context
    :param push_missing: bool. flag to push missing items
    """
    registry = RemoteRegistry(ctx)
    _check_dependencies_in_registry(registry, ctx.agent_config, push_missing)
    publish_agent(ctx)
