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

from contextlib import contextmanager
from typing import Dict, Optional

import docker
import pytest

from aea.test_tools.docker_image import (
    Container,
    DockerClient,
    DockerImage,
    launch_image,
)


@pytest.fixture(scope="session")
def configuration():
    """Get the Ganache configuration for testing purposes."""
    return {}


class HelloWorldImage(DockerImage):
    """Wrapper to Hello World Docker image."""

    def __init__(
        self,
        client: DockerClient,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the Hello World Docker image.

        :param client: the Docker client.
        :param addr: the address.
        :param port: the port.
        :param config: optional configuration to command line.
        """
        super().__init__(client)
        self._config = config or {}

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "hello-world:latest"

    def create(self) -> Container:
        """Create the container."""
        container = self._client.containers.run(self.tag, detach=True)
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        return True


@pytest.fixture(scope="class")
def hello_world(
    configuration,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Hello World image."""
    with _context(configuration, timeout, max_attempts) as image:
        yield image


@contextmanager
def _context(
    configuration: Dict,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    client = docker.from_env()
    image = HelloWorldImage(client, config=configuration)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
