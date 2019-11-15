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

"""Conftest module for Pytest."""
import asyncio
import inspect
import logging
import os
import socket
import sys
import time
from threading import Timer
from typing import Optional

import docker as docker
import pytest
from docker.models.containers import Container
from oef.agents import AsyncioCore, OEFAgent

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope
from aea import AEA_DIR

logger = logging.getLogger(__name__)

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
CLI_LOG_OPTION = ["-v", "OFF"]

CONFIGURATION_SCHEMA_DIR = os.path.join(AEA_DIR, "configurations", "schemas")
AGENT_CONFIGURATION_SCHEMA = os.path.join(CONFIGURATION_SCHEMA_DIR, "aea-config_schema.json")
SKILL_CONFIGURATION_SCHEMA = os.path.join(CONFIGURATION_SCHEMA_DIR, "skill-config_schema.json")
CONNECTION_CONFIGURATION_SCHEMA = os.path.join(CONFIGURATION_SCHEMA_DIR, "connection-config_schema.json")
PROTOCOL_CONFIGURATION_SCHEMA = os.path.join(CONFIGURATION_SCHEMA_DIR, "protocol-config_schema.json")


def pytest_addoption(parser):
    """Add options to the parser."""
    parser.addoption("--ci", action="store_true", default=False)
    parser.addoption("--no-integration-tests", action="store_true", default=False, help="Skip integration tests.")


@pytest.fixture(scope="session")
def oef_addr() -> str:
    """IP address pointing to the OEF Node to use during the tests."""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def oef_port() -> int:
    """Port of the connection to the OEF Node to use during the tests."""
    return 10000


def tcpping(ip, port) -> bool:
    """Ping TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception as e:
        logger.exception(e)
        return False


class DummyConnection(Connection):
    """A dummy connection that just stores the messages."""

    def __init__(self):
        """Initialize."""
        super().__init__(connection_id="dummy")
        self.connection_status.is_connected = False
        self._queue = None

    async def connect(self, *args, **kwargs):
        """Connect."""
        self._queue = asyncio.Queue(loop=self.loop)
        self.connection_status.is_connected = True

    async def disconnect(self, *args, **kwargs):
        """Disconnect."""
        self.connection_status.is_connected = False

    async def send(self, envelope: 'Envelope'):
        """Send an envelope."""
        self._queue.put_nowait(envelope)

    async def recv(self, *args, **kwargs) -> Optional['Envelope']:
        """Receive an envelope."""
        try:
            return await self._queue.get()
        except Exception as e:
            print(str(e))
            await asyncio.sleep(0.5)
            return None

    def put(self, envelope: Envelope):
        """Put an envelope in the queue."""
        self._queue.put_nowait(envelope)

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Return a connection obj fom a configuration."""


class OEFHealthCheck(object):
    """A health check class."""

    def __init__(self, oef_addr: str, oef_port: int, loop: Optional[asyncio.AbstractEventLoop] = None):
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
        self.agent = OEFAgent("check", core=self._core, oef_addr=self.oef_addr, oef_port=self.oef_port)
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

        t = Timer(1.5, stop_connection_attempt, args=(self, ))

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

        except Exception as e:
            print(str(e))
        finally:
            t.join(1.0)
            self.agent.stop()
            self.agent.disconnect()
            self._core.stop()
            return self._result


def _stop_oef_search_images():
    """Stop the OEF search image."""
    client = docker.from_env()
    for container in client.containers.list():
        if "fetchai/oef-search:0.7" in container.image.tags:
            logger.info("Stopping existing Docker image...")
            container.stop()


def _wait_for_oef(max_attempts: int = 15, sleep_rate: float = 1.0):
    """Wait until the OEF is up."""
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
            logger.info("OEF not available yet - sleeping for {} second...".format(sleep_rate))
            time.sleep(sleep_rate)

    return success


def _create_oef_docker_image(oef_addr_, oef_port_) -> Container:
    client = docker.from_env()

    logger.info(ROOT_DIR + '/tests/common/oef_search_pluto_scripts')
    ports = {'20000/tcp': ("0.0.0.0", 20000), '30000/tcp': ("0.0.0.0", 30000),
             '{}/tcp'.format(oef_port_): ("0.0.0.0", oef_port_)}
    volumes = {ROOT_DIR + '/tests/common/oef_search_pluto_scripts': {'bind': '/config', 'mode': 'rw'}, ROOT_DIR + '/data/oef-logs': {'bind': '/logs', 'mode': 'rw'}}
    c = client.containers.run("fetchai/oef-search:0.7",
                              "/config/node_config.json",
                              detach=True, ports=ports, volumes=volumes)
    return c


@pytest.fixture(scope="session")
def network_node(oef_addr, oef_port, pytestconfig):
    """Network node initialization."""
    if sys.version_info < (3, 7):
        pytest.skip("Python version < 3.7 not supported by the OEF.")
    if pytestconfig.getoption("no_integration_tests"):
        pytest.skip('skipped: no OEF running')
        return

    if pytestconfig.getoption("ci"):
        logger.warning("Skipping creation of OEF Docker image...")
        success = _wait_for_oef(max_attempts=10, sleep_rate=2.0)
        if not success:
            pytest.fail("OEF doesn't work. Exiting...")
        else:
            yield
            return
    else:
        _stop_oef_search_images()
        c = _create_oef_docker_image(oef_addr, oef_port)
        c.start()

        # wait for the setup...
        logger.info("Setting up the OEF node...")
        success = _wait_for_oef(max_attempts=10, sleep_rate=2.0)

        if not success:
            c.stop()
            c.remove()
            pytest.fail("OEF doesn't work. Exiting...")
        else:
            logger.info("Done!")
            time.sleep(1.0)
            yield
            logger.info("Stopping the OEF node...")
            c.stop()
            c.remove()
