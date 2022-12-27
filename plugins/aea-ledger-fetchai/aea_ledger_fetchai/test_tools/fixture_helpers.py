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

"""Fixture helpers"""

from contextlib import contextmanager

import pytest
from aea_ledger_fetchai.test_tools.constants import (
    DEFAULT_FETCH_DOCKER_IMAGE_TAG,
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_RPC_PORT,
    FETCHD_CONFIGURATION,
)
from aea_ledger_fetchai.test_tools.docker_images import FetchLedgerDockerImage

from aea.test_tools.docker_image import launch_image


@pytest.fixture(scope="class")
def fetchd(  # pylint: disable=dangerous-default-value
    fetchd_configuration=FETCHD_CONFIGURATION,
    timeout: float = 2.0,
    max_attempts: int = 20,
):
    """Launch the Fetch ledger image."""
    with _fetchd_context(fetchd_configuration, timeout, max_attempts) as fetchd_image:
        yield fetchd_image


@contextmanager
def _fetchd_context(fetchd_configuration, timeout: float = 2.0, max_attempts: int = 20):
    import docker  # pylint: disable=import-outside-toplevel,import-error

    client = docker.from_env()
    image = FetchLedgerDockerImage(
        client,
        DEFAULT_FETCH_LEDGER_ADDR,
        DEFAULT_FETCH_LEDGER_RPC_PORT,
        DEFAULT_FETCH_DOCKER_IMAGE_TAG,
        config=fetchd_configuration,
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
