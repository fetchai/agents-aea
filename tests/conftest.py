# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

import difflib
import inspect
import logging
import os
import platform
import random
import shutil
import socket
import stat
import string
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from copy import copy
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Tuple, cast
from unittest.mock import MagicMock, patch

import docker as docker
import gym
import pytest
from _pytest.monkeypatch import MonkeyPatch  # type: ignore
from aea_cli_ipfs.ipfs_utils import IPFSDaemon  # type: ignore
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import (
    DEFAULT_EIP1559_STRATEGY,
    ETHEREUM_PRIVATE_KEY_PATH,
    ETHEREUM_PRIVATE_KEY_TWO_PATH,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
)
from aea_ledger_ethereum.test_tools.docker_images import GanacheDockerImage
from aea_ledger_fetchai import FetchAIApi, FetchAICrypto, FetchAIFaucetApi
from aea_ledger_fetchai.test_tools.constants import (
    FETCHAI_P2P_ADDRESS,
    FETCHAI_TESTNET_CONFIG,
    FUNDED_FETCHAI_ADDRESS_ONE,
    FUNDED_FETCHAI_ADDRESS_TWO,
    FUNDED_FETCHAI_PRIVATE_KEY_1,
)
from aea_ledger_fetchai.test_tools.docker_images import FetchLedgerDockerImage
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.address import Address as CosmpyAddress
from cosmpy.crypto.keypairs import PrivateKey

from aea import AEA_DIR
from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.utils.config import _init_cli_config
from aea.common import Address
from aea.configurations.base import ComponentType, ConnectionConfig, ContractConfig
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE as AGENT_YAML
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE as CONNECTION_YAML
from aea.configurations.base import DEFAULT_CONTRACT_CONFIG_FILE as CONTRACT_YAML
from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE as PROTOCOL_YAML
from aea.configurations.base import DEFAULT_SKILL_CONFIG_FILE as SKILL_YAML
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER, PRIVATE_KEY_PATH_SCHEMA
from aea.configurations.loader import load_component_configuration
from aea.connections.base import Connection
from aea.contracts.base import Contract, contract_registry
from aea.crypto.ledger_apis import (
    COSMOS_DEFAULT_ADDRESS,
    DEFAULT_LEDGER_CONFIGS,
    ETHEREUM_DEFAULT_CURRENCY_DENOM,
)
from aea.crypto.registries import ledger_apis_registry, make_crypto, make_ledger_api
from aea.crypto.wallet import CryptoStore
from aea.exceptions import enforce
from aea.helpers.base import cd
from aea.identity.base import Identity
from aea.test_tools.click_testing import CliRunner as ImportedCliRunner
from aea.test_tools.constants import DEFAULT_AUTHOR
from aea.test_tools.docker_image import DockerImage
from aea.test_tools.network import LOCALHOST
from aea.test_tools.test_cases import BaseAEATestCase

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.connections.stub.connection import StubConnection

from tests.data.dummy_connection.connection import DummyConnection  # type: ignore


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


# URL to local Ganache instance
DEFAULT_GANACHE_ADDR = LOCALHOST.geturl()
DEFAULT_GANACHE_PORT = 8545
DEFAULT_GANACHE_CHAIN_ID = 1337
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 1_000_000_000
DEFAULT_MAX_FEE_PER_GAS = 1_000_000_000

# URL to local Fetch ledger instance
DEFAULT_FETCH_DOCKER_IMAGE_TAG = "fetchai/fetchd:0.10.2"
DEFAULT_FETCH_LEDGER_ADDR = LOCALHOST.geturl()
DEFAULT_FETCH_LEDGER_RPC_PORT = 26657
DEFAULT_FETCH_LEDGER_REST_PORT = 1317
DEFAULT_FETCH_ADDR_REMOTE = "https://rest-dorado.fetch.ai:443"
DEFAULT_FETCH_MNEMONIC = "gap bomb bulk border original scare assault pelican resemble found laptop skin gesture height inflict clinic reject giggle hurdle bubble soldier hurt moon hint"
DEFAULT_MONIKER = "test-node"
DEFAULT_FETCH_CHAIN_ID = "dorado-1"
DEFAULT_GENESIS_ACCOUNT = "validator"
DEFAULT_DENOMINATION = "atestfet"
FETCHD_INITIAL_TX_SLEEP = 6

