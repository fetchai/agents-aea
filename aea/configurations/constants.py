# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
from typing import List


FETCHAI = "fetchai"
DEFAULT_CONNECTION = "fetchai/stub:latest"
DEFAULT_PROTOCOL = "fetchai/default:latest"
SIGNING_PROTOCOL = "fetchai/signing:latest"
STATE_UPDATE_PROTOCOL = "fetchai/state_update:latest"
DEFAULT_SKILL = "fetchai/error:latest"
LEDGER_CONNECTION = "fetchai/ledger:latest"
DEFAULT_LEDGER = FETCHAI
PRIVATE_KEY_PATH_SCHEMA = "{}_private_key.txt"
DEFAULT_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(DEFAULT_LEDGER)
DEFAULT_LICENSE = "Apache-2.0"
DISTRIBUTED_PACKAGES: List[str] = []
DEFAULT_SEARCH_SERVICE_ADDRESS = "fetchai/soef:any"
DEFAULT_INPUT_FILE_NAME = "./input_file"
DEFAULT_OUTPUT_FILE_NAME = "./output_file"
SCAFFOLD_PUBLIC_ID = "fetchai/scaffold:0.1.0"
PACKAGES = "packages"
DEFAULT_REGISTRY_NAME = PACKAGES
DEFAULT_REGISTRY_PATH = Path("./", DEFAULT_REGISTRY_NAME)
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
DEFAULT_README_FILE = "README.md"
DEFAULT_VERSION = "0.1.0"
DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
DEFAULT_CONNECTION_CONFIG_FILE = "connection.yaml"
DEFAULT_CONTRACT_CONFIG_FILE = "contract.yaml"
DEFAULT_PROTOCOL_CONFIG_FILE = "protocol.yaml"
DEFAULT_LICENSE = "Apache-2.0"
PACKAGE_PUBLIC_ID_VAR_NAME = "PUBLIC_ID"
DEFAULT_FINGERPRINT_IGNORE_PATTERNS = [
    ".DS_Store",
    "*__pycache__/*",
    "*__pycache__",
    "*.pyc",
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
]
DEFAULT_PYPI_INDEX_URL = "https://pypi.org/simple"
DEFAULT_GIT_REF = "master"
IMPORT_TEMPLATE_1 = "from packages.{author}.{type}.{name}"
IMPORT_TEMPLATE_2 = "import packages.{author}.{type}.{name}"
DEFAULT_ENV_DOTFILE = ".env"
DOTTED_PATH_MODULE_ELEMENT_SEPARATOR = ":"
LIBPROTOC_VERSION = "libprotoc 3.11.4"
