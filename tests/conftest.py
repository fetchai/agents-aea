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
from docker.models.containers import Container

import gym

from oef.agents import AsyncioCore, OEFAgent

import pytest

from aea import AEA_DIR
from aea.cli.common import _init_cli_config
from aea.cli_gui import DEFAULT_AUTHOR
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PublicId,
)
from aea.configurations.constants import DEFAULT_CONNECTION
from aea.connections.base import Connection
from aea.connections.stub.connection import StubConnection
from aea.mail.base import Address

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.connections.oef.connection import OEFConnection
from packages.fetchai.connections.p2p_client.connection import (
    PeerToPeerClientConnection,
)
from packages.fetchai.connections.tcp.tcp_client import TCPClientConnection
from packages.fetchai.connections.tcp.tcp_server import TCPServerConnection

from .data.dummy_connection.connection import DummyConnection  # type: ignore

logger = logging.getLogger(__name__)

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
CLI_LOG_OPTION = ["-v", "OFF"]

AUTHOR = DEFAULT_AUTHOR
CONFIGURATION_SCHEMA_DIR = os.path.join(AEA_DIR, "configurations", "schemas")
AGENT_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "aea-config_schema.json"
)
SKILL_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "skill-config_schema.json"
)
CONNECTION_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "connection-config_schema.json"
)
PROTOCOL_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "protocol-config_schema.json"
)

DUMMY_ENV = gym.GoalEnv

# common public ids used in the tests
UNKNOWN_PROTOCOL_PUBLIC_ID = PublicId("unknown_author", "unknown_protocol", "0.1.0")
UNKNOWN_CONNECTION_PUBLIC_ID = PublicId("unknown_author", "unknown_connection", "0.1.0")
UNKNOWN_SKILL_PUBLIC_ID = PublicId("unknown_author", "unknown_skill", "0.1.0")
LOCAL_CONNECTION_PUBLIC_ID = PublicId("fetchai", "local", "0.1.0")
P2P_CLIENT_CONNECTION_PUBLIC_ID = PublicId("fetchai", "p2p_client", "0.1.0")
HTTP_CLIENT_CONNECTION_PUBLIC_ID = PublicId.from_str("fetchai/http_client:0.2.0")
HTTP_PROTOCOL_PUBLIC_ID = PublicId("fetchai", "http", "0.1.0")
STUB_CONNECTION_PUBLIC_ID = DEFAULT_CONNECTION
DUMMY_PROTOCOL_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")
DUMMY_CONNECTION_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")
DUMMY_SKILL_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")

contract_config_files = [
    os.path.join(
        ROOT_DIR, "aea", "contracts", "scaffold", DEFAULT_CONTRACT_CONFIG_FILE
    ),
]

protocol_config_files = [
    os.path.join(ROOT_DIR, "aea", "protocols", "default", DEFAULT_PROTOCOL_CONFIG_FILE),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "protocols",
        "fipa",
        DEFAULT_PROTOCOL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "protocols",
        "oef_search",
        DEFAULT_PROTOCOL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR, "aea", "protocols", "scaffold", DEFAULT_PROTOCOL_CONFIG_FILE
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "protocols",
        "gym",
        DEFAULT_PROTOCOL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "protocols",
        "ml_trade",
        DEFAULT_PROTOCOL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "protocols",
        "tac",
        DEFAULT_PROTOCOL_CONFIG_FILE,
    ),
]

connection_config_files = [
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "connections",
        "local",
        DEFAULT_CONNECTION_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "connections",
        "oef",
        DEFAULT_CONNECTION_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR, "aea", "connections", "scaffold", DEFAULT_CONNECTION_CONFIG_FILE
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "connections",
        "gym",
        DEFAULT_CONNECTION_CONFIG_FILE,
    ),
    os.path.join(CUR_PATH, "data", "dummy_connection", DEFAULT_CONNECTION_CONFIG_FILE),
    os.path.join(CUR_PATH, "data", "gym-connection.yaml"),
]


skill_config_files = [
    os.path.join(ROOT_DIR, "aea", "skills", "error", DEFAULT_SKILL_CONFIG_FILE),
    os.path.join(ROOT_DIR, "aea", "skills", "scaffold", DEFAULT_SKILL_CONFIG_FILE),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "carpark_client",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "carpark_detection",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR, "packages", "fetchai", "skills", "echo", DEFAULT_SKILL_CONFIG_FILE
    ),
    os.path.join(
        ROOT_DIR, "packages", "fetchai", "skills", "gym", DEFAULT_SKILL_CONFIG_FILE
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "ml_data_provider",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR, "packages", "fetchai", "skills", "ml_train", DEFAULT_SKILL_CONFIG_FILE
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "tac_control",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "tac_negotiation",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "tac_participation",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "weather_client",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(
        ROOT_DIR,
        "packages",
        "fetchai",
        "skills",
        "weather_station",
        DEFAULT_SKILL_CONFIG_FILE,
    ),
    os.path.join(CUR_PATH, "data", "dummy_skill", DEFAULT_SKILL_CONFIG_FILE),
    os.path.join(
        CUR_PATH, "data", "dummy_aea", "skills", "dummy", DEFAULT_SKILL_CONFIG_FILE
    ),
    os.path.join(CUR_PATH, "data", "dependencies_skill", DEFAULT_SKILL_CONFIG_FILE),
    os.path.join(CUR_PATH, "data", "exception_skill", DEFAULT_SKILL_CONFIG_FILE),
]