COSMOS_PRIVATE_KEY_FILE_CONNECTION = "cosmos_connection_private_key.txt"
COSMOS_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(CosmosCrypto.identifier)


DEFAULT_AMOUNT = 1000000000000000000000
GAS_PRICE_API_KEY = ""

# private keys with value on testnet
COSMOS_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", COSMOS_PRIVATE_KEY_FILE
)

DEFAULT_PRIVATE_KEY_PATH = COSMOS_PRIVATE_KEY_PATH

NON_FUNDED_COSMOS_PRIVATE_KEY_1 = (
    "81b0352f99a08a754b56e529dda965c4ce974edb6db7e90035e01ed193e1b7bc"
)

# addresses with no value on testnet
COSMOS_ADDRESS_ONE = "cosmos1z4ftvuae5pe09jy2r7udmk6ftnmx504alwd5qf"
COSMOS_ADDRESS_TWO = "cosmos1gssy8pmjdx8v4reg7lswvfktsaucp0w95nk78m"


# P2P addresses
COSMOS_P2P_ADDRESS = "/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAmAzvu5uNbcnD2qaqrkSULhJsc6GJUg3iikWerJkoD72pr"  # relates to NON_FUNDED_COSMOS_PRIVATE_KEY_1

NON_GENESIS_CONFIG = {
    "delegate_uri": "127.0.0.1:11001",
    "entry_peers": [FETCHAI_P2P_ADDRESS],
    "local_uri": "127.0.0.1:9001",
    "log_file": "libp2p_node.log",
    "public_uri": "127.0.0.1:9001",
    "ledger_id": "fetchai",
}
NON_GENESIS_CONFIG_TWO = {
    "delegate_uri": "127.0.0.1:11002",
    "entry_peers": [FETCHAI_P2P_ADDRESS],
    "local_uri": "127.0.0.1:9002",
    "log_file": "libp2p_node.log",
    "public_uri": "127.0.0.1:9002",
    "ledger_id": "fetchai",
}

# testnets
COSMOS_TESTNET_CONFIG = {"address": COSMOS_DEFAULT_ADDRESS}

# common public ids used in the tests

MY_FIRST_AEA_PUBLIC_ID = PublicId.from_str("fetchai/my_first_aea:0.27.0")

DUMMY_SKILL_PATH = os.path.join(CUR_PATH, "data", "dummy_skill", SKILL_YAML)

MAX_FLAKY_RERUNS = 3
MAX_FLAKY_RERUNS_ETH = 1
MAX_FLAKY_RERUNS_INTEGRATION = 1

PACKAGES_DIR = os.path.join(ROOT_DIR, "packages")
FETCHAI_PREF = os.path.join(ROOT_DIR, "packages", "fetchai")
OPEN_AEA_REF = os.path.join(ROOT_DIR, "packages", "open_aea")
VALORY_REF = os.path.join(ROOT_DIR, "packages", "valory")
PROTOCOL_SPECS_PREF_1 = os.path.join(ROOT_DIR, "examples", "protocol_specification_ex")
PROTOCOL_SPECS_PREF_2 = os.path.join(ROOT_DIR, "tests", "data")


GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (FUNDED_ETH_PRIVATE_KEY_1, DEFAULT_AMOUNT),
        (FUNDED_ETH_PRIVATE_KEY_2, DEFAULT_AMOUNT),
        (FUNDED_ETH_PRIVATE_KEY_3, DEFAULT_AMOUNT),
        (Path(ETHEREUM_PRIVATE_KEY_PATH).read_text().strip(), DEFAULT_AMOUNT),
    ],
)

FETCHD_CONFIGURATION = dict(
    mnemonic=DEFAULT_FETCH_MNEMONIC,
    moniker=DEFAULT_MONIKER,
    chain_id=DEFAULT_FETCH_CHAIN_ID,
    genesis_account=DEFAULT_GENESIS_ACCOUNT,
    denom=DEFAULT_DENOMINATION,
)


contract_config_files = [
    os.path.join(FETCHAI_PREF, "contracts", "erc1155", CONTRACT_YAML),
    os.path.join(ROOT_DIR, "tests", "data", "dummy_contract", CONTRACT_YAML),
]

