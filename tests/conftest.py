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
import json
import logging
import os
import platform
import socket
import sys
import threading
import time
from functools import WRAPPER_ASSIGNMENTS, wraps
from pathlib import Path
from threading import Timer
from types import FunctionType, MethodType
from typing import Callable, List, Optional, Sequence, cast
from unittest.mock import patch

import docker as docker
from docker.models.containers import Container

import gym

from oef.agents import AsyncioCore, OEFAgent

import pytest

from aea import AEA_DIR
from aea.aea import AEA
from aea.cli.utils.config import _init_cli_config
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    DEFAULT_AEA_CONFIG_FILE as AGENT_YAML,
    DEFAULT_CONNECTION_CONFIG_FILE as CONNECTION_YAML,
    DEFAULT_CONTRACT_CONFIG_FILE as CONTRACT_YAML,
    DEFAULT_PROTOCOL_CONFIG_FILE as PROTOCOL_YAML,
    DEFAULT_SKILL_CONFIG_FILE as SKILL_YAML,
    PublicId,
)
from aea.configurations.constants import DEFAULT_CONNECTION
from aea.connections.base import Connection
from aea.connections.stub.connection import StubConnection
from aea.contracts import Contract, contract_registry
from aea.crypto.cosmos import _COSMOS
from aea.crypto.ethereum import _ETHEREUM
from aea.crypto.fetchai import _FETCHAI
from aea.crypto.helpers import (
    COSMOS_PRIVATE_KEY_FILE,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
)
from aea.crypto.registries import make_crypto
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.test_tools.click_testing import CliRunner as ImportedCliRunner
from aea.test_tools.constants import DEFAULT_AUTHOR

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.connections.oef.connection import OEFConnection
from packages.fetchai.connections.p2p_client.connection import (
    PeerToPeerClientConnection,
)
from packages.fetchai.connections.p2p_libp2p.connection import (
    MultiAddr,
    P2PLibp2pConnection,
)
from packages.fetchai.connections.p2p_libp2p_client.connection import (
    P2PLibp2pClientConnection,
)
from packages.fetchai.connections.tcp.tcp_client import TCPClientConnection
from packages.fetchai.connections.tcp.tcp_server import TCPServerConnection

from .data.dummy_connection.connection import DummyConnection  # type: ignore

logger = logging.getLogger(__name__)
CliRunner = ImportedCliRunner

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
CONTRACT_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "contract-config_schema.json"
)
PROTOCOL_SPEC_CONFIGURATION_SCHEMA = os.path.join(
    CONFIGURATION_SCHEMA_DIR, "protocol-specification_schema.json"
)

DUMMY_ENV = gym.GoalEnv

# Ledger identifiers
COSMOS = _COSMOS
ETHEREUM = _ETHEREUM
FETCHAI = _FETCHAI

# private keys with value on testnet
COSMOS_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", COSMOS_PRIVATE_KEY_FILE
)
ETHEREUM_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", ETHEREUM_PRIVATE_KEY_FILE
)
FETCHAI_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", FETCHAI_PRIVATE_KEY_FILE
)
FUNDED_ETH_PRIVATE_KEY_1 = (
    "0xa337a9149b4e1eafd6c21c421254cf7f98130233595db25f0f6f0a545fb08883"
)
FUNDED_ETH_PRIVATE_KEY_2 = (
    "0x04b4cecf78288f2ab09d1b4c60219556928f86220f0fb2dcfc05e6a1c1149dbf"
)
FUNDED_ETH_PRIVATE_KEY_3 = (
    "0x6F611408F7EF304947621C51A4B7D84A13A2B9786E9F984DA790A096E8260C64"
)
FUNDED_FET_PRIVATE_KEY_1 = (
    "6d56fd47e98465824aa85dfe620ad3dbf092b772abc6c6a182e458b5c56ad13b"
)
FUNDED_COSMOS_PRIVATE_KEY_1 = (
    "0aea4a45c40776f138a22655819519fe213030f6df7c14bf628fdc41de33a7c8"
)
NON_FUNDED_COSMOS_PRIVATE_KEY_1 = (
    "81b0352f99a08a754b56e529dda965c4ce974edb6db7e90035e01ed193e1b7bc"
)

