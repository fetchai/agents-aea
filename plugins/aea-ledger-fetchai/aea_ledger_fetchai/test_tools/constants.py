# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Constants."""


import os
from pathlib import Path

from aea_ledger_fetchai.fetchai import FetchAICrypto

from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.ledger_apis import FETCHAI_DEFAULT_ADDRESS


DATA_DIR = Path(__file__).parent / "data"

FETCHAI_TESTNET_CONFIG = {"address": FETCHAI_DEFAULT_ADDRESS}

FETCHAI_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier)
FETCHAI_PRIVATE_KEY_FILE_CONNECTION = "fetchai_connection_private_key.txt"

FETCHAI_ADDRESS_ONE = "fetch1paqxtqnfh7da7z9c05l3y3lahe8rhd0nm0jk98"
FETCHAI_ADDRESS_TWO = "fetch19j4dc3e6fgle98pj06l5ehhj6zdejcddx7teac"
FUNDED_FETCHAI_ADDRESS_ONE = "fetch1k9dns2fd74644g0q9mfpsmfeqg0h2ym2cm6wdh"
FUNDED_FETCHAI_ADDRESS_TWO = "fetch1x2vfp8ec2yk8nnlzn52agflpmpwtucm6yj2hw4"

NON_FUNDED_FETCHAI_PRIVATE_KEY_1 = (
    "b6ef49c3078f300efe2d4480e179362bd39f20cbb2087e970c8f345473661aa5"
)
FUNDED_FETCHAI_PRIVATE_KEY_1 = (
    "bbaef7511f275dc15f47436d14d6d3c92d4d01befea073d23d0c2750a46f6cb3"
)
FUNDED_FETCHAI_PRIVATE_KEY_2 = (
    "9d6459d1f93dd153335291af940f6b5224a34a9a1e1062e2158a45fa4901ed3f"
)

FETCHAI_P2P_ADDRESS = "/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAmLBCAqHL8SuFosyDhAKYsLKXBZBWXBsB9oFw2qU4Kckun"  # relates to NON_FUNDED_FETCHAI_PRIVATE_KEY_1

FETCHAI_PRIVATE_KEY_PATH = os.path.join(DATA_DIR, FETCHAI_PRIVATE_KEY_FILE)
