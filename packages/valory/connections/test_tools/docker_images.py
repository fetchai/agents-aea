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

"""ACN Docker Image."""

import logging
import socket
import time
from typing import Dict, List

from docker import DockerClient  # pylint: disable=import-error
from docker.models.containers import Container  # pylint: disable=import-error

from aea.exceptions import enforce
from aea.test_tools.docker_image import DockerImage


LOCAL_ADDRESS = "0.0.0.0"
PUBLIC_DHT_MADDRS = [
    "/dns4/0.0.0.0/tcp/10000/p2p/16Uiu2HAmMC2tJMRaRTeWSESv8mArbq6jipJCD4adSBcBLsbc7cSL"
]
PUBLIC_DHT_DELEGATE_URIS = ["localhost:11000"]
PUBLIC_DHT_PUBLIC_KEYS = [
    "037ed15dcee3a317e590cbdd28768ad8e2d29960b3e5d4eccca14bc94f83747f09"
]


BOOTSTRAP: Dict[str, str] = dict(
    AEA_P2P_ID="54562eb807d2f80df8151db0a394cac72e16435a5f64275c277cae70308e8b24",
    AEA_P2P_URI_PUBLIC=f"{LOCAL_ADDRESS}:9000",
    AEA_P2P_URI=f"{LOCAL_ADDRESS}:10000",
    AEA_P2P_DELEGATE_URI=f"{LOCAL_ADDRESS}:11000",
    AEA_P2P_URI_MONITORING=f"{LOCAL_ADDRESS}:8080",
    ACN_LOG_FILE="/acn/libp2p_node.log",
)

NODE1: Dict[str, str] = dict(
    AEA_P2P_ID="54562eb807d2f80df8151db0a394cac72e16435a5f64275c277cae70308e8b24",
    AEA_P2P_URI_PUBLIC=f"{LOCAL_ADDRESS}:9001",
    AEA_P2P_URI=f"{LOCAL_ADDRESS}:10001",
    AEA_P2P_DELEGATE_URI=f"{LOCAL_ADDRESS}:11001",
    AEA_P2P_URI_MONITORING=f"{LOCAL_ADDRESS}:8081",
    AEA_P2P_ENTRY_URIS=",".join(PUBLIC_DHT_MADDRS),
    ACN_LOG_FILE="/acn/libp2p_node.log",
)


NODE2: Dict[str, str] = dict(
    AEA_P2P_ID="54562eb807d2f80df8151db0a394cac72e16435a5f64275c277cae70308e8b24",
    AEA_P2P_URI_PUBLIC=f"{LOCAL_ADDRESS}:9002",
    AEA_P2P_URI=f"{LOCAL_ADDRESS}:10002",
    AEA_P2P_DELEGATE_URI=f"{LOCAL_ADDRESS}:11002",
    AEA_P2P_URI_MONITORING=f"{LOCAL_ADDRESS}:8082",
    AEA_P2P_ENTRY_URIS=",".join(PUBLIC_DHT_MADDRS),
    ACN_LOG_FILE="/acn/libp2p_node.log",
)


class ACNNodeDockerImage(DockerImage):
    """Wrapper to ACNNode Docker image."""

    uris: List = [
        "AEA_P2P_URI_PUBLIC",
        "AEA_P2P_URI",
        "AEA_P2P_DELEGATE_URI",
        "AEA_P2P_URI_MONITORING",
    ]

    nodes = ["bootstrap"]

    def __init__(
        self,
        client: DockerClient,
        config: Dict,
    ):
        """
        Initialize the ACNNode Docker image.

        :param client: the Docker client.
        :param config: optional configuration to command line.
        """
        super().__init__(client)
        self._config = config
        self._extra_hosts = {name: "host-gateway" for name in self.nodes}

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "valory/acn-node:v0.1.0"

    @property
    def ports(self) -> List[str]:
        """Ports"""
        return [self._config[uri].split(":")[1] for uri in self.uris]

    def _make_ports(self) -> Dict:
        """Make ports dictionary for Docker."""

        return {f"{p}/tcp": ("0.0.0.0", p) for p in self.ports}

    def create(self) -> Container:
        """Create the container."""
        container = self._client.containers.run(
            image=self.tag,
            command=["--config-from-env"],
            detach=True,
            ports=self._make_ports(),
            environment=self._config,
            extra_hosts=self._extra_hosts,
        )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""

        i, to_be_connected = 0, {self._config[uri] for uri in self.uris}
        while i < max_attempts and to_be_connected:
            i += 1
            for uri in to_be_connected:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host, port = uri.split(":")
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    enforce(result == 0, "")
                    to_be_connected.remove(uri)
                    logging.info(f"URI ready: {uri}")
                    break
                except Exception:  # pylint: disable=broad-except
                    logging.error(
                        f"Attempt {i} failed on {uri}. Retrying in {sleep_rate} seconds..."
                    )
                    time.sleep(sleep_rate)

        return not to_be_connected


class ACNWithBootstrappedEntryNodesDockerImage(ACNNodeDockerImage):
    """ACN with bootstrapped entry nodes"""

    nodes = ["bootstrap", "entry_node_1", "entry_node_2"]

    def create(self) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""

        containers = []
        configs = [BOOTSTRAP, NODE1, NODE2]

        for i, name in enumerate(self.nodes):
            # this is odd looking for now, because _make_ports()
            self._config = configs[i]
            kwargs = dict(
                image=self.tag,
                name=name,
                hostname=name,
                command=["--config-from-env"],
                detach=True,
                ports=self._make_ports(),
                environment=self._config,
                extra_hosts=self._extra_hosts,
            )
            containers.append(self._client.containers.run(**kwargs))

        return []

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        time.sleep(1)  # TOFIX
        return True