# addresses with no value on testnet
COSMOS_ADDRESS_ONE = "cosmos1z4ftvuae5pe09jy2r7udmk6ftnmx504alwd5qf"
COSMOS_ADDRESS_TWO = "cosmos1gssy8pmjdx8v4reg7lswvfktsaucp0w95nk78m"
ETHEREUM_ADDRESS_ONE = "0x46F415F7BF30f4227F98def9d2B22ff62738fD68"
ETHEREUM_ADDRESS_TWO = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"
FETCHAI_ADDRESS_ONE = "Vu6aENcVSYYH9GhY1k3CsL7shWH9gKKBAWcc4ckLk5w4Ltynx"
FETCHAI_ADDRESS_TWO = "2LnTTHvGxWvKK1WfEAXnZvu81RPcMRDVQW8CJF3Gsh7Z3axDfP"

# P2P addresses
COSMOS_P2P_ADDRESS = "/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAmAzvu5uNbcnD2qaqrkSULhJsc6GJUg3iikWerJkoD72pr"  # relates to NON_FUNDED_COSMOS_PRIVATE_KEY_1
NON_GENESIS_CONFIG = {
    "delegate_uri": "127.0.0.1:11001",
    "entry_peers": [COSMOS_P2P_ADDRESS],
    "local_uri": "127.0.0.1:9001",
    "log_file": "libp2p_node.log",
    "public_uri": "127.0.0.1:9001",
}

# testnets
COSMOS_TESTNET_CONFIG = {"address": "https://rest-agent-land.prod.fetch-ai.com:443"}
ETHEREUM_TESTNET_CONFIG = {
    "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
    "gas_price": 50,
}
FETCHAI_TESTNET_CONFIG = {"network": "testnet"}
ALT_FETCHAI_CONFIG = {"host": "127.0.0.1", "port": 80}

# common public ids used in the tests
UNKNOWN_PROTOCOL_PUBLIC_ID = PublicId("unknown_author", "unknown_protocol", "0.1.0")
UNKNOWN_CONNECTION_PUBLIC_ID = PublicId("unknown_author", "unknown_connection", "0.1.0")
UNKNOWN_SKILL_PUBLIC_ID = PublicId("unknown_author", "unknown_skill", "0.1.0")
LOCAL_CONNECTION_PUBLIC_ID = PublicId("fetchai", "local", "0.1.0")
P2P_CLIENT_CONNECTION_PUBLIC_ID = PublicId("fetchai", "p2p_client", "0.1.0")
HTTP_CLIENT_CONNECTION_PUBLIC_ID = PublicId.from_str("fetchai/http_client:0.5.0")
HTTP_PROTOCOL_PUBLIC_ID = PublicId("fetchai", "http", "0.1.0")
STUB_CONNECTION_PUBLIC_ID = DEFAULT_CONNECTION
DUMMY_PROTOCOL_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")
DUMMY_CONNECTION_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")
DUMMY_SKILL_PUBLIC_ID = PublicId("dummy_author", "dummy", "0.1.0")

MAX_FLAKY_RERUNS = 3
MAX_FLAKY_RERUNS_ETH = 1
MAX_FLAKY_RERUNS_INTEGRATION = 2

FETCHAI_PREF = os.path.join(ROOT_DIR, "packages", "fetchai")
PROTOCOL_SPECS_PREF = os.path.join(ROOT_DIR, "examples", "protocol_specification_ex")

contract_config_files = [
    os.path.join(ROOT_DIR, "aea", "contracts", "scaffold", CONTRACT_YAML),
]

protocol_config_files = [
    os.path.join(ROOT_DIR, "aea", "protocols", "default", PROTOCOL_YAML),
    os.path.join(ROOT_DIR, "aea", "protocols", "scaffold", PROTOCOL_YAML),
    os.path.join(ROOT_DIR, "aea", "protocols", "signing", PROTOCOL_YAML),
    os.path.join(ROOT_DIR, "aea", "protocols", "state_update", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "contract_api", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "fipa", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "gym", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "http", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "ledger_api", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "ml_trade", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "oef_search", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "tac", PROTOCOL_YAML),
]

