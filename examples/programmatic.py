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

"""Example of programmatic initialization of an AEA using the builder."""

import logging

from aea.aea_builder import AEABuilder
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    builder = AEABuilder()

    builder.set_name("myagent")
    builder.set_default_ledger_api_config("ethereum")
    builder.add_private_key("fetchai", FetchAICrypto().address)
    builder.add_private_key("ethereum", EthereumCrypto().address)
    builder.add_protocol("./packages/fetchai/protocols/oef_search")
    builder.add_skill("./packages/fetchai/skills/echo")
    builder.add_contract("./packages/fetchai/contracts/erc1155")
    builder.add_ledger_api_config(
        "ethereum",
        {
            "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
            "chain_id": 3,
            "gas_price": 50,
        },
    )

    builder.add_skill("./packages/fetchai/skills/erc1155_deploy")

    # you can also use the fluent interface
    # builder.add_protocol(...).add_skill(...)

    aea_agent = builder.build()
    try:
        aea_agent.start()
    except KeyboardInterrupt:
        aea_agent.stop()
