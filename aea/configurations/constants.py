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

from aea.configurations.base import DEFAULT_LICENSE as DL
from aea.configurations.base import DEFAULT_REGISTRY_PATH as DRP
from aea.configurations.base import PublicId
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.helpers import COSMOS_PRIVATE_KEY_FILE

DEFAULT_CONNECTION = PublicId.from_str("fetchai/stub:0.6.0")
DEFAULT_PROTOCOL = PublicId.from_str("fetchai/default:0.3.0")
DEFAULT_SKILL = PublicId.from_str("fetchai/error:0.3.0")
DEFAULT_LEDGER = CosmosCrypto.identifier
DEFAULT_PRIVATE_KEY_FILE = COSMOS_PRIVATE_KEY_FILE
DEFAULT_REGISTRY_PATH = DRP
DEFAULT_LICENSE = DL
SIGNING_PROTOCOL = PublicId.from_str("fetchai/signing:0.1.0")
STATE_UPDATE_PROTOCOL = PublicId.from_str("fetchai/state_update:0.1.0")
LOCAL_PROTOCOLS = [DEFAULT_PROTOCOL, SIGNING_PROTOCOL, STATE_UPDATE_PROTOCOL]
