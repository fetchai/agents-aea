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

"""This scripts contains code from cli-vs-programmatic-aeas.md file."""

import logging
import os
import time
from threading import Thread
from typing import cast

from aea import AEA_DIR
from aea.aea import AEA
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE, _create_fetchai_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.base import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.oef.connection import OEFConnection
from packages.fetchai.skills.weather_client.strategy import Strategy

HOST = "127.0.0.1"
PORT = 10000
ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


def run():
    # Create a private key
    _create_fetchai_private_key()

    # Set up the wallet, identity, oef connection, ledger and (empty) resources
    wallet = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
    identity = Identity("my_aea", address=wallet.addresses.get(FETCHAI))
    oef_connection = OEFConnection(
        address=identity.address, oef_addr=HOST, oef_port=PORT
    )
    ledger_apis = LedgerApis({}, FETCHAI)
    resources = Resources()

    # create the AEA
    my_aea = AEA(
        identity, [oef_connection], wallet, ledger_apis, resources,  # stub_connection,
    )

    # Add the default protocol (which is part of the AEA distribution)
    default_protocol = Protocol.from_dir(os.path.join(AEA_DIR, "protocols", "default"))
    resources.add_protocol(default_protocol)

    # Add the oef protocol (which is a package)
    oef_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "oef_search",)
    )
    resources.add_protocol(oef_protocol)

    # Add the fipa protocol (which is a package)
    fipa_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "fipa",)
    )
    resources.add_protocol(fipa_protocol)

    # Add the error and weather_station skills
    error_skill = Skill.from_dir(
        os.path.join(AEA_DIR, "skills", "error"), my_aea.context
    )
    weather_skill = Skill.from_dir(
        os.path.join(ROOT_DIR, "packages", "fetchai", "skills", "weather_client"),
        my_aea.context,
    )

    strategy = cast(Strategy, weather_skill.models.get("strategy"))
    strategy.is_ledger_tx = False
    strategy.max_buyer_tx_fee = 100
    strategy.max_row_price = 40

    for skill in [error_skill, weather_skill]:
        resources.add_skill(skill)

    # Set the AEA running in a different thread
    try:
        logger.info("STARTING AEA NOW!")
        t = Thread(target=my_aea.start)
        t.start()

        # Let it run long enough to interact with the weather station
        time.sleep(25)
    finally:
        # Shut down the AEA
        logger.info("STOPPING AEA NOW!")
        my_aea.stop()
        t.join()


if __name__ == "__main__":
    run()