protocol_config_files = [
    os.path.join(ROOT_DIR, "aea", "protocols", "scaffold", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "contract_api", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "default", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "fipa", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "gym", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "http", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "ledger_api", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "oef_search", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "state_update", PROTOCOL_YAML),
    os.path.join(FETCHAI_PREF, "protocols", "tac", PROTOCOL_YAML),
    os.path.join(OPEN_AEA_REF, "protocols", "signing", PROTOCOL_YAML),
    os.path.join(VALORY_REF, "protocols", "acn", PROTOCOL_YAML),
    os.path.join(CUR_PATH, "data", "dummy_protocol", PROTOCOL_YAML),
]

connection_config_files = [
    os.path.join(ROOT_DIR, "aea", "connections", "scaffold", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "gym", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "http_client", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "http_server", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "ledger", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "local", CONNECTION_YAML),
    os.path.join(FETCHAI_PREF, "connections", "stub", CONNECTION_YAML),
    os.path.join(VALORY_REF, "connections", "p2p_libp2p", CONNECTION_YAML),
    os.path.join(VALORY_REF, "connections", "p2p_libp2p_client", CONNECTION_YAML),
    os.path.join(VALORY_REF, "connections", "p2p_libp2p_mailbox", CONNECTION_YAML),
    os.path.join(CUR_PATH, "data", "dummy_connection", CONNECTION_YAML),
    os.path.join(CUR_PATH, "data", "gym-connection.yaml"),
]

skill_config_files = [
    os.path.join(ROOT_DIR, "aea", "skills", "scaffold", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "echo", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "erc1155_client", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "erc1155_deploy", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "error", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "generic_buyer", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "generic_seller", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "gym", SKILL_YAML),
    os.path.join(FETCHAI_PREF, "skills", "http_echo", SKILL_YAML),
    DUMMY_SKILL_PATH,
    os.path.join(CUR_PATH, "data", "dummy_aea", "skills", "dummy", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "dependencies_skill", SKILL_YAML),
    os.path.join(CUR_PATH, "data", "exception_skill", SKILL_YAML),
]

agent_config_files = [
    os.path.join(CUR_PATH, "data", "dummy_aea", AGENT_YAML),
    os.path.join(CUR_PATH, "data", "aea-config.example.yaml"),
    os.path.join(CUR_PATH, "data", "aea-config.example_w_keys.yaml"),
    os.path.join(CUR_PATH, "data", "aea-config.example_multipage.yaml"),
    os.path.join(FETCHAI_PREF, "agents", "my_first_aea", AGENT_YAML),
]

protocol_specification_files = [
    os.path.join(
        PROTOCOL_SPECS_PREF_1,
        "sample.yaml",
    ),
    os.path.join(
        PROTOCOL_SPECS_PREF_2,
        "sample_specification.yaml",
    ),
    os.path.join(
        PROTOCOL_SPECS_PREF_2,
        "sample_specification_no_custom_types.yaml",
    ),
]

DEFAULT_HOST = LOCALHOST.hostname


