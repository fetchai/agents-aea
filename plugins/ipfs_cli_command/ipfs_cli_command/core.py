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
from typing import Optional

import click
from ipfs_cli_command.ipfs_utils import IPFSTool, NodeError, PublishError, RemoveError


@click.group()
@click.pass_context
def ipfs(click_context: click.Context) -> None:
    """IPFS Commands"""
    ipfs_tool = IPFSTool()
    click_context.obj = ipfs_tool
    try:
        ipfs_tool.chec_ipfs_node_running()
    except NodeError as e:
        raise click.ClickException(f"Error connecting to node: {e}")


@ipfs.command()
@click.argument(
    "dir_path",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=False, resolve_path=True, readable=True
    ),
    required=False,
)
@click.option("-p", "--publish", is_flag=True)
@click.pass_context
def add(click_context: click.Context, dir_path: Optional[str], publish=False) -> None:
    """Add directory to ipfs, if not directory specified the current one will be added."""
    dir_path = dir_path or os.getcwd()
    ipfs_tool = click_context.obj
    click.echo(f"Starting processing: {dir_path}")
    name, hash_id, _ = ipfs_tool.add(dir_path)
    click.echo(f"Added: `{name}`, hash id is {hash_id}")
    if publish:
        click.echo("Publishing...")
        try:
            response = ipfs_tool.publish(hash_id)
            click.echo(f"Published to {', '.join(response.keys())}")
        except PublishError as e:
            raise click.ClickException(str(e)) from e


@ipfs.command()
@click.argument(
    "hash_id", metavar="hash_id", type=str, required=True,
)
@click.pass_context
def remove(click_context: click.Context, hash_id: str) -> None:
    """Remove a directory from ipfs by it's hash."""
    ipfs_tool = click_context.obj
    try:
        ipfs_tool.remove(hash_id)
        click.echo(f"{hash_id} was removed successfully")
    except RemoveError as e:
        raise click.ClickException(str(e)) from e


@ipfs.command()
@click.argument(
    "hash_id", metavar="hash_id", type=str, required=True,
)
@click.argument(
    "target_dir",
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
    required=False,
)
@click.pass_context
def download(
    click_context: click.Context, hash_id: str, target_dir: Optional[str]
) -> None:
    """Download directory by it's hash, if not target directory specified will use current one."""
    target_dir = target_dir or os.getcwd()
    ipfs_tool = click_context.obj
    click.echo(f"Download {hash_id} to {target_dir}")
    ipfs_tool.download(hash_id, target_dir)
    click.echo("Download complete!")
