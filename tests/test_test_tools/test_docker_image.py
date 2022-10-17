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

"""This module contains a test for aea.test_tools.docker_image."""

import subprocess  # nosec
from contextlib import contextmanager
from unittest import mock

import docker
import pytest

from aea.test_tools.docker_image import (
    Container,
    DockerException,
    DockerImage,
    launch_image,
)


class HelloWorldImage(DockerImage):
    """Wrapper to Hello World Docker image."""

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return "hello-world:latest"

    def create(self) -> Container:
        """Create the container."""
        return self._client.containers.run(self.tag, detach=True)

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """Wait until the image is up."""
        return True


@pytest.fixture(scope="class")
def hello_world(timeout: float = 2.0, max_attempts: int = 10):
    """Launch the Hello World image."""

    with _context(timeout, max_attempts) as image:
        yield image


@contextmanager
def _context(timeout: float = 2.0, max_attempts: int = 10):
    """Context"""

    image = HelloWorldImage(docker.from_env())
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


class TestHelloWorldImage:
    """Test Hello World"""

    image = HelloWorldImage(mock.Mock())

    @pytest.fixture(autouse=True)
    def _start_hello_world(self, hello_world) -> None:
        """Start the Hello World image."""

    @mock.patch("shutil.which", return_value=None)
    def test_docker_binary_not_available(self, _) -> None:
        """Test skip when docker binary not available"""

        self.image._check_docker_binary_available()

    @pytest.mark.parametrize(
        "proc_result",
        [
            subprocess.CompletedProcess("", 1),
            subprocess.CompletedProcess("", 0, stdout=b""),
            subprocess.CompletedProcess("", 0, stdout=b"Docker version 0.0.0,"),
        ],
    )
    def test_correct_docker_binary_not_available(self, proc_result) -> None:
        """Test skip when docker binary not available"""

        with mock.patch("subprocess.run", return_value=proc_result):
            self.image._check_docker_binary_available()

    def test_stop_if_already_running(self) -> None:
        """Test stop if already running"""

        magic_mock = mock.MagicMock()
        magic_mock.image.tags = [self.image.tag]
        ContainerCollection = docker.models.containers.ContainerCollection
        with mock.patch.object(ContainerCollection, "list", return_value=[magic_mock]):
            any(launch_image(self.image))

    @mock.patch.object(HelloWorldImage, "wait", return_value=False)
    def test_wait_returns_false(self, _) -> None:
        """Test wait returns False"""

        with pytest.raises(DockerException, match=f"{self.image.tag} doesn't work."):
            any(launch_image(self.image))
