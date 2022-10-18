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

import platform
import subprocess  # nosec
from unittest import mock

import docker
import pytest

from aea.test_tools.docker_image import Container, DockerImage, launch_image


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


class TestHelloWorldImage:
    """Test Hello World"""

    image = HelloWorldImage(mock.Mock())

    @pytest.mark.parametrize("result", [None, not None])
    @pytest.mark.skipif(platform.system() == "Darwin", reason="no docker on github CI")
    def test_docker_binary_availability(self, result) -> None:
        """Test skip based on docker binary availability"""

        with mock.patch("shutil.which", return_value=result):
            with mock.patch("pytest.skip") as m:
                self.image._check_docker_binary_available()
                assert m.call_count == int(not bool(result))

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
            with mock.patch("pytest.skip") as m:
                self.image._check_docker_binary_available()
                m.assert_called_once()

    def test_stop_if_already_running(self) -> None:
        """Test stop if already running"""

        magic_mock = mock.MagicMock()
        magic_mock.image.tags = [self.image.tag]
        ContainerCollection = docker.models.containers.ContainerCollection
        with mock.patch.object(ContainerCollection, "list", return_value=[magic_mock]):
            with mock.patch.object(magic_mock, "stop"):
                any(launch_image(self.image))
                assert magic_mock.stop.call_count == 1

    @mock.patch.object(HelloWorldImage, "wait", return_value=False)
    def test_image_wait_returns_false(self, _) -> None:
        """Test wait returns False"""

        with mock.patch("pytest.fail") as m:
            any(launch_image(self.image))
            m.assert_called_once()
