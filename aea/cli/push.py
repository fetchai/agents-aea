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
"""Implementation of the 'aea push' subcommand."""

from pathlib import Path
from shutil import copytree
from typing import Dict, cast

import click
from aea_cli_ipfs.core import IPFSTool  # type: ignore

from aea.cli.registry.settings import (
    REGISTRY_CONFIG_KEY,
    REGISTRY_HTTP,
    REGISTRY_IPFS,
    REGISTRY_LOCAL,
)
from aea.cli.utils.click_utils import registry_flag_
from aea.cli.utils.config import get_or_create_cli_config, load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import try_get_item_target_path
from aea.configurations.base import PackageConfiguration, PublicId
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL


@click.command()
@registry_flag_()
@click.argument(
    "item_type", type=click.Choice(choices=(CONNECTION, CONTRACT, PROTOCOL, SKILL))
)
@click.argument(
    "path", type=click.Path(exists=True, dir_okay=True), default=Path(".").resolve()
)
@click.pass_context
def push(
    click_context: click.Context, registry: str, item_type: str, path: Path
) -> None:
    """Push a non-vendor package of the agent to the registry."""
    ctx = cast(Context, click_context.obj)
    cli_config = get_or_create_cli_config()
    path = Path(path).absolute()

    try:
        item_config = load_item_config(item_type, path)
    except FileNotFoundError as e:
        raise click.ClickException(f"{path} is not a valid package") from e

    if registry == REGISTRY_HTTP:
        raise click.ClickException("We don't have support for HTTP registry right now.")
    elif registry == REGISTRY_LOCAL:
        push_item_local(ctx, item_type, item_config.public_id, path, cli_config)
    else:
        push_item_ipfs(ctx, item_type, item_config, path, cli_config)


def push_item_ipfs(
    ctx: Context,
    item_type: str,
    item_config: PackageConfiguration,
    package_path: Path,
    cli_config: Dict,
) -> None:
    """Push item to IPFS registry."""

    multiaddr = cli_config[REGISTRY_CONFIG_KEY]["settings"][REGISTRY_IPFS]["ipfs_node"]
    ipfs_tool = IPFSTool(addr=multiaddr)
    _, package_hash, _ = ipfs_tool.add(package_path)

    click.echo(f"Published package with")
    click.echo(f"\t PublicId: {item_config.public_id}")
    click.echo(f"\t Hash: {package_hash}")


def push_item_local(
    ctx: Context,
    item_type: str,
    item_id: PublicId,
    package_path: Path,
    cli_config: Dict,
) -> None:
    """Save item to local packages."""

    try:
        registry_path = cli_config[REGISTRY_CONFIG_KEY]["settings"][REGISTRY_LOCAL][
            "default_registry_path"
        ]
        if registry_path is None:
            registry_path = ctx.registry_path
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))

    item_type_plural = item_type + "s"
    target_path = try_get_item_target_path(
        registry_path, item_id.author, item_type_plural, item_id.name,
    )
    copytree(package_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )
