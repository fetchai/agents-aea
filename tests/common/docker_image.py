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

"""This module contains testing utilities."""
import asyncio
import logging
import os
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from threading import Timer
from typing import Dict, List, Optional

import docker
import pytest
from docker import DockerClient
from docker.models.containers import Container
from oef.agents import OEFAgent
from oef.core import AsyncioCore

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
            pytest.skip("Docker not in the OS Path; skipping the test")

        result = subprocess.run(  # nosec
            ["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            pytest.skip(f"'docker --version' failed with exit code {result.returncode}")

        match = re.search(
            r"Docker version ([0-9]+)\.([0-9]+)\.([0-9]+)",
            result.stdout.decode("utf-8"),
        )
        if match is None:
            pytest.skip("cannot read version from the output of 'docker --version'")
        version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if version < self.MINIMUM_DOCKER_VERSION:
            pytest.skip(
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


class OEFHealthCheck(object):
    """A health check class."""

    def __init__(
        self,
        oef_addr: str,
        oef_port: int,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        Initialize.

        :param oef_addr: IP address of the OEF node.
        :param oef_port: Port of the OEF node.
        """
        self.oef_addr = oef_addr
        self.oef_port = oef_port

        self._result = False
        self._stop = False
        self._core = AsyncioCore()
        self.agent = OEFAgent(
            "check", core=self._core, oef_addr=self.oef_addr, oef_port=self.oef_port
        )
        self.agent.on_connect_success = self.on_connect_ok
        self.agent.on_connection_terminated = self.on_connect_terminated
        self.agent.on_connect_failed = self.exception_handler

    def exception_handler(self, url=None, ex=None):
        """Handle exception during a connection attempt."""
        print("An error occurred. Exception: {}".format(ex))
        self._stop = True

    def on_connect_ok(self, url=None):
        """Handle a successful connection."""
        print("Connection OK!")
        self._result = True
        self._stop = True

    def on_connect_terminated(self, url=None):
        """Handle a connection failure."""
        print("Connection terminated.")
        self._stop = True

    def run(self) -> bool:
        """
        Run the check, asynchronously.

        :return: True if the check is successful, False otherwise.
        """
        self._result = False
        self._stop = False

        def stop_connection_attempt(self):
            if self.agent.state == "connecting":
                self.agent.state = "failed"

        t = Timer(1.5, stop_connection_attempt, args=(self,))

        try:
            print("Connecting to {}:{}...".format(self.oef_addr, self.oef_port))
            self._core.run_threaded()

            t.start()
            self._result = self.agent.connect()
            self._stop = True

            if self._result:
                print("Connection established. Tearing down connection...")
                self.agent.disconnect()
                t.cancel()
            else:
                print("A problem occurred. Exiting...")
            return self._result

        except Exception as e:
            print(str(e))
            return self._result
        finally:
            t.join()
            self.agent.stop()
            self.agent.disconnect()
            self._core.stop()


class OEFSearchDockerImage(DockerImage):
    """Wrapper to OEF Search Docker image."""

    def __init__(self, client: DockerClient, oef_addr: str, oef_port: int):
        """Initialize the OEF Search Docker image."""
        super().__init__(client)
        self._oef_addr = oef_addr
        self._oef_port = oef_port

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "fetchai/oef-search:0.7"

    def check_skip(self):
        """Check if the test should be skipped."""
        super().check_skip()
        if sys.version_info < (3, 7):
            pytest.skip("Python version < 3.7 not supported by the OEF.")
            return

    def create(self) -> Container:
        """Create an instance of the OEF Search image."""
        from tests.conftest import ROOT_DIR  # pylint: disable

        logger.info(ROOT_DIR + "/tests/common/oef_search_pluto_scripts")
        ports = {
            "20000/tcp": ("0.0.0.0", 20000),  # nosec
            "30000/tcp": ("0.0.0.0", 30000),  # nosec
            "{}/tcp".format(self._oef_port): ("0.0.0.0", self._oef_port),  # nosec
        }
        volumes = {
            ROOT_DIR
            + "/tests/common/oef_search_pluto_scripts": {
                "bind": "/config",
                "mode": "rw",
            },
            ROOT_DIR + "/data/oef-logs": {"bind": "/logs", "mode": "rw"},
        }
        c = self._client.containers.run(
            self.tag,
            "/config/node_config.json",
            detach=True,
            ports=ports,
            volumes=volumes,
        )
        return c

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        success = False
        attempt = 0
        while not success and attempt < max_attempts:
            attempt += 1
            logger.info("Attempt {}...".format(attempt))
            oef_healthcheck = OEFHealthCheck("127.0.0.1", 10000)
            result = oef_healthcheck.run()
            if result:
                success = True
            else:
                logger.info(
                    "OEF not available yet - sleeping for {} second...".format(
                        sleep_rate
                    )
                )
                time.sleep(sleep_rate)

        return success


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
        run_node_lines = [
            "#!/usr/bin/env bash",
            "set -e",
            f'fetchd init {self._config["moniker"]} --chain-id {self._config["chain_id"]}',
            'sed -i "s/stake/atestfet/" ~/.fetchd/config/genesis.json',
            'sed -i "s/enable = false/enable = true/" ~/.fetchd/config/app.toml',
            f'MNEMONIC="{self._config["mnemonic"]}"',
            "fetchcli config keyring-backend test",
            f'echo $MNEMONIC | fetchcli keys add {self._config["genesis_account"]} --recover',
            f'fetchd add-genesis-account $(fetchcli keys show {self._config["genesis_account"]} -a) 1152997575000000000000000000{self._config["denom"]}',
            f'fetchd gentx --amount 100000000000000000000{self._config["denom"]} --name {self._config["genesis_account"]} --keyring-backend test',
            "fetchd collect-gentxs",
            f'fetchcli config chain-id {self._config["chain_id"]}',
            f"fetchd start --rpc.laddr tcp://0.0.0.0:{self._port} &",
            "fetchcli rest-server --trust-node=true",
        ]
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
