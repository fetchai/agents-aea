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

"""Module with constants of the aea cli."""

import os
from pathlib import Path
from typing import Dict

from aea.configurations.constants import (
    AGENT,
    CONNECTION,
    CONNECTIONS,
    CONTRACT,
    CONTRACTS,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PACKAGES,
    PROTOCOL,
    PROTOCOLS,
    SKILL,
    SKILLS,
    VENDOR,
)


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


FROM_STRING_TO_TYPE = dict(
    str=str, int=int, bool=bool, float=float, dict=dict, list=list, none=None,
)
CONFIG_SUPPORTED_KEY_TYPES = list(FROM_STRING_TO_TYPE.keys())
CONFIG_SUPPORTED_VALUE_TYPES = (str, int, bool, float, dict, list, type(None))

ALLOWED_PATH_ROOTS = [
    AGENT,
    CONNECTIONS,
    CONTRACTS,
    PROTOCOLS,
    SKILLS,
    VENDOR,
]
RESOURCE_TYPE_TO_CONFIG_FILE = {
    SKILLS: DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOLS: DEFAULT_PROTOCOL_CONFIG_FILE,
    CONNECTIONS: DEFAULT_CONNECTION_CONFIG_FILE,
    CONTRACTS: DEFAULT_CONTRACT_CONFIG_FILE,
}  # type: Dict[str, str]
FALSE_EQUIVALENTS = ["f", "false", "False"]

REQUIREMENTS = "requirements.txt"
