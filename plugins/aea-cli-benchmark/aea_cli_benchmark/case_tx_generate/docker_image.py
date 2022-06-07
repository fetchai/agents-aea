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
"""This module contains testing utilities."""
import logging
import os
import re
import shutil
import subprocess  # nosec
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import docker
from docker import DockerClient
from docker.models.containers import Container

from aea.exceptions import enforce
from aea.helpers import http_requests as requests


logger = logging.getLogger(__name__)


class DockerImage(ABC):
    """A class to wrap interatction with a Docker image."""

    MINIMUM_DOCKER_VERSION = (19, 0, 0)

    def __init__(self, client: docker.DockerClient):
        """Initialize."""
        self._client = client

    def check_skip(self):
        """
        Check whether the test should be skipped.

        By default, nothing happens.
        """
        self._check_docker_binary_available()

    def _check_docker_binary_available(self):
        """Check the 'Docker' CLI tool is in the OS PATH."""
        result = shutil.which("docker")
        if result is None:
            raise Exception("Docker not in the OS Path; skipping the test")

        result = subprocess.run(  # nosec
            ["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise Exception(
                f"'docker --version' failed with exit code {result.returncode}"
            )

        match = re.search(
            r"Docker version ([0-9]+)\.([0-9]+)\.([0-9]+)",
            result.stdout.decode("utf-8"),
        )
        if match is None:
            raise Exception("cannot read version from the output of 'docker --version'")
        version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if version < self.MINIMUM_DOCKER_VERSION:
            raise Exception(
                f"expected Docker version to be at least {'.'.join(self.MINIMUM_DOCKER_VERSION)}, found {'.'.join(version)}"
            )

    @property
    @abstractmethod
    def tag(self) -> str:
        """Return the tag of the image."""

    def stop_if_already_running(self):
        """Stop the running images with the same tag, if any."""
        client = docker.from_env()
        for container in client.containers.list():
            if self.tag in container.image.tags:
                logger.info(f"Stopping image {self.tag}...")
                container.stop()

    @abstractmethod
    def create(self) -> Container:
        """Instantiate the image in a container."""

    @abstractmethod
    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """
        Wait until the image is running.

        :param max_attempts: max number of attempts.
        :param sleep_rate: the amount of time to sleep between different requests.
        :return: True if the wait was successful, False otherwise.
        """
        return True


class GanacheDockerImage(DockerImage):
    """Wrapper to Ganache Docker image."""

    def __init__(
        self,
        client: DockerClient,
        addr: str,
        port: int,
        config: Optional[Dict] = None,
        gas_limit: int = 10000000000000,
    ):
        """
        Initialize the Ganache Docker image.

        :param client: the Docker client.
        :param addr: the address.
        :param port: the port.
        :param config: optional configuration to command line.
        :param gas_limit: gas limit.
        """
        super().__init__(client)
        self._addr = addr
        self._port = port
        self._config = config or {}
        self._gas_limit = gas_limit

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "trufflesuite/ganache-cli:latest"

    def _make_ports(self) -> Dict:
        """Make ports dictionary for Docker."""
        return {f"{self._port}/tcp": ("0.0.0.0", self._port)}  # nosec

    def _build_command(self) -> List[str]:
        """Build command."""
        cmd = ["ganache-cli"]
        cmd += ["--gasLimit=" + str(self._gas_limit)]
        accounts_balances = self._config.get("accounts_balances", [])
        for account, balance in accounts_balances:
            cmd += [f"--account='{account},{balance}'"]
        return cmd

    def create(self) -> Container:
        """Create the container."""
        cmd = self._build_command()
        container = self._client.containers.run(
            self.tag, command=cmd, detach=True, ports=self._make_ports()
        )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        request = dict(jsonrpc=2.0, method="web3_clientVersion", params=[], id=1)
        for i in range(max_attempts):
            try:
                response = requests.post(f"{self._addr}:{self._port}", json=request)
                enforce(response.status_code == 200, "")
                return True
            except Exception:
                logger.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False


class FetchLedgerDockerImage(DockerImage):
    """Wrapper to Fetch ledger Docker image."""

    PORTS = {1317: 1317, 26657: 26657}

    def __init__(
        self,
        client: DockerClient,
        addr: str,
        port: int,
        tag: str,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the Fetch ledger Docker image.

        :param client: the Docker client.
        :param addr: the address.
        :param port: the port.
        :param tag: image tag
        :param config: optional configuration to command line.
        """
        super().__init__(client)
        self._addr = addr
        self._port = port
        self._image_tag = tag
        self._config = config or {}

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return self._image_tag

    def _make_entrypoint_file(self, tmpdirname) -> None:
        """Make a temporary entrypoint file to setup and run the test ledger node"""
        run_node_lines = (
            "#!/usr/bin/env bash",
            # variables
            f'export VALIDATOR_KEY_NAME={self._config["genesis_account"]}',
            f'export VALIDATOR_MNEMONIC="{self._config["mnemonic"]}"',
            'export PASSWORD="12345678"',
            f'export CHAIN_ID={self._config["chain_id"]}',
            f'export MONIKER={self._config["moniker"]}',
            f'export DENOM={self._config["denom"]}',
            # Add key
            '( echo "$VALIDATOR_MNEMONIC"; echo "$PASSWORD"; echo "$PASSWORD"; ) |fetchd keys add $VALIDATOR_KEY_NAME --recover',
            # Configure node
            "fetchd init --chain-id=$CHAIN_ID $MONIKER",
            'echo "$PASSWORD" |fetchd add-genesis-account $(fetchd keys show $VALIDATOR_KEY_NAME -a) 100000000000000000000000$DENOM',
            'echo "$PASSWORD" |fetchd gentx $VALIDATOR_KEY_NAME 10000000000000000000000$DENOM --chain-id $CHAIN_ID',
            "fetchd collect-gentxs",
            # Enable rest-api
            'sed -i "s/stake/atestfet/" ~/.fetchd/config/genesis.json',
            'sed -i "s/enable = false/enable = true/" ~/.fetchd/config/app.toml',
            'sed -i "s/swagger = false/swagger = true/" ~/.fetchd/config/app.toml',
            "fetchd start",
        )

        entrypoint_file = os.path.join(tmpdirname, "run-node.sh")
        with open(entrypoint_file, "w") as file:
            file.writelines(line + "\n" for line in run_node_lines)
        os.chmod(entrypoint_file, 300)  # nosec

    def create(self) -> Container:
        """Create the container."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            self._make_entrypoint_file(tmpdirname)
            mount_path = "/mnt"
            volumes = {tmpdirname: {"bind": mount_path, "mode": "rw"}}
            entrypoint = os.path.join(mount_path, "run-node.sh")
            container = self._client.containers.run(
                self.tag,
                detach=True,
                network="host",
                volumes=volumes,
                entrypoint=str(entrypoint),
                ports=self.PORTS,
            )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        for i in range(max_attempts):
            try:
                url = f"{self._addr}:{self._port}/net_info?"
                response = requests.get(url)
                enforce(response.status_code == 200, "")
                return True
            except Exception:
                logger.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False