agent_config_files = [
    os.path.join(CUR_PATH, "data", "dummy_aea", DEFAULT_AEA_CONFIG_FILE),
    os.path.join(CUR_PATH, "data", "aea-config.example.yaml"),
    os.path.join(CUR_PATH, "data", "aea-config.example_w_keys.yaml"),
]


def pytest_addoption(parser):
    """Add options to the parser."""
    parser.addoption("--ci", action="store_true", default=False)
    parser.addoption(
        "--no-integration-tests",
        action="store_true",
        default=False,
        help="Skip integration tests.",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "ci: mark test as not for ci")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--ci"):
        skip_ci = pytest.mark.skip(reason="need no --ci to run")
        for item in items:
            if "ci" in item.keywords:
                item.add_marker(skip_ci)


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


class OEFHealthCheck(object):
    """A health check class."""

    def __init__(
        self,
        oef_addr: str,
        oef_port: int,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
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
        self.agent = OEFAgent(
            "check", core=self._core, oef_addr=self.oef_addr, oef_port=self.oef_port
        )
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

        t = Timer(1.5, stop_connection_attempt, args=(self,))

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
            return self._result

        except Exception as e:
            print(str(e))
            return self._result
        finally:
            t.join(1.0)
            self.agent.stop()
            self.agent.disconnect()
            self._core.stop()


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
            logger.info(
                "OEF not available yet - sleeping for {} second...".format(sleep_rate)
            )
            time.sleep(sleep_rate)

    return success


def _create_oef_docker_image(oef_addr_, oef_port_) -> Container:
    client = docker.from_env()

    logger.info(ROOT_DIR + "/tests/common/oef_search_pluto_scripts")
    ports = {
        "20000/tcp": ("0.0.0.0", 20000),  # nosec
        "30000/tcp": ("0.0.0.0", 30000),  # nosec
        "{}/tcp".format(oef_port_): ("0.0.0.0", oef_port_),  # nosec
    }
    volumes = {
        ROOT_DIR
        + "/tests/common/oef_search_pluto_scripts": {"bind": "/config", "mode": "rw"},
        ROOT_DIR + "/data/oef-logs": {"bind": "/logs", "mode": "rw"},
    }
    c = client.containers.run(
        "fetchai/oef-search:0.7",
        "/config/node_config.json",
        detach=True,
        ports=ports,
        volumes=volumes,
    )
    return c


@pytest.fixture(scope="session")
def network_node(oef_addr, oef_port, pytestconfig):
    """Network node initialization."""
    if sys.version_info < (3, 7):
        pytest.skip("Python version < 3.7 not supported by the OEF.")
    if pytestconfig.getoption("no_integration_tests"):
        pytest.skip("skipped: no OEF running")
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


def get_unused_tcp_port():
    """Get an unused TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def get_host():
    """Get the host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


@pytest.fixture(scope="session", autouse=True)
def reset_aea_cli_config() -> None:
    """Resets the cli config."""
    _init_cli_config()


def _make_dummy_connection() -> Connection:
    dummy_connection = DummyConnection()
    return dummy_connection


def _make_local_connection(
    address: Address,
    node: LocalNode,
    restricted_to_protocols=None,
    excluded_protocols=None,
) -> Connection:
    oef_local_connection = OEFLocalConnection(
        node,
        address=address,
        connection_id=PublicId("fetchai", "local", "0.1.0"),
        restricted_to_protocols=restricted_to_protocols,
        excluded_protocols=excluded_protocols,
    )
    return oef_local_connection


def _make_oef_connection(address: Address, oef_addr: str, oef_port: int):
    oef_connection = OEFConnection(
        oef_addr,
        oef_port,
        address=address,
        connection_id=PublicId("fetchai", "oef", "0.1.0"),
    )
    return oef_connection


def _make_tcp_server_connection(address: str, host: str, port: int):
    tcp_connection = TCPServerConnection(
        host, port, address=address, connection_id=PublicId("fetchai", "tcp", "0.1.0")
    )
    return tcp_connection


def _make_tcp_client_connection(address: str, host: str, port: int):
    tcp_connection = TCPClientConnection(
        host, port, address=address, connection_id=PublicId("fetchai", "tcp", "0.1.0")
    )
    return tcp_connection


def _make_p2p_client_connection(
    address: Address, provider_addr: str, provider_port: int
):
    p2p_client_connection = PeerToPeerClientConnection(
        provider_addr,
        provider_port,
        address=address,
        connection_id=PublicId("fetchai", "p2p", "0.1.0"),
    )
    return p2p_client_connection


def _make_stub_connection(input_file_path: str, output_file_path: str):
    connection = StubConnection(
        input_file_path=input_file_path,
        output_file_path=output_file_path,
        connection_id=DEFAULT_CONNECTION,
    )
    return connection
