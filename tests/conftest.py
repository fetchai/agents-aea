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
import time
from typing import Optional

import docker as docker
import pytest
from docker.models.containers import Container
from oef.agents import AsyncioCore, Connection

logger = logging.getLogger(__name__)

CUR_PATH = inspect.getfile(inspect.currentframe())
ROOT_DIR = os.path.join(os.path.dirname(CUR_PATH), "..")


def pytest_addoption(parser):
    """Add options to the parser."""
    parser.addoption("--ci", action="store_true", default=False)
    parser.addoption("--no-oef", action="store_true", default=False, help="Skip tests that require the OEF.")


@pytest.fixture(scope="session")
def oef_addr() -> str:
    """IP address pointing to the OEF Node to use during the tests."""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def oef_port() -> int:
    """Port of the connection to the OEF Node to use during the tests."""
    return 10000


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
        self._conn = None  # type: Optional[Connection]
        self._loop = asyncio.get_event_loop() if loop is None else loop
        self._loop.set_exception_handler(self.exception_handler)
        self._core = AsyncioCore(loop=self._loop)

    def exception_handler(self, loop, d):
        """Handle exception during a connection attempt."""
        print("An error occurred. Details: {}".format(d))
        self._stop = True

    def on_connect_ok(self, conn=None, url=None, ex=None, conn_name=None):
        """Handle a successful connection."""
        print("Connection OK!")
        self._result = True
        self._stop = True

    def on_connect_fail(self, conn=None, url=None, ex=None, conn_name=None):
        """Handle a connection failure."""
        print("Connection failed. {}".format(ex))
        self._result = False
        self._stop = True

    async def _run(self) -> bool:
        """
        Run the check, asynchronously.

        :return: True if the check is successful, False otherwise.
        """
        self._result = False
        self._stop = False
        pbk = 'check'
        seconds = 3.0
        try:
            print("Connecting to {}:{}...".format(self.oef_addr, self.oef_port))

            self._conn = Connection(self._core)
            self._conn.connect(url="127.0.0.1:10000", success=self.on_connect_ok,
                               failure=self.on_connect_fail,
                               public_key=pbk)

            while not self._stop and seconds > 0:
                await asyncio.sleep(1.0)
                seconds -= 1.0

            if self._result:
                print("Connection established. Tearing down connection...")
                self._core.call_soon_async(self._conn.do_stop)
                await asyncio.sleep(1.0)
            else:
                print("A problem occurred. Exiting...")

        except Exception as e:
            print(str(e))
        finally:
            return self._result

    def run(self) -> bool:
        """Run the check.

        :return: True if the check is successful, False otherwise.
        """
        return self._loop.run_until_complete(self._run())


def _stop_oef_search_images():
    """Stop the OEF search image."""
    client = docker.from_env()
    for container in client.containers.list():
        if "fetchai/oef-search:latest" in container.image.tags:
            logger.info("Stopping existing Docker image...")
            container.stop()


def _wait_for_oef(max_attempts: int = 15, sleep_rate: float = 1.0):
    """Wait until the OEF is up."""
    success = False
    attempt = 0
    while not success and attempt < max_attempts:
        attempt += 1
        logger.info("Attempt {}...".format(attempt))
        # oef_healthcheck = subprocess.Popen(["python3", ROOT_DIR + "/sandbox/oef_healthcheck.py", "127.0.0.1", "10000"])
        # oef_healthcheck.wait()
        # oef_healthcheck.terminate()
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
    c = client.containers.run("fetchai/oef-search:latest",
                              "/config/node_config_latest.json",
                              detach=True, ports=ports, volumes=volumes)
    return c


@pytest.fixture(scope="session")
def network_node(oef_addr, oef_port, pytestconfig):
    """Network node initialization."""
    if pytestconfig.getoption("no_oef"):
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