connection_config_files = [
    os.path.join(ROOT_DIR, "aea", "connections", "scaffold", CONNECTION_YAML),
    os.path.join(ROOT_DIR, "aea", "connections", "stub", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "gym", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "http_client", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "http_server", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "ledger", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "local", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "oef", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "p2p_client", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "p2p_libp2p", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "p2p_libp2p_client", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "p2p_stub", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "soef", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "tcp", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "webhook", CONNECTION_YAML),
    os.path.join(CUR_PATH, "data", "dummy_connection", CONNECTION_YAML),
    os.path.join(CUR_PATH, "data", "gym-connection.yaml"),
]


skill_config_files = [
    os.path.join(ROOT_DIR, "aea", "skills", "error", SKILL_YAML),
    os.path.join(ROOT_DIR, "aea", "skills", "scaffold", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "aries_alice", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "aries_faber", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "carpark_client", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "carpark_detection", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "echo", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "erc1155_client", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "erc1155_deploy", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "generic_buyer", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "generic_seller", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "gym", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "http_echo", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "ml_data_provider", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "ml_train", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "simple_service_registration", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "tac_control", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "tac_control_contract", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "tac_negotiation", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "tac_participation", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "thermometer", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "thermometer_client", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "weather_client", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "weather_station", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "dummy_skill", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "dummy_aea", "skills", "dummy", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "dependencies_skill", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "exception_skill", SKILL_YAML),
]


agent_config_files = [
    os.path.join(CUR_PATH, "data", "dummy_aea", AGENT_YAML),
    os.path.join(CUR_PATH, "data", "aea-config.example.yaml"),
    os.path.join(CUR_PATH, "data", "aea-config.example_w_keys.yaml"),
    os.path.join(FETCHAI_PREF, "agents", "aries_alice", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "aries_faber", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "car_data_buyer", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "car_detector", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "erc1155_client", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "erc1155_deployer", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "generic_buyer", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "generic_seller", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "gym_aea", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "ml_data_provider", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "ml_model_trainer", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "my_first_aea", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "simple_service_registration", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "tac_controller", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "tac_controller_contract", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "tac_participant", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "thermometer_aea", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "thermometer_client", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "weather_client", AGENT_YAML),
    os.path.join(FETCHAI_PREF, "agents", "weather_station", AGENT_YAML),
]

protocol_specification_files = [
    os.path.join(PROTOCOL_SPECS_PREF, "contract_api.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "default.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "fipa.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "gym.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "http.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "ledger_api.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "ml_trade.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "oef_search.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "sample.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "signing.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "state_update.yaml",),
    os.path.join(PROTOCOL_SPECS_PREF, "tac.yaml",),
]


def only_windows(fn: Callable) -> Callable:
    """
    Decorate a pytest method to run a test only in a case we are on Windows.

    :return: decorated method.
    """
    return action_for_platform("Windows", skip=False)(fn)


def skip_test_windows(fn: Callable) -> Callable:
    """
    Decorate a pytest method to skip a test in a case we are on Windows.

    :return: decorated method.
    """
    return action_for_platform("Windows", skip=True)(fn)


