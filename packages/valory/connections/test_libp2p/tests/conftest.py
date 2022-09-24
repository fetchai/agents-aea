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

# pylint: skip-file

"""Conftest module for Pytest."""

import functools
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator

import docker
import pytest
import yaml
from docker.errors import ImageNotFound, NotFound

from aea.test_tools.docker_image import Container, DockerImage

from packages.valory.connections import p2p_libp2p_client
from packages.valory.connections.test_libp2p.tests.acn_image import (
    ACNNodeDockerImage,
    ACNWithBootstrappedEntryNodesDockerImage,
)


@dataclass
class NodeConfig:
    """Node configuration"""

    uri: str
    maddr: str
    public_key: str


DOCKER_PRINT_SEPARATOR = ("\n" + "*" * 40) * 3 + "\n"

logger = logging.getLogger(__name__)


META_ADDRESS = "0.0.0.0"  # nosec
ACN_CONFIGURATION: Dict[str, str] = dict(
    AEA_P2P_ID="54562eb807d2f80df8151db0a394cac72e16435a5f64275c277cae70308e8b24",
    AEA_P2P_URI_PUBLIC=f"{META_ADDRESS}:5000",
    AEA_P2P_URI=f"{META_ADDRESS}:5000",
    AEA_P2P_DELEGATE_URI=f"{META_ADDRESS}:11000",
    AEA_P2P_URI_MONITORING=f"{META_ADDRESS}:8080",
    ACN_LOG_FILE="/acn/libp2p_node.log",
)

local_nodes = [
    NodeConfig(
        "localhost:11001",
        f"/dns4/{META_ADDRESS}/tcp/9001/p2p/16Uiu2HAkw99FW2GKb2qs24eLgfXSSUjke1teDaV9km63Fv3UGdnF",
        "02197b55d736bd242311aaabb485f9db40881349873bb13e8b60c8a130ecb341d8",
    ),
    NodeConfig(
        "localhost:11002",
        f"/dns4/{META_ADDRESS}/tcp/9002/p2p/16Uiu2HAm4aHr1iKR323tca8Zu8hKStEEVwGkE2gtCJw49S3gbuVj",
        "0287ee61e8f939aeaa69bd7156463d698f8e74a3e1d5dd20cce997970f13ad4f12",
    ),
]


@functools.lru_cache()
def load_client_connection_yaml_config() -> Dict[str, Any]:
    """Load libp2p client connection yaml configuration"""

    connection_yaml = (
        Path(p2p_libp2p_client.__file__).absolute().parent / "connection.yaml"
    )
    config = yaml.safe_load(connection_yaml.read_text())["config"]
    dns_template = "/dns4/{domain}/tcp/{port}/p2p/{peer_id}"

    # add matching information needed in ACN libp2p tests
    port_mapping = {
        "9005": ("9003", "16Uiu2HAm9ftkcmsBwPf2KXjrUd9G6GPi2WN3opXvjrjukNpE9e5k"),
        "9006": ("9004", "16Uiu2HAmAzQL3YV2Yv37ffafuMaaPtLUSPBEoyjDyFyrcLQzgB6P"),
    }

    for node in config["nodes"]:
        domain, port = node["uri"].split(":")
        port, peer_id = port_mapping[port]
        node["maddr"] = dns_template.format(domain=domain, port=port, peer_id=peer_id)

    return config


LIBP2P_LEDGER = load_client_connection_yaml_config()["ledger_id"]
public_nodes = [
    NodeConfig(**kw) for kw in load_client_connection_yaml_config()["nodes"]
]


def _launch_image(
    image: DockerImage, timeout: float = 2.0, max_attempts: int = 10
) -> Generator:
    """Launch image."""

    image.check_skip()
    image.stop_if_already_running()
    container = image.create()
    container.start()
    logger.info(f"Setting up image {image.tag}...")
    success = image.wait(max_attempts, timeout)
    if not success:
        container.stop()
        container.remove()
        pytest.fail(f"{image.tag} doesn't work. Exiting...")
    else:
        try:
            logger.info("Done!")
            time.sleep(timeout)
            yield
        finally:
            logger.info(f"Stopping the image {image.tag}...")
            container.stop()
            container.remove()


def _pre_launch(image: DockerImage) -> None:
    """Run pre-launch checks."""
    image.check_skip()
    image.stop_if_already_running()


def _start_container(
    image: DockerImage, container, timeout: float, max_attempts: int
) -> None:
    """
    Start a container.

    :param image: an instance of Docker image.
    :param container: the container to start, created from the image.
    :param timeout: timeout to launch
    :param max_attempts: max launch attempts
    """
    container.start()
    logger.info(f"Setting up image {image.tag}...")
    success = image.wait(max_attempts, timeout)
    if not success:
        container.stop()
        logger.error(
            f"{DOCKER_PRINT_SEPARATOR}Logs from container {container.name}:\n{container.logs().decode()}"
        )
        container.remove()
        pytest.fail(f"{image.tag} doesn't work. Exiting...")
    else:
        logger.info("Done!")
        time.sleep(timeout)


def _stop_container(container: Container, tag: str) -> None:
    """Stop a container."""
    logger.info(f"Stopping container {container.name} from image {tag}...")
    container.stop()
    try:
        logger.info(
            f"{DOCKER_PRINT_SEPARATOR}Logs from container {container.name}:\n{container.logs().decode()}"
        )
        if str(container.name).startswith("node"):
            logger.info(
                f"{DOCKER_PRINT_SEPARATOR}Logs from container log file {container.name}:\n"
            )
            bits, _ = container.get_archive(f"/logs/{container.name}.txt")
            for chunk in bits:
                logger.info(chunk.decode())
    except (ImageNotFound, NotFound) as e:
        logger.error(e)
    finally:
        container.remove()


def launch_many_containers(
    image: DockerImage, timeout: float = 2.0, max_attempts: int = 10
) -> Generator[DockerImage, None, None]:
    """Launch many containers from an image."""
    _pre_launch(image)
    containers = image.create()
    for container in containers:
        _start_container(image, container, timeout, max_attempts)
    yield image
    for container in containers:
        _stop_container(container, image.tag)


@pytest.fixture(scope="session")
def acn_configuration():
    """Get the ACN Node configuration for testing purposes."""
    return ACN_CONFIGURATION


@contextmanager
def _acn_context(
    acn_configuration: Dict,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    client = docker.from_env()
    image = ACNNodeDockerImage(client, config=acn_configuration)
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="class")
def acn_node(
    acn_configuration,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the ACN image."""
    with _acn_context(acn_configuration, timeout, max_attempts) as image:
        yield image


@pytest.mark.integration
class UseACNNode:
    """Inherit from this class to an ACN Node."""

    @pytest.fixture(autouse=True)
    def _start_acn_node(self, acn_node):
        """Start a ACN Node image."""


@contextmanager
def _acn_multiple_nodes_context(
    acn_configuration: Dict,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    client = docker.from_env()
    image = ACNWithBootstrappedEntryNodesDockerImage(client, config=acn_configuration)
    yield from launch_many_containers(image, timeout, max_attempts)


@pytest.fixture(scope="class")
def acn_multiple_nodes(
    acn_configuration,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the ACN images."""
    with _acn_multiple_nodes_context(acn_configuration, timeout, max_attempts) as image:
        logging.info("Starting up local ACN nodes")
        yield image


@pytest.mark.integration
class ACNWithBootstrappedEntryNodes:
    """Inherit from this class to an ACN Node."""

    @pytest.fixture(autouse=True)
    def _start_acn(self, acn_multiple_nodes):
        """Start a series of ACN Node images."""
