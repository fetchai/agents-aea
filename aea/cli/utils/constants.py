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
"""Module with constants of the aea cli."""
import os
from pathlib import Path

from aea.cli.registry.settings import (
    REGISTRY_LOCAL,
    REGISTRY_REMOTE,
    REMOTE_HTTP,
    REMOTE_IPFS,
)
from aea.configurations.constants import (
    CONNECTION,
    CONNECTIONS,
    CONTRACT,
    CONTRACTS,
    PACKAGES,
    PROTOCOL,
    PROTOCOLS,
    SKILL,
    SKILLS,
    VENDOR,
)
from aea.configurations.data_types import PublicId
from aea.helpers.constants import FROM_STRING_TO_TYPE


AEA_DIR = str(Path("."))
ITEM_TYPES = (CONNECTION, CONTRACT, PROTOCOL, SKILL)
AEA_LOGO = "    _     _____     _    \r\n   / \\   | ____|   / \\   \r\n  / _ \\  |  _|    / _ \\  \r\n / ___ \\ | |___  / ___ \\ \r\n/_/   \\_\\|_____|/_/   \\_\\\r\n                         \r\n"
AUTHOR_KEY = "author"
CLI_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".aea", "cli_config.yaml")
NOT_PERMITTED_AUTHORS = [
    CONNECTIONS,
    CONTRACTS,
    PROTOCOLS,
    SKILLS,
    VENDOR,
    PACKAGES,
    "aea",
]
DEFAULT_CLI_CONFIG = {
    "author": "default_author",
    "registry_config": {
        "default": REGISTRY_LOCAL,
        "settings": {
            REGISTRY_REMOTE: {
                REMOTE_HTTP: {
                    "auth_token": None,  # auth token for registry
                    "registry_api_url": None,  # registry url
                },
                REMOTE_IPFS: {"ipfs_node": None},  # IPFS url (in multiaddr format)
            },
            REGISTRY_LOCAL: {"default_packages_path": None},
        },
    },
}

CONFIG_SUPPORTED_KEY_TYPES = list(FROM_STRING_TO_TYPE.keys())
REQUIREMENTS = "requirements.txt"
DUMMY_AUTHOR = "__DUMMY__AUTHOR__"
DUMMY_PACKAGE = "__DUMMY_PACKAGE__"
DUMMY_PACKAGE_ID = PublicId.from_json(
    {"author": DUMMY_AUTHOR, "name": DUMMY_PACKAGE, "version": "latest"}
)
