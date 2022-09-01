# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
import logging
import os
import tempfile
import time
from typing import Any, Dict, Optional


try:
    from docker import DockerClient
    from docker.models.containers import Container
except ImportError:
    DockerClient = Any
    Container = Any


from aea.exceptions import enforce
from aea.helpers import http_requests as requests
from aea.test_tools.docker_image import DockerImage


logger = logging.getLogger(__name__)


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
        :param tag: the tag
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
            except Exception:  # pylint: disable=broad-except
                logger.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False
