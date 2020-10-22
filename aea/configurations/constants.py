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

from typing import List

from aea.configurations.base import DEFAULT_LICENSE as DL
from aea.configurations.base import DEFAULT_REGISTRY_PATH as DRP
from aea.configurations.base import PublicId
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import PRIVATE_KEY_PATH_SCHEMA


DEFAULT_CONNECTION = PublicId.from_str("fetchai/stub:0.12.0")
DEFAULT_PROTOCOL = PublicId.from_str("fetchai/default:0.8.0")
SIGNING_PROTOCOL = PublicId.from_str("fetchai/signing:0.6.0")
STATE_UPDATE_PROTOCOL = PublicId.from_str("fetchai/state_update:0.6.0")
LEDGER_CONNECTION = PublicId.from_str("fetchai/ledger:0.8.0")
DEFAULT_SKILL = PublicId.from_str("fetchai/error:0.8.0")
DEFAULT_LEDGER = FetchAICrypto.identifier
DEFAULT_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(DEFAULT_LEDGER)
DEFAULT_REGISTRY_PATH = DRP
DEFAULT_LICENSE = DL
DISTRIBUTED_PACKAGES = []  # type: List[PublicId]
DEFAULT_SEARCH_SERVICE_ADDRESS = "fetchai/soef:*"
DEFAULT_INPUT_FILE_NAME = "./input_file"
DEFAULT_OUTPUT_FILE_NAME = "./output_file"
