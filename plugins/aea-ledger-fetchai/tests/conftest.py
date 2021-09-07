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

"""Conftest module for Pytest."""
import inspect
import os

from aea_ledger_fetchai import FetchAICrypto


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
MAX_FLAKY_RERUNS = 3
FETCHAI = FetchAICrypto.identifier


FETCHAI_DEFAULT_ADDRESS = "https://rest-stargateworld.fetch.ai:443"
FETCHAI_DEFAULT_CURRENCY_DENOM = "atestfet"
FETCHAI_DEFAULT_CHAIN_ID = "stargateworld-1"
FETCHAI_TESTNET_CONFIG = {"address": FETCHAI_DEFAULT_ADDRESS}