def remove_test_directory(directory: str, retries: int = 3) -> bool:
    """Destroy a directory once tests are done, change permissions if needed.

    Note that on Windows directories and files that are open cannot be deleted.

    :param directory: directory to be deleted
    :param retries: number of re-attempts
    :return: whether the directory was successfully deleted
    """

    def readonly_handler(func, path, execinfo) -> None:
        """If permission is readonly, we change these and retry."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    # we need `onerror` to deal with permissions, e.g. on Windows
    while os.path.exists(directory) and retries:
        try:
            shutil.rmtree(directory, onerror=readonly_handler)
        except Exception:  # pylint: disable=broad-except
            retries -= 1
            time.sleep(1)
    return not os.path.exists(directory)


@contextmanager
def project_root_pythonpath():
    """Set pythonpath to project root."""
    old_python_path = os.environ.get("PYTHONPATH", None)
    os.environ["PYTHONPATH"] = ":".join(
        filter(None, [os.path.abspath(ROOT_DIR), old_python_path])
    )
    yield
    if old_python_path is None:
        os.environ.pop("PYTHONPATH")
    else:
        os.environ["PYTHONPATH"] = old_python_path


def match_files(fname1: str, fname2: str) -> Tuple[bool, str]:
    """
    Find out whether two text files match.

    :param fname1: string path to file 1
    :param fname2: string path to file 2

    :return: whether files match (True) or not (False) and a string of their difference ("" if they match)
    """
    with open(fname1, "r") as f1, open(fname2, "r") as f2:
        difference = set(f1).difference(f2)
    are_identical = difference == set()

    diff = ""
    if not are_identical:
        diff = find_difference(fname1, fname2)
    return are_identical, diff


def find_difference(fname1: str, fname2: str) -> str:
    """Find the difference between two text files."""
    diff = ""
    with open(fname1) as f1, open(fname2) as f2:
        differ = difflib.Differ()

        for line in differ.compare(f1.readlines(), f2.readlines()):
            if not (line.startswith(" ") or line.startswith("? ")):
                line = line[2:].lstrip()
                diff += line
    return diff


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


def skip_test_macos(fn: Callable) -> Callable:
    """
    Decorate a pytest method to skip a test in a case we are on MacOS.

    :return: decorated method.
    """
    return action_for_platform("Darwin", skip=True)(fn)


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
                {
                    "setup_class": action,
                    "setup": action,
                    "setUp": action,
                    "_skipped": True,
                },
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


@pytest.fixture(scope="session")
def ganache_addr() -> str:
    """HTTP address to the Ganache node."""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture(scope="session")
def ganache_port() -> int:
    """Port of the connection to the Ganache Node to use during the tests."""
    return DEFAULT_GANACHE_PORT


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
def increase_aea_builder_build_timeout(request) -> Generator:
    """Increase build timeout for aea builder."""
    old_timeout = AEABuilder.BUILD_TIMEOUT
    AEABuilder.BUILD_TIMEOUT = 420
    try:
        yield
    finally:
        AEABuilder.BUILD_TIMEOUT = old_timeout


@pytest.fixture(scope="session", autouse=True)
def apply_aea_loop(request) -> None:
    """Patch AEA.DEFAULT_RUN_LOOP using pytest option `--aea-loop`."""
    loop = request.config.getoption("--aea-loop")
    assert loop in AEA.RUN_LOOPS
    AEA.DEFAULT_RUN_LOOP = loop


@pytest.fixture(scope="session")
def ganache_configuration():
    """Get the Ganache configuration for testing purposes."""
    return GANACHE_CONFIGURATION


@pytest.fixture(scope="session")
def fetchd_configuration():
    """Get the Fetch ledger configuration for testing purposes."""
    return FETCHD_CONFIGURATION


@pytest.fixture(scope="session")
def ethereum_testnet_config(ganache_addr, ganache_port):
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = {
        "address": new_uri,
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM,
        "default_gas_price_strategy": "gas_station",
        "gas_price_strategies": {
            "eip1559": DEFAULT_EIP1559_STRATEGY,
            "gas_station": {
                "gas_price_api_key": GAS_PRICE_API_KEY,
                "gas_price_strategy": "fast",
            },
        },
    }
    return new_config


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(ethereum_testnet_config):
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier, None)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="class")
def ganache(
    ganache_configuration,
    ganache_addr=DEFAULT_GANACHE_ADDR,
    ganache_port=DEFAULT_GANACHE_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    with _ganache_context(
        ganache_configuration, ganache_addr, ganache_port, timeout, max_attempts
    ) as image:
        yield image


@contextmanager
def _ganache_context(
    ganache_configuration: Dict,
    ganache_addr: str = DEFAULT_GANACHE_ADDR,
    ganache_port: int = DEFAULT_GANACHE_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="class")
@action_for_platform("Linux", skip=False)
def fetchd(
    fetchd_configuration,
    timeout: float = 2.0,
    max_attempts: int = 20,
):
    """Launch the Fetch ledger image."""
    with _fetchd_context(fetchd_configuration, timeout, max_attempts) as fetchd:
        yield fetchd


@contextmanager
def _fetchd_context(fetchd_configuration, timeout: float = 2.0, max_attempts: int = 20):
    client = docker.from_env()
    image = FetchLedgerDockerImage(
        client,
        DEFAULT_FETCH_LEDGER_ADDR,
        DEFAULT_FETCH_LEDGER_RPC_PORT,
        DEFAULT_FETCH_DOCKER_IMAGE_TAG,
        config=fetchd_configuration,
    )
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


def _launch_image(image: DockerImage, timeout: float = 2.0, max_attempts: int = 10):
    """
    Launch image.

    :param image: an instance of Docker image.
    :return: None
    """
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


@pytest.fixture(scope="session", autouse=True)
def reset_aea_cli_config() -> None:
    """Reset the cli config for each test."""
    _init_cli_config()


def get_unused_tcp_port():
    """Get an unused TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((LOCALHOST.hostname, 0))
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
        IP = LOCALHOST.hostname
    finally:
        s.close()
    return IP


