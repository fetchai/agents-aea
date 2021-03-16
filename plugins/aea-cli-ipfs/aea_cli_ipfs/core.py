# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
import time
from contextlib import suppress
from typing import Any, Optional

import click
from aea_cli_ipfs.ipfs_utils import (
    DownloadError,
    IPFSTool,
    NodeError,
    PublishError,
    RemoveError,
)


@click.group()
@click.pass_context
def ipfs(click_context: click.Context) -> None:
    """IPFS Commands"""
    ipfs_tool = IPFSTool()
    click_context.obj = ipfs_tool
    try:
        ipfs_tool.chec_ipfs_node_running()
    except NodeError as e:
        click.echo("Can not connect to the local ipfs node. Starting own one.")
        ipfs_tool.daemon.start()
        for _ in range(10):
            with suppress(NodeError):  # pragma: nocover
                ipfs_tool.chec_ipfs_node_running()
                click.echo("ipfs node started.")
                break
            time.sleep(1)
        else:
            raise click.ClickException(
                "Failed to connect or start ipfs node! Please check ipfs is installed or launched!"
            ) from e


@ipfs.resultcallback()
@click.pass_context
def process_result(click_context: click.Context, *_: Any) -> None:
    """Tear down command group."""
    ipfs_tool = click_context.obj
    if ipfs_tool.daemon.is_started():  # pragma: nocover
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
    click.echo(f"Starting processing: {dir_path}")
    name, hash_, _ = ipfs_tool.add(dir_path, pin=(not no_pin))
    click.echo(f"Added: `{name}`, hash is {hash_}")
    if publish:
        click.echo("Publishing...")
        try:
            response = ipfs_tool.publish(hash_)
            click.echo(f"Published to {response['Name']}")
        except PublishError as e:
            raise click.ClickException(f"Publish failed: {str(e)}") from e


@ipfs.command()
@click.argument(
    "hash_", metavar="hash", type=str, required=True,
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
    "hash_", metavar="hash", type=str, required=True,
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
