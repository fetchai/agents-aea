# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
import inspect
import os

from aea_ledger_cosmos import CosmosCrypto


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
MAX_FLAKY_RERUNS = 3
COSMOS = CosmosCrypto.identifier

COSMOS_DEFAULT_ADDRESS = "INVALID_URL"
COSMOS_DEFAULT_CURRENCY_DENOM = "INVALID_CURRENCY_DENOM"
COSMOS_DEFAULT_CHAIN_ID = "INVALID_CHAIN_ID"
COSMOS_TESTNET_CONFIG = {"address": COSMOS_DEFAULT_ADDRESS}