def double_escape_windows_path_separator(path):
    r"""Doubleescape Windows path separator '\'."""
    return path.replace("\\", "\\\\")


def _make_dummy_connection() -> Connection:
    configuration = ConnectionConfig(
        connection_id=DummyConnection.connection_id,
    )
    dummy_connection = DummyConnection(
        configuration=configuration,
        data_dir=MagicMock(),
        identity=Identity("name", "address", "public_key"),
    )
    return dummy_connection


def _make_local_connection(
    address: Address,
    public_key: str,
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
        configuration=configuration,
        data_dir=MagicMock(),
        identity=Identity("name", address, public_key),
        local_node=node,
    )
    return oef_local_connection


def _make_stub_connection(input_file_path: str, output_file_path: str):
    configuration = ConnectionConfig(
        input_file=input_file_path,
        output_file=output_file_path,
        connection_id=StubConnection.connection_id,
    )
    connection = StubConnection(configuration=configuration, data_dir=MagicMock())
    return connection


def is_port_in_use(host: str, port: int) -> bool:
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


class CwdException(Exception):
    """Exception to raise if cwd was not restored by test."""

    def __init__(self):
        """Init exception with default message."""
        super().__init__("CWD was not restored")


@pytest.fixture(scope="class", autouse=True)
def aea_testcase_teardown_check(request):
    """Check BaseAEATestCase.teardown_class for BaseAEATestCase based test cases."""
    from aea.test_tools.test_cases import BaseAEATestCase  # cause circular import

    yield
    if (
        request.cls
        and issubclass(request.cls, BaseAEATestCase)
        and getattr(request.cls, "_skipped", False) is False
    ):
        assert getattr(
            request.cls, "_is_teardown_class_called", None
        ), "No BaseAEATestCase.teardown_class was called!"


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
        os.chdir(ROOT_DIR)
        raise CwdException()


@pytest.fixture(autouse=True)
def set_logging_to_debug(request):
    """Set aea logger to debug."""
    aea_logger = logging.getLogger("aea")
    aea_logger.setLevel(logging.DEBUG)


@pytest.fixture(autouse=True)
def check_test_threads(request):
    """Check particular test close all spawned threads."""
    if not request.config.getoption("--check-threads"):
        yield
        return
    if request.cls:
        yield
        return
    num_threads = threading.active_count()
    yield
    new_num_threads = threading.active_count()
    assert num_threads >= new_num_threads, "Non closed threads!"


@pytest.fixture()
async def ledger_apis_connection(request, ethereum_testnet_config):
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "fetchai", "connections", "ledger")
    connection = Connection.from_dir(
        directory, data_dir=MagicMock(), identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    connection._logger = logging.getLogger("aea.packages.fetchai.connections.ledger")

    # use testnet config
    connection.configuration.config.get("ledger_apis", {})[
        "ethereum"
    ] = ethereum_testnet_config

    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.fixture()
def ledger_api(ethereum_testnet_config, ganache):
    """Ledger api fixture."""
    ledger_id, config = EthereumCrypto.identifier, ethereum_testnet_config
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api


def get_register_erc1155() -> Contract:
    """Get and register the erc1155 contract package."""
    directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

    contract = contract_registry.make(str(configuration.public_id))
    return contract


@pytest.fixture()
def erc1155_contract(ledger_api, ganache, ganache_addr, ganache_port):
    """
    Instantiate an ERC1155 contract instance.

    As a side effect, register it to the registry, if not already registered.
    """
    contract = get_register_erc1155()
    # deploy contract
    crypto = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_PATH
    )

    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api, deployer_address=crypto.address, gas=5000000
    )
    gas = ledger_api.api.eth.estimate_gas(transaction=tx)
    tx["gas"] = gas
    tx_signed = crypto.sign_transaction(tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed)
    time.sleep(0.5)
    receipt = ledger_api.get_transaction_receipt(tx_digest)
    contract_address = cast(Dict, receipt)["contractAddress"]
    yield contract, contract_address


