# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Core components for `ipfs cli command`."""
import os
from glob import glob
from pathlib import Path
from typing import Any, Optional, Tuple

import click
from aea_cli_ipfs.ipfs_utils import (
    DownloadError,
    IPFSTool,
    NodeError,
    PublishError,
    RemoveError,
)
from aea_cli_ipfs.registry import register_item_to_local_registry

from aea.cli.utils.config import get_ipfs_node_multiaddr, load_item_config
from aea.configurations.constants import CONFIG_FILE_TO_PACKAGE_TYPE
from aea.helpers.cid import to_v1


@click.group()
@click.pass_context
def ipfs(click_context: click.Context) -> None:
    """IPFS Commands"""
    ipfs_tool = IPFSTool(get_ipfs_node_multiaddr())
    click_context.obj = ipfs_tool
    try:
        ipfs_tool.check_ipfs_node_running()
    except NodeError:
        click.echo("Can not connect to the local ipfs node. Starting own one.")
        ipfs_tool.daemon.start()


@ipfs.resultcallback()
@click.pass_context
def process_result(click_context: click.Context, *_: Any, **__: Any) -> None:
    """Tear down command group."""
    ipfs_tool = click_context.obj
    if ipfs_tool.daemon.is_started_internally():  # pragma: nocover
        click.echo("Stopping ipfs node launched to execute the command.")
        ipfs_tool.daemon.stop()
        click.echo("Daemon stopped.")


@ipfs.command()
@click.argument(
    "dir_path",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=False, resolve_path=True, readable=True
    ),
    required=False,
)
@click.option("-p", "--publish", is_flag=True)
@click.option("--no-pin", is_flag=True)
@click.pass_context
def add(
    click_context: click.Context,
    dir_path: Optional[str],
    publish: bool = False,
    no_pin: bool = False,
) -> None:
    """Add directory to ipfs, if not directory specified the current one will be added."""
    dir_path = dir_path or os.getcwd()
    ipfs_tool = click_context.obj
    package_hash = register_package(ipfs_tool, dir_path, no_pin)
    if publish:
        click.echo("Publishing...")
        try:
            response = ipfs_tool.publish(package_hash)
            click.echo(f"Published to {response['Name']}")
        except PublishError as e:
            raise click.ClickException(f"Publish failed: {str(e)}") from e


@ipfs.command()
@click.argument(
    "hash_",
    metavar="hash",
    type=str,
    required=True,
)
@click.pass_context
def remove(click_context: click.Context, hash_: str) -> None:
    """Remove a directory from ipfs by it's hash."""
    ipfs_tool = click_context.obj
    try:
        ipfs_tool.remove(hash_)
        click.echo(f"{hash_} was removed successfully")
    except RemoveError as e:
        raise click.ClickException(f"Remove error: {str(e)}") from e


@ipfs.command()
@click.argument(
    "hash_",
    metavar="hash",
    type=str,
    required=True,
)
@click.argument(
    "target_dir",
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
    required=False,
)
@click.pass_context
def download(
    click_context: click.Context, hash_: str, target_dir: Optional[str]
) -> None:
    """Download directory by it's hash, if not target directory specified will use current one."""
    target_dir = target_dir or os.getcwd()
    ipfs_tool = click_context.obj
    click.echo(f"Download {hash_} to {target_dir}")
    try:
        ipfs_tool.download(hash_, target_dir)
        click.echo("Download complete!")
    except DownloadError as e:  # pragma: nocover
        raise click.ClickException(str(e)) from e


def _get_path_data(dir_path: str) -> Optional[Tuple[str, str]]:
    """
    Returns the file path for item config file.

    :param dir_path: directory path.
    :return: package path and item type.
    """

    yaml_files = glob(str(Path(dir_path) / "*.yaml"))
    for config_file_path in yaml_files:
        package_path, config_file = os.path.split(config_file_path)
        if config_file in CONFIG_FILE_TO_PACKAGE_TYPE.keys():
            return (package_path, CONFIG_FILE_TO_PACKAGE_TYPE[config_file])
    return None


def register_package(
    ipfs_tool: IPFSTool,
    dir_path: str,
    no_pin: bool,
) -> str:
    """
    Register package to IPFS registry.

    :param ipfs_tool: instance of IPFSTool.
    :param dir_path: package directory.
    :param no_pin: pin object or not.
    :return: package hash
    """

    click.echo(f"Processing package: {dir_path}")
    name, package_hash, _ = ipfs_tool.add(dir_path, pin=(not no_pin))
    package_hash = to_v1(package_hash)
    path_data = _get_path_data(dir_path)
    if path_data is not None:
        package_path, item_type = path_data
        package_path_ = Path(package_path)
        item_config = load_item_config(item_type=item_type, package_path=package_path_)
        register_item_to_local_registry(
            item_type=item_type,
            public_id=item_config.public_id,
            package_hash=package_hash,
        )
        click.echo(
            f"Registered item with:\n\titem_type: {item_type}\n\tpublic id : {item_config.public_id}\n\thash : {package_hash}"
        )
    else:
        click.echo(f"Added: `{name}`, hash is {package_hash}")
    return package_hash
