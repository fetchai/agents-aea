# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Module to declare constants."""
from pathlib import Path
from typing import Dict, List


AEA_DIR = Path(__file__).parent.parent
_FETCHAI_IDENTIFIER = "fetchai"
_ETHEREUM_IDENTIFIER = "ethereum"
_COSMOS_IDENTIFIER = "cosmos"
SIGNING_PROTOCOL = "open_aea/signing:latest"
SIGNING_PROTOCOL_WITH_HASH = (
    "open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44"
)
DEFAULT_LEDGER = _ETHEREUM_IDENTIFIER
PRIVATE_KEY_PATH_SCHEMA = "{}_private_key.txt"
DEFAULT_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(DEFAULT_LEDGER)
DEFAULT_LICENSE = "Apache-2.0"
DISTRIBUTED_PACKAGES: List[str] = []
DEFAULT_SEARCH_SERVICE_ADDRESS = "open_aea/soef:any"
DEFAULT_INPUT_FILE_NAME = "./input_file"
DEFAULT_OUTPUT_FILE_NAME = "./output_file"
SCAFFOLD_PUBLIC_ID = "open_aea/scaffold:0.1.0"
PACKAGES = "packages"
DEFAULT_REGISTRY_NAME = PACKAGES
VENDOR = "vendor"
AGENT = "agent"
AGENTS = "agents"
CONNECTION = "connection"
CONNECTIONS = "connections"
CONTRACT = "contract"
CONTRACTS = "contracts"
PROTOCOL = "protocol"
PROTOCOLS = "protocols"
SKILL = "skill"
SKILLS = "skills"
SERVICE = "service"
SERVICES = "services"
DEFAULT_README_FILE = "README.md"
DEFAULT_VERSION = "0.1.0"
DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
DEFAULT_CONNECTION_CONFIG_FILE = "connection.yaml"
DEFAULT_CONTRACT_CONFIG_FILE = "contract.yaml"
DEFAULT_PROTOCOL_CONFIG_FILE = "protocol.yaml"
DEFAULT_SERVICE_CONFIG_FILE = "service.yaml"
PACKAGE_PUBLIC_ID_VAR_NAME = "PUBLIC_ID"
DEFAULT_FINGERPRINT_IGNORE_PATTERNS = [
    ".DS_Store",
    "*__pycache__/*",
    "*__pycache__",
    "*.pyc",
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SERVICE_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    PRIVATE_KEY_PATH_SCHEMA.format("*"),
]
DEFAULT_PYPI_INDEX_URL = "https://pypi.org/simple"
DEFAULT_GIT_REF = "master"
DEFAULT_LOGGING_CONFIG = {"version": 1, "disable_existing_loggers": False}
IMPORT_TEMPLATE_1 = "from packages.{author}.{type}.{name}"
IMPORT_TEMPLATE_2 = "import packages.{author}.{type}.{name}"
DEFAULT_ENV_DOTFILE = ".env"
DOTTED_PATH_MODULE_ELEMENT_SEPARATOR = ":"
DEFAULT_BUILD_DIR_NAME = ".build"
DEFAULT_DEPENDENCIES: Dict[str, Dict] = {"open-aea-ledger-ethereum": {}}

CONFIG_FILE_TO_PACKAGE_TYPE = {
    DEFAULT_SKILL_CONFIG_FILE: SKILL,
    DEFAULT_PROTOCOL_CONFIG_FILE: PROTOCOL,
    DEFAULT_CONNECTION_CONFIG_FILE: CONNECTION,
    DEFAULT_CONTRACT_CONFIG_FILE: CONTRACT,
    DEFAULT_SERVICE_CONFIG_FILE: SERVICE,
    DEFAULT_AEA_CONFIG_FILE: AGENT,
}  # type: Dict[str, str]

PACKAGE_TYPE_TO_CONFIG_FILE = {
    value: key for key, value in CONFIG_FILE_TO_PACKAGE_TYPE.items()
}  # type: Dict[str, str]

CRYPTO_PLUGIN_GROUP = "aea.cryptos"
LEDGER_APIS_PLUGIN_GROUP = "aea.ledger_apis"
FAUCET_APIS_PLUGIN_GROUP = "aea.faucet_apis"
ALLOWED_GROUPS = {
    CRYPTO_PLUGIN_GROUP,
    LEDGER_APIS_PLUGIN_GROUP,
    FAUCET_APIS_PLUGIN_GROUP,
}
AEA_MANAGER_DATA_DIRNAME = "data"
LAUNCH_SUCCEED_MESSAGE = "Start processing messages..."

PROTOCOL_LANGUAGE_PYTHON = "python"
PROTOCOL_LANGUAGE_GO = "go"
PROTOCOL_LANGUAGE_CPP = "cpp"
PROTOCOL_LANGUAGE_JAVA = "java"
PROTOCOL_LANGUAGE_CSHARP = "csharp"
PROTOCOL_LANGUAGE_RUBY = "ruby"
PROTOCOL_LANGUAGE_OBJC = "objc"
PROTOCOL_LANGUAGE_JS = "js"
SUPPORTED_PROTOCOL_LANGUAGES = [
    PROTOCOL_LANGUAGE_PYTHON,
    PROTOCOL_LANGUAGE_GO,
    PROTOCOL_LANGUAGE_CPP,
    PROTOCOL_LANGUAGE_JAVA,
    PROTOCOL_LANGUAGE_CSHARP,
    PROTOCOL_LANGUAGE_RUBY,
    PROTOCOL_LANGUAGE_OBJC,
    PROTOCOL_LANGUAGE_JS,
]
DEFAULT_CERTS_DIR_NAME = ".certs"
DEFAULT_IGNORE_DIRS_AGENT_FINGERPRINT = [
    SKILLS,
    PROTOCOLS,
    CONTRACTS,
    CONNECTIONS,
    VENDOR,
    DEFAULT_BUILD_DIR_NAME,
    DEFAULT_CERTS_DIR_NAME,
]

ITEM_TYPE_TO_PLURAL = {
    PROTOCOL: PROTOCOLS,
    AGENT: AGENTS,
    CONTRACT: CONTRACTS,
    CONNECTION: CONNECTIONS,
    SKILL: SKILLS,
}

ITEM_TYPE_PLURAL_TO_TYPE = {v: k for k, v in ITEM_TYPE_TO_PLURAL.items()}
SCAFFOLD_PACKAGES = [
    AEA_DIR / "protocols" / "scaffold",
    AEA_DIR / "connections" / "scaffold",
    AEA_DIR / "contracts" / "scaffold",
    AEA_DIR / "skills" / "scaffold",
]
PYCACHE = "__pycache__"
AEA_TEST_DIRNAME = "tests"
