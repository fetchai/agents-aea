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
import sys
from typing import cast

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ConnectionConfig
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE, create_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill, SkillContext

from packages.fetchai.connections.oef.connection import OEFConnection
from packages.fetchai.skills.weather_client.strategy import Strategy

HOST = "127.0.0.1"
PORT = 10000
ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def run():
    # Create a private key
    create_private_key(FetchAICrypto.identifier)

    # Set up the wallet, identity, oef connection, ledger and (empty) resources
    wallet = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE})
    identity = Identity(
        "my_aea", address=wallet.addresses.get(FetchAICrypto.identifier)
    )
    configuration = ConnectionConfig(
        oef_addr=HOST, oef_port=PORT, connection_id=OEFConnection.connection_id
    )
    oef_connection = OEFConnection(configuration=configuration, identity=identity)
    ledger_apis = LedgerApis({}, FetchAICrypto.identifier)
    resources = Resources()

    # create the AEA
    my_aea = AEA(
        identity, [oef_connection], wallet, ledger_apis, resources,  # stub_connection,
    )

    # Add the default protocol (which is part of the AEA distribution)
    default_protocol = Protocol.from_dir(os.path.join(AEA_DIR, "protocols", "default"))
    resources.add_protocol(default_protocol)

    # Add the oef search protocol (which is a package)
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
    error_skill_context = SkillContext()
    error_skill_context.set_agent_context(my_aea.context)
    logger_name = "aea.packages.fetchai.skills.error"
    error_skill_context.logger = logging.getLogger(logger_name)
    error_skill = Skill.from_dir(
        os.path.join(AEA_DIR, "skills", "error"), skill_context=error_skill_context
    )
    weather_skill_context = SkillContext()
    weather_skill_context.set_agent_context(my_aea.context)
    logger_name = "aea.packages.fetchai.skills.error"
    weather_skill_context.logger = logging.getLogger(logger_name)
    weather_skill = Skill.from_dir(
        os.path.join(ROOT_DIR, "packages", "fetchai", "skills", "weather_client"),
        skill_context=weather_skill_context,
    )

    strategy = cast(Strategy, weather_skill.models.get("strategy"))
    strategy.is_ledger_tx = False

    for skill in [error_skill, weather_skill]:
        resources.add_skill(skill)

    try:
        logger.info("STARTING AEA NOW!")
        my_aea.start()
    except KeyboardInterrupt:
        logger.info("STOPPING AEA NOW!")
        my_aea.stop()


if __name__ == "__main__":
    run()