@pytest.fixture()
def erc20_contract(ledger_api, ganache, ganache_addr, ganache_port):
    """Instantiate an ERC20 contract."""
    directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "fet_erc20")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

    contract = contract_registry.make(str(configuration.public_id))

    # get two accounts
    account1 = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_PATH
    )
    account2 = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_TWO_PATH
    )

    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api,
        deployer_address=account1.address,
        gas=5000000,
        name="FetERC20Mock",
        symbol="MFET",
        initialSupply=int(1e23),
        decimals_=18,
    )
    gas = ledger_api.api.eth.estimate_gas(transaction=tx)
    tx["gas"] = gas
    tx_signed = account1.sign_transaction(tx)
    tx_receipt = ledger_api.send_signed_transaction(tx_signed)
    receipt = ledger_api.get_transaction_receipt(tx_receipt)
    contract_address = cast(Dict, receipt)["contractAddress"]

    # Transfer some MFET to another default account
    tx = contract.get_transfer_transaction(
        ledger_api=ledger_api,
        contract_address=contract_address,
        from_address=account1.address,
        gas=200000,
        receiver=account2.address,
        amount=int(1e20),
    )
    tx_signed = account1.sign_transaction(tx)
    ledger_api.send_signed_transaction(tx_signed)

    yield contract, contract_address


@pytest.fixture()
def oracle_contract(ledger_api, ganache, ganache_addr, ganache_port, erc20_contract):
    """Instantiate a Fetch Oracle contract."""
    directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "oracle")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

    contract = contract_registry.make(str(configuration.public_id))

    _, erc20_address = erc20_contract

    # deploy contract
    crypto = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_PATH
    )

    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api,
        deployer_address=crypto.address,
        gas=5000000,
        ERC20Address=erc20_address,
        initialFee=10000000000,
    )
    tx_signed = crypto.sign_transaction(tx)
    tx_receipt = ledger_api.send_signed_transaction(tx_signed)
    receipt = ledger_api.get_transaction_receipt(tx_receipt)
    contract_address = cast(Dict, receipt)["contractAddress"]
    yield contract, contract_address


def docker_exec_cmd(image_tag: str, cmd: str, **kwargs):
    """Execute a command in running docker containers matching image tag."""
    client = docker.from_env()
    for container in client.containers.list():
        if image_tag in container.image.tags:
            logger.info(f"Running command '{cmd}' in docker container {image_tag}")
            resp = container.exec_run(cmd, **kwargs)
            logger.info(resp)


def fund_accounts_from_local_validator(
    addresses: List[str], amount: int, denom: str = DEFAULT_DENOMINATION
):
    """Send funds to local accounts from the local genesis validator."""

    pk = PrivateKey(bytes.fromhex(FUNDED_FETCHAI_PRIVATE_KEY_1))
    wallet = LocalWallet(pk)
    ledger = LedgerClient(
        NetworkConfig(
            chain_id=DEFAULT_FETCH_CHAIN_ID,
            url=f"rest+{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
            fee_minimum_gas_price=5000000000,
            fee_denomination=DEFAULT_DENOMINATION,
            staking_denomination=DEFAULT_DENOMINATION,
        )
    )

    for address in addresses:
        tx = ledger.send_tokens(CosmpyAddress(address), amount, denom, wallet)
        tx.wait_to_complete()


@pytest.fixture()
def fund_fetchai_accounts(fetchd):
    """Fund test accounts from local validator."""
    for _ in range(5):
        try:
            # retry, cause possible race condition with fetchd docker image init
            fund_accounts_from_local_validator(
                [FUNDED_FETCHAI_ADDRESS_ONE, FUNDED_FETCHAI_ADDRESS_TWO],
                10000000000000000000,
            )
            return
        except Exception:  # pylint: disable=broad-except
            time.sleep(3)


