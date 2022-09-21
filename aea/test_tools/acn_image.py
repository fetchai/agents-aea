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

from aea.exceptions import enforce
from aea.test_tools.docker_image import Container, DockerClient, DockerImage


META_ADDRESS = "0.0.0.0"  # nosec

# created agent: bootstrap_peer
#     private key: 7f669ab5eee5719e385f7aeb1973769fc75b7cbbe0850ca16c4eabe84e01afbd
#     public key:  0270475f9b78c0285a6ac6067582f5e159ec147ccb03aee16a32731f68920b1ae8
#     PeerID:      16Uiu2HAm2yxmLQTZTrxjo5c4k5ka8AVMcpeD5zMMeasE6xDw1YQw
#
# created agent: entry_node_1
#     private key: 5b8d3be9f27489040a01adc2b746b9a5f9d32ed843d99cf7d2995c8140636190
#     public key:  02197b55d736bd242311aaabb485f9db40881349873bb13e8b60c8a130ecb341d8
#     PeerID:      16Uiu2HAkw99FW2GKb2qs24eLgfXSSUjke1teDaV9km63Fv3UGdnF
#
# created agent: entry_node_2
#     private key: cc096b7be575c11d3d3d2f8a9c9be9bd59b351317b2a114ef7e014cc5a92508e
#     public key:  0287ee61e8f939aeaa69bd7156463d698f8e74a3e1d5dd20cce997970f13ad4f12
#     PeerID:      16Uiu2HAm4aHr1iKR323tca8Zu8hKStEEVwGkE2gtCJw49S3gbuVj


GENESIS_MADDR = f"/dns4/{META_ADDRESS}/tcp/9000/p2p/16Uiu2HAm2yxmLQTZTrxjo5c4k5ka8AVMcpeD5zMMeasE6xDw1YQw"

BOOTSTRAP: Dict[str, str] = dict(
    AEA_P2P_ID="7f669ab5eee5719e385f7aeb1973769fc75b7cbbe0850ca16c4eabe84e01afbd",
    AEA_P2P_URI_PUBLIC=f"{META_ADDRESS}:9000",
    AEA_P2P_URI=f"{META_ADDRESS}:9000",
    AEA_P2P_DELEGATE_URI=f"{META_ADDRESS}:11000",
    AEA_P2P_URI_MONITORING=f"{META_ADDRESS}:8080",
    ACN_LOG_FILE="/acn/libp2p_node.log",
)

NODE1: Dict[str, str] = dict(
    AEA_P2P_ID="5b8d3be9f27489040a01adc2b746b9a5f9d32ed843d99cf7d2995c8140636190",
    AEA_P2P_URI_PUBLIC=f"{META_ADDRESS}:9001",
    AEA_P2P_URI=f"{META_ADDRESS}:9001",
    AEA_P2P_DELEGATE_URI=f"{META_ADDRESS}:11001",
    AEA_P2P_URI_MONITORING=f"{META_ADDRESS}:8081",
    AEA_P2P_ENTRY_URIS=GENESIS_MADDR,
    ACN_LOG_FILE="/acn/libp2p_node.log",
)

NODE2: Dict[str, str] = dict(
    AEA_P2P_ID="cc096b7be575c11d3d3d2f8a9c9be9bd59b351317b2a114ef7e014cc5a92508e",
    AEA_P2P_URI_PUBLIC=f"{META_ADDRESS}:9002",
    AEA_P2P_URI=f"{META_ADDRESS}:9002",
    AEA_P2P_DELEGATE_URI=f"{META_ADDRESS}:11002",
    AEA_P2P_URI_MONITORING=f"{META_ADDRESS}:8082",
    AEA_P2P_ENTRY_URIS=GENESIS_MADDR,
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
        return "valory/open-acn-node:latest"

    @property
    def ports(self) -> List[str]:
        """Ports"""
        return [self._config[uri].split(":")[1] for uri in self.uris]

    def _make_ports(self) -> Dict:
        """Make ports dictionary for Docker."""

        return {f"{p}/tcp": (META_ADDRESS, p) for p in self.ports}

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


class ACNWithBootstrappedEntryNodesDockerImage(ACNNodeDockerImage):  # noqa: F401
    """ACN with bootstrapped entry nodes"""

    nodes = ["bootstrap", "entry_node_1", "entry_node_2"]
    configs = [BOOTSTRAP, NODE1, NODE2]

    def create(self) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""

        containers = []

        for name, config in zip(self.nodes, self.configs):
            kwargs = dict(
                image=self.tag,
                hostname=name,
                command=["--config-from-env"],
                detach=True,
                network="host",
                environment=config,
                extra_hosts=self._extra_hosts,
            )
            containers.append(self._client.containers.run(**kwargs))

        return containers

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait - this is container specific (using self._config) so doesn't work"""
        time.sleep(sleep_rate)
        return True
