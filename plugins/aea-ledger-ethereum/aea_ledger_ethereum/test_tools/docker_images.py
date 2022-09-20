# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Constants."""
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from aea.exceptions import enforce
from aea.test_tools.docker_image import DockerImage


try:
    from docker import DockerClient
    from docker.models.containers import Container
except ImportError:
    DockerClient = Any
    Container = Any


logger = logging.getLogger(__name__)


class GanacheDockerImage(DockerImage):
    """Wrapper to Ganache Docker image."""

    def __init__(
        self,
        client: DockerClient,
        addr: str,
        port: int,
        config: Optional[Dict] = None,
        gas_limit: str = "0x9184e72a000",  # 10000000000000,
    ):
        """
        Initialize the Ganache Docker image.

        :param client: the Docker client.
        :param addr: the address.
        :param port: the port.
        :param config: optional configuration to command line.
        :param gas_limit: the gas limit for blocks.
        """
        super().__init__(client)
        self._addr = addr
        self._port = port
        self._config = config or {}
        self._gas_limit = gas_limit

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "trufflesuite/ganache:beta"

    def _make_ports(self) -> Dict:
        """Make ports dictionary for Docker."""
        return {f"{self._port}/tcp": ("0.0.0.0", self._port)}  # nosec

    def _build_command(self) -> List[str]:
        """Build command."""
        # cmd = ["--chain.hardfork=london"]  # noqa: E800
        cmd = ["--miner.blockGasLimit=" + str(self._gas_limit)]
        # cmd += ["--miner.callGasLimit=" + "0x1fffffffffffff"]  # noqa: E800
        accounts_balances = self._config.get("accounts_balances", [])
        for account, balance in accounts_balances:
            cmd += [f"--wallet.accounts='{account},{balance}'"]
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
            except Exception:  # pylint: disable=broad-except
                logger.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False
