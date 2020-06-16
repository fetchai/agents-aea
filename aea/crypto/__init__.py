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

from aea.crypto.registries import register_crypto, register_ledger_api  # noqa

register_crypto(id="fetchai", entry_point="aea.crypto.fetchai:FetchAICrypto")
register_crypto(id="ethereum", entry_point="aea.crypto.ethereum:EthereumCrypto")
register_crypto(id="cosmos", entry_point="aea.crypto.cosmos:CosmosCrypto")

register_ledger_api(
    id="fetchai", entry_point="aea.crypto.fetchai:FetchAIApi", network="testnet"
)
register_ledger_api(
    id="ethereum",
    entry_point="aea.crypto.ethereum:EthereumApi",
    address="https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
    gas_price=50,
)
register_ledger_api(
    id="cosmos",
    entry_point="aea.crypto.cosmos:CosmosApi",
    address="http://aea-testnet.sandbox.fetch-ai.com:1317",
)
