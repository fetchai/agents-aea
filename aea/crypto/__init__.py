# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

"""This module contains the crypto modules."""

from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.registries import register_crypto  # noqa
from aea.crypto.registries import register_faucet_api, register_ledger_api


register_crypto(
    id_=FetchAICrypto.identifier, entry_point="aea.crypto.fetchai:FetchAICrypto"
)
register_crypto(
    id_=EthereumCrypto.identifier, entry_point="aea.crypto.ethereum:EthereumCrypto"
)
register_crypto(
    id_=CosmosCrypto.identifier, entry_point="aea.crypto.cosmos:CosmosCrypto"
)

register_faucet_api(
    id_=FetchAICrypto.identifier, entry_point="aea.crypto.fetchai:FetchAIFaucetApi"
)
register_faucet_api(
    id_=EthereumCrypto.identifier, entry_point="aea.crypto.ethereum:EthereumFaucetApi"
)
register_faucet_api(
    id_=CosmosCrypto.identifier, entry_point="aea.crypto.cosmos:CosmosFaucetApi"
)

register_ledger_api(
    id_=FetchAICrypto.identifier, entry_point="aea.crypto.fetchai:FetchAIApi",
)
register_ledger_api(
    id_=EthereumCrypto.identifier, entry_point="aea.crypto.ethereum:EthereumApi"
)
register_ledger_api(
    id_=CosmosCrypto.identifier, entry_point="aea.crypto.cosmos:CosmosApi",
)