def env_path_separator() -> str:
    """
    Get the separator between path items in PATH variables, cross platform.

    E.g. on Linux and MacOS, it returns ':', whereas on Windows ';'.
    """
    if sys.platform == "win32":
        return ";"
    else:
        return ":"


def random_string(length: int = 8) -> str:
    """Generate a random string.

    :param length: how long random string should be

    :return: random chars str
    """
    return "".join(
        random.choice(string.ascii_lowercase) for _ in range(length)  # nosec
    )


def make_uri(addr: str, port: int):
    """Make uri from address and port."""
    return f"{addr}:{port}"


@pytest.mark.integration
class UseGanache:
    """Inherit from this class to use Ganache."""

    @pytest.fixture(autouse=True)
    def _start_ganache(self, ganache):
        """Start a Ganache image."""


@pytest.mark.integration
class UseSOEF:
    """Inherit from this class to use SOEF."""

    @pytest.fixture(autouse=True)
    def _start_soef(self, soef):
        """Start an SOEF image."""


@pytest.mark.integration
class UseLocalFetchNode:
    """Inherit from this class to use a local Fetch ledger node."""

    @pytest.fixture(autouse=True)
    def _start_fetchd(self, fetchd):
        """Start a Fetch ledger image."""


@pytest.fixture()
def change_directory():
    """Change directory and execute the test."""
    temporary_directory = tempfile.mkdtemp()
    try:
        with cd(temporary_directory):
            yield temporary_directory
    finally:
        shutil.rmtree(temporary_directory)


@pytest.fixture(params=[None, "fake-password"])
def password_or_none(request) -> Optional[str]:
    """
    Return a password for testing purposes, including None.

    Note that this is a parametrized fixture.
    """
    return request.param


def method_scope(cls):
    """
    Class decorator to make the setup/teardown to have the 'method' scope.

    :param cls: the class. It must be a subclass of
    :return:
    """
    enforce(
        issubclass(cls, BaseAEATestCase),
        "cannot use decorator if class is not instance of BaseAEATestCase",
    )
    old_setup_class = cls.setup_class
    old_teardown_class = cls.teardown_class
    cls.setup_class = classmethod(lambda _cls: None)
    cls.teardown_class = classmethod(lambda _cls: None)
    cls.setup = lambda self: old_setup_class()
    cls.teardown = lambda self: old_teardown_class()
    return cls


def get_wealth_if_needed(address: Address, fetchai_api: FetchAIApi = None):
    """
     Get wealth from fetch.ai faucet to specific address

    :param: address: Addresse to be funded from faucet
    """
    if fetchai_api is None:
        fetchai_api = cast(
            FetchAIApi,
            make_ledger_api(FetchAICrypto.identifier, **FETCHAI_TESTNET_CONFIG),
        )

    balance = fetchai_api.get_balance(address)
    if balance == 0:
        FetchAIFaucetApi().get_wealth(address)

        timeout = 0
        while timeout < 40 and balance == 0:
            time.sleep(1)
            timeout += 1
            _balance = fetchai_api.get_balance(address)
            balance = _balance if _balance is not None else 0


@pytest.fixture(scope="session", autouse=True)
def disable_logging_handlers_cleanup(request) -> Generator:
    """
    Fix for pytest flaky crash, disable handlers cleanup.

    Check https://github.com/fetchai/agents-aea/issues/2431
    """

    def do_nothing(*args):
        pass

    with MonkeyPatch().context() as mp:
        mp.setattr(logging.config, "_clearExistingHandlers", do_nothing)
        yield


@pytest.fixture(scope="class")
def use_ipfs_daemon() -> Generator:
    """Use IPFS daemon."""
    ipfs_daemon = IPFSDaemon()
    ipfs_daemon.start()

    yield
    ipfs_daemon.stop()


@pytest.fixture(scope="function")
def mock_sys_modules() -> Generator:
    """Store previous content of sys.modules and restore it after test execution."""
    old_sys_modules = copy(sys.modules)
    yield
    sys.modules = old_sys_modules