def action_for_platform(platform_name: str, skip: bool = True) -> Callable:
    """
    Decorate a pytest class or method to skip on certain platform.

    :param platform_name: check `platform.system()` for available platforms.
    :param skip: if True, the test will be skipped;
      if False, the test will be run ONLY on the chosen platform.

    :return: decorated object
    """
    # for docstyle.
    def decorator(pytest_func):
        """
        For the sake of clarity, assume the chosen platform for the action is "Windows".
        If the following condition is true:
          - the current system is not Windows (is_different) AND we want to skip it (skip)
         OR
          - the current system is Windows (not is_different) AND we want to run only on it (not skip)
        we run the test, else we skip the test.

        logically, the condition is a boolean equivalence
        between the variables "is_different" and "skip"
        Hence, the condition becomes:
        """
        is_different = platform.system() != platform_name
        if is_different is skip:
            return pytest_func

        def action(*args, **kwargs):
            if skip:
                pytest.skip(
                    f"Skipping the test since it doesn't work on {platform_name}."
                )
            else:
                pytest.skip(
                    f"Skipping the test since it works only on {platform_name}."
                )

        if isinstance(pytest_func, type):
            return type(
                pytest_func.__name__,
                (pytest_func,),
                {"setup_class": action, "setup": action, "setUp": action},
            )

        @wraps(pytest_func)
        def wrapper(*args, **kwargs):  # type: ignore
            action(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture(scope="session")
def oef_addr() -> str:
    """IP address pointing to the OEF Node to use during the tests."""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def oef_port() -> int:
    """Port of the connection to the OEF Node to use during the tests."""
    return 10000


def tcpping(ip, port, log_exception: bool = True) -> bool:
    """Ping TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception as e:
        if log_exception:
            logger.exception(e)
        return False


def wait_for_localhost_ports_to_close(
    ports: List[int], timeout: int = 120, sleep_time: int = 2
) -> None:
    """Wait for ports to close with timeout."""
    open_ports = ports
    elapsed = 0
    while len(open_ports) > 0 and elapsed < timeout:
        closed = []
        for port in open_ports:
            if not tcpping("127.0.0.1", port, log_exception=False):
                closed.append(port)
        open_ports = [port for port in open_ports if port not in closed]
        if len(open_ports) > 0:
            time.sleep(sleep_time)
            elapsed += sleep_time
    if open_ports != []:
        raise ValueError("Some ports are open: {}!".format(open_ports))


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


def pytest_addoption(parser) -> None:
    """Add --aea-loop option."""
    parser.addoption(
        "--aea-loop",
        action="store",
        default="async",
        help="aea loop to use: async[default] or sync",
    )
    # disable inernet connection
    parser.addoption(
        "--no-inet",
        action="store_true",
        default=False,
        help="block socket connect outside of 127.x.x.x",
    )

    parser.addoption(
        "--check-threads",
        action="store_true",
        default=False,
        help="check non closed threads i started during test",
    )


@pytest.fixture(scope="session", autouse=True)
def inet_disable(request) -> None:
    """Disable internet access via socket."""
    if not request.config.getoption("--no-inet"):
        return

    orig_connect = socket.socket.connect

    def socket_connect(*args):
        host = args[1][0]
        if host == "localhost" or host.startswith("127."):
            return orig_connect(*args)
        raise socket.error("Internet disabled by pytest option --no-inet")

    p = patch.object(socket.socket, "connect", new=socket_connect)
    p.start()


@pytest.fixture(scope="session", autouse=True)
def apply_aea_loop(request) -> None:
    """Patch AEA.DEFAULT_RUN_LOOP using pytest option `--aea-loop`."""
    loop = request.config.getoption("--aea-loop")
    assert loop in AEA.RUN_LOOPS
    AEA.DEFAULT_RUN_LOOP = loop


@pytest.fixture(scope="session")
def network_node(
    oef_addr, oef_port, pytestconfig, timeout: float = 2.0, max_attempts: int = 10
):
    """Network node initialization."""
    if sys.version_info < (3, 7):
        pytest.skip("Python version < 3.7 not supported by the OEF.")
        return

    if os.name == "nt":
        pytest.skip("Skip test as it doesn't work on Windows.")

    _stop_oef_search_images()
    c = _create_oef_docker_image(oef_addr, oef_port)
    c.start()

    # wait for the setup...
    logger.info("Setting up the OEF node...")
    success = _wait_for_oef(max_attempts=max_attempts, sleep_rate=timeout)

    if not success:
        c.stop()
        c.remove()
        pytest.fail("OEF doesn't work. Exiting...")
    else:
        logger.info("Done!")
        time.sleep(timeout)
        yield
        logger.info("Stopping the OEF node...")
        c.stop()
        c.remove()


@pytest.fixture(scope="session", autouse=True)
def reset_aea_cli_config() -> None:
    """Reset the cli config for each test."""
    _init_cli_config()


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


def double_escape_windows_path_separator(path):
    r"""Doubleescape Windows path separator '\'."""
    return path.replace("\\", "\\\\")


def _make_dummy_connection() -> Connection:
    configuration = ConnectionConfig(connection_id=DummyConnection.connection_id,)
    dummy_connection = DummyConnection(
        configuration=configuration, identity=Identity("name", "address")
    )
    return dummy_connection


def _make_local_connection(
    address: Address,
    node: LocalNode,
    restricted_to_protocols=None,
    excluded_protocols=None,
) -> Connection:
    configuration = ConnectionConfig(
        restricted_to_protocols=restricted_to_protocols,
        excluded_protocols=excluded_protocols,
        connection_id=OEFLocalConnection.connection_id,
    )
    oef_local_connection = OEFLocalConnection(
        configuration=configuration, identity=Identity("name", address), local_node=node
    )
    return oef_local_connection


def _make_oef_connection(address: Address, oef_addr: str, oef_port: int):
    configuration = ConnectionConfig(
        addr=oef_addr, port=oef_port, connection_id=OEFConnection.connection_id
    )
    oef_connection = OEFConnection(
        configuration=configuration, identity=Identity("name", address),
    )
    oef_connection._default_logger_name = "aea.packages.fetchai.connections.oef"
    return oef_connection


def _make_tcp_server_connection(address: str, host: str, port: int):
    configuration = ConnectionConfig(
        address=host, port=port, connection_id=TCPServerConnection.connection_id
    )
    tcp_connection = TCPServerConnection(
        configuration=configuration, identity=Identity("name", address),
    )
    tcp_connection._default_logger_name = (
        "aea.packages.fetchai.connections.tcp.tcp_server"
    )
    return tcp_connection


def _make_tcp_client_connection(address: str, host: str, port: int):
    configuration = ConnectionConfig(
        address=host, port=port, connection_id=TCPClientConnection.connection_id
    )
    tcp_connection = TCPClientConnection(
        configuration=configuration, identity=Identity("name", address),
    )
    tcp_connection._default_logger_name = (
        "aea.packages.fetchai.connections.tcp.tcp_client"
    )
    return tcp_connection


def _make_p2p_client_connection(
    address: Address, provider_addr: str, provider_port: int
):
    configuration = ConnectionConfig(
        addr=provider_addr,
        port=provider_port,
        connection_id=PeerToPeerClientConnection.connection_id,
    )
    p2p_client_connection = PeerToPeerClientConnection(
        configuration=configuration, identity=Identity("", address),
    )
    return p2p_client_connection


def _make_stub_connection(input_file_path: str, output_file_path: str):
    configuration = ConnectionConfig(
        input_file=input_file_path,
        output_file=output_file_path,
        connection_id=StubConnection.connection_id,
    )
    connection = StubConnection(configuration=configuration)
    return connection


def _make_libp2p_connection(
    port: int = 10234,
    host: str = "127.0.0.1",
    relay: bool = True,
    delegate: bool = False,
    entry_peers: Optional[Sequence[MultiAddr]] = None,
    delegate_port: int = 11234,
    delegate_host: str = "127.0.0.1",
) -> P2PLibp2pConnection:
    log_file = "libp2p_node_{}.log".format(port)
    if os.path.exists(log_file):
        os.remove(log_file)
    crypto = make_crypto(FETCHAI)
    identity = Identity("", address=crypto.address)
    if relay and delegate:
        configuration = ConnectionConfig(
            node_key_file=None,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            delegate_uri="{}:{}".format(delegate_host, delegate_port),
            connection_id=P2PLibp2pConnection.connection_id,
        )
    elif relay and not delegate:
        configuration = ConnectionConfig(
            node_key_file=None,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            connection_id=P2PLibp2pConnection.connection_id,
        )
    else:
        configuration = ConnectionConfig(
            node_key_file=None,
            local_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            connection_id=P2PLibp2pConnection.connection_id,
        )
    return P2PLibp2pConnection(configuration=configuration, identity=identity)


def _make_libp2p_client_connection(
    node_port: int = 11234, node_host: str = "127.0.0.1"
) -> P2PLibp2pClientConnection:
    crypto = make_crypto(FETCHAI)
    identity = Identity("", address=crypto.address)
    configuration = ConnectionConfig(
        client_key_file=None,
        nodes=[{"uri": "{}:{}".format(node_host, node_port)}],
        connection_id=P2PLibp2pClientConnection.connection_id,
    )
    return P2PLibp2pClientConnection(configuration=configuration, identity=identity)


def libp2p_log_on_failure(fn: Callable) -> Callable:
    """
    Decorate a pytest method running a libp2p node to print its logs in case test fails.

    :return: decorated method.
    """

    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            fn(self, *args, **kwargs)
        except Exception as e:
            for log_file in self.log_files:
                print("libp2p log file ======================= {}".format(log_file))
                with open(log_file, "r") as f:
                    print(f.read())
                print("=======================================")
            raise e

    return wrapper


def libp2p_log_on_failure_all(cls):
    """
    Decorate every method of a class with `libp2p_log_on_failure`

    :return: class with decorated methods.
    """
    # TODO(LR) test it is a type
    for name, fn in inspect.getmembers(cls):
        if isinstance(fn, FunctionType):
            setattr(cls, name, libp2p_log_on_failure(fn))
        # TOFIX(LR) decorate already @classmethod decorated methods
        continue
        if isinstance(fn, MethodType):
            if fn.im_self is None:
                wrapped_fn = libp2p_log_on_failure(fn.im_func)
                method = MethodType(wrapped_fn, None, cls)
                setattr(cls, name, method)
            else:
                wrapped_fn = libp2p_log_on_failure(fn.im_func)
                clsmethod = MethodType(wrapped_fn, cls, type)
                setattr(cls, name, clsmethod)
    return cls


def do_for_all(method_decorator):
    def class_decorator(cls):
        class GetAttributeMetaClass(type):
            def __getattribute__(cls, name):
                attr = super().__getattribute__(name)
                return method_decorator(attr)

        class DecoratedClass(cls, metaclass=GetAttributeMetaClass):
            def __getattribute__(self, name):
                attr = super().__getattribute__(name)
                return method_decorator(attr)

        for attr in WRAPPER_ASSIGNMENTS:
            if not hasattr(cls, attr):
                continue
            setattr(DecoratedClass, attr, getattr(cls, attr))
        DecoratedClass.__wrapped__ = cls
        return DecoratedClass

    return class_decorator


class CwdException(Exception):
    """Exception to raise if cwd was not restored by test."""

    def __init__(self):
        """Init expcetion with default message."""
        super().__init__("CWD was not restored")


@pytest.fixture(scope="class", autouse=True)
def check_test_class_cwd():
    """Check test case class restore CWD."""
    os.chdir(ROOT_DIR)
    old_cwd = os.getcwd()
    yield
    if old_cwd != os.getcwd():
        raise CwdException()


@pytest.fixture(autouse=True)
def check_test_cwd(request):
    """Check particular test restore CWD."""
    if request.cls:
        yield
        return
    os.chdir(ROOT_DIR)
    old_cwd = os.getcwd()
    yield
    if old_cwd != os.getcwd():
        raise CwdException()


@pytest.fixture(autouse=True)
def check_test_threads(request):
    """Check particular test close all spawned threads."""
    if not request.config.getoption("--check-threads"):
        yield
        return
    if request.cls:
        yield
        return
    num_threads = threading.activeCount()
    yield
    new_num_threads = threading.activeCount()
    assert num_threads >= new_num_threads, "Non closed threads!"


@pytest.fixture()
def erc1155_contract():
    """
    Instantiate an ERC1155 contract instance. As a side effect,
    register it to the registry, if not already registered.
    """
    directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
    configuration = ComponentConfiguration.load(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

        path = Path(configuration.directory, configuration.path_to_contract_interface)
        with open(path, "r") as interface_file:
            contract_interface = json.load(interface_file)

        contract_registry.register(
            id_=str(configuration.public_id),
            entry_point=f"{configuration.prefix_import_path}.contract:{configuration.class_name}",
            class_kwargs={"contract_interface": contract_interface},
            contract_config=configuration,
        )

    contract = contract_registry.make(str(configuration.public_id))
    yield contract


def env_path_separator() -> str:
    """
    Get the separator between path items in PATH variables, cross platform.

    E.g. on Linux and MacOS, it returns ':', whereas on Windows ';'.
    """
    if sys.platform == "win32":
        return ";"
    else:
        return ":"
