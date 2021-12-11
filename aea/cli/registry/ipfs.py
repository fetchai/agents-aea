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

"""Module with methods for ipfs registry."""

import json
import os
from pathlib import Path
from typing import List, Optional, Union

import click

from aea.cli.utils.constants import LOCAL_REGISTRY_PATH
from aea.configurations.base import PublicId
from aea.helpers.io import open_file


def get_ipfs_hash_from_public_id(
    item_type: str, public_id: PublicId, local_registry_path: Path
) -> Optional[str]:
    """Get IPFS hash from local registry."""

    with open_file(str(local_registry_path), mode="r") as fp:
        local_registry_data = json.load(fp)

    if public_id.package_version.is_latest:
        package_versions: List[PublicId] = [
            PublicId.from_str(_public_id)
            for _public_id in local_registry_data.get(f"{item_type}s").keys()
            if public_id.same_prefix(PublicId.from_str(_public_id))
        ]
        package_versions = list(
            reversed(sorted(package_versions, key=lambda x: x.package_version))
        )
        if len(package_versions) == 0:
            return None
        public_id, *_ = package_versions

    return local_registry_data.get(f"{item_type}s").get(str(public_id), None)


def register_item_to_local_registry(
    item_type: str, public_id: Union[str, PublicId], package_hash: str
) -> None:
    """
    Add PublicId to hash mapping in the local registry.

    :param item_type: item type.
    :param public_id: public id of package.
    :param package_hash: hash of package.
    """

    local_registry_path = Path(LOCAL_REGISTRY_PATH)
    if local_registry_path.is_file():
        with open_file(local_registry_path, mode="r") as fp:
            local_registry_data = json.load(fp)
    else:
        local_registry_data = {
            "protocols": {},
            "skills": {},
            "connections": {},
            "contracts": {},
            "agents": {},
        }

    local_registry_data[f"{item_type}s"][str(public_id)] = str(package_hash)
    with open_file(local_registry_path, mode="w+") as fp:
        fp.write(json.dumps(local_registry_data, indent=2))


def fetch_ipfs(
    item_type: str,
    public_id: PublicId,
    cwd: str,  # pylint: disable=unused-argument
    dest: str,
) -> Path:
    """Fetch a package from IPFS node."""
    try:
        from aea_cli_ipfs.ipfs_utils import (  # type: ignore # pylint: disable=import-outside-toplevel
            DownloadError,
            IPFSTool,
            NodeError,
        )
    except ImportError:
        click.echo("Please install IPFS plugin.")
        raise

    local_registry_path = Path(LOCAL_REGISTRY_PATH)
    package_hash = get_ipfs_hash_from_public_id(
        item_type, public_id, local_registry_path
    )

    if package_hash is None:
        raise click.ClickException(f"Couldn't retrive hash for package {public_id}")

    ipfs_tool = IPFSTool()
    try:
        ipfs_tool.check_ipfs_node_running()
    except NodeError:
        click.echo("Can not connect to the local ipfs node. Starting own one.")
        ipfs_tool.daemon.start()

    try:
        click.echo(f"Downloading {public_id} from IPFS.")
        *_download_dir, _ = os.path.split(dest)
        download_dir = os.path.sep.join(_download_dir)
        ipfs_tool.download(package_hash, download_dir)
        package_path = Path(dest).absolute()
        ipfs_tool.daemon.stop()
        return package_path

    except DownloadError as e:  # pragma: nocover
        ipfs_tool.daemon.stop()
        raise click.ClickException(str(e)) from e
