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
"""Ipfs utils for `ipfs cli command`."""
import os
import shutil
import signal
import subprocess  # nosec
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ipfshttpclient  # type: ignore


class IPFSDaemon:
    """
    Set up the IPFS daemon.

    :raises Exception: if IPFS is not installed.
    """

    def __init__(self) -> None:
        """Initialise IPFS daemon."""
        # check we have ipfs
        self.process = None  # type: Optional[subprocess.Popen]

    def is_started(self) -> bool:
        """Check daemon was started."""
        return bool(self.process)

    def start(self) -> None:
        """Run the ipfs daemon."""
        self.process = subprocess.Popen(  # nosec
            ["ipfs", "daemon"], stdout=subprocess.PIPE, env=os.environ.copy(),
        )

    def stop(self) -> None:  # pragma: nocover
        """Terminate the ipfs daemon."""
        if self.process is None:
            return
        self.process.send_signal(signal.SIGTERM)
        self.process.wait(timeout=30)
        poll = self.process.poll()
        if poll is None:
            self.process.terminate()
            self.process.wait(2)


class BaseIPFSToolException(Exception):
    """Base ipfs tool exception."""


class RemoveError(BaseIPFSToolException):
    """Exception on remove."""


class PublishError(BaseIPFSToolException):
    """Exception on publish."""


class NodeError(BaseIPFSToolException):
    """Exception for node connection check."""


class DownloadError(BaseIPFSToolException):
    """Exception on download failed."""


class IPFSTool:
    """IPFS tool to add, publish, remove, download directories."""

    def __init__(self, client_options: Optional[Dict] = None):
        """
        Init tool.

        :param client_options: dict, options for ipfshttpclient instance.
        """
        self.client = ipfshttpclient.Client(**(client_options or {}))
        self.daemon = IPFSDaemon()

    def add(self, dir_path: str, pin: bool = True) -> Tuple[str, str, List]:
        """
        Add directory to ipfs.

        It wraps into directory.

        :param dir_path: str, path to dir to publish
        :param pin: bool, pin object or not

        :return: dir name published, hash, list of items processed
        """
        response = self.client.add(
            dir_path, pin=pin, recursive=True, wrap_with_directory=True
        )
        return response[-2]["Name"], response[-1]["Hash"], response[:-1]

    def remove(self, hash_id: str) -> Dict:
        """
        Remove dir added by it's hash.

        :param hash_id: str. hash of dir to remove

        :return: dict with unlinked items.
        """
        try:
            return self.client.pin.rm(hash_id, recursive=True)
        except ipfshttpclient.exceptions.ErrorResponse as e:
            raise RemoveError(f"Error on {hash_id} remove: {str(e)}") from e

    def download(self, hash_id: str, target_dir: str, fix_path: bool = True) -> None:
        """
        Download dir by it's hash.

        :param hash_id: str. hash of file to download
        :param target_dir: str. directory to place downloaded
        :param fix_path: bool. default True. on download don't wrap result in to hash_id directory.
        """
        if not os.path.exists(target_dir):  # pragma: nocover
            os.makedirs(target_dir, exist_ok=True)

        if os.path.exists(os.path.join(target_dir, hash_id)):  # pragma: nocover
            raise DownloadError(f"{hash_id} was already downloaded to {target_dir}")

        self.client.get(hash_id, target_dir)

        downloaded_path = str(Path(target_dir) / hash_id)

        if fix_path:
            # self.client.get creates result with hash name
            # and content, but we want content in the target dir
            try:
                for each_file in Path(downloaded_path).iterdir():  # grabs all files
                    shutil.move(str(each_file), target_dir)
            except shutil.Error as e:  # pragma: nocover
                raise DownloadError(f"error on move files {str(e)}") from e

        os.rmdir(downloaded_path)

    def publish(self, hash_id: str) -> Dict:
        """
        Publish directory by it's hash id.

        :param hash_id: hash of the directory to publish.

        :return: dict of names it was publish for.
        """
        try:
            return self.client.name.publish(hash_id)
        except ipfshttpclient.exceptions.TimeoutError as e:  # pragma: nocover
            raise PublishError(
                "can not publish within timeout, check internet connection!"
            ) from e

    def chec_ipfs_node_running(self) -> None:
        """Check ipfs node running."""
        try:
            self.client.id()
        except ipfshttpclient.exceptions.CommunicationError as e:
            raise NodeError(f"Can not connect to node. Is node running?:\n{e}") from e
