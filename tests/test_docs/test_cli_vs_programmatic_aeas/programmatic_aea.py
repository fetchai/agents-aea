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

from aea_ledger_fetchai import FetchAICrypto

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import ConnectionConfig
from aea.crypto.helpers import (
    PRIVATE_KEY_PATH_SCHEMA,
    create_private_key,
    make_certificate,
)
from aea.crypto.wallet import Wallet
from aea.helpers.base import CertRequest
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill

import packages.fetchai.connections.p2p_libp2p.connection
from packages.fetchai.connections.ledger.connection import LedgerConnection
from packages.fetchai.connections.p2p_libp2p.connection import P2PLibp2pConnection
from packages.fetchai.connections.soef.connection import SOEFConnection
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.weather_client.strategy import Strategy


API_KEY = "TwiCIriSl0mLahw17pyqoA"
SOEF_ADDR = "s-oef.fetch.ai"
SOEF_PORT = 443
ENTRY_PEER_ADDRESS = (
    "/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAmLBCAqHL8SuFosyDhAKYsLKXBZBWXBsB9oFw2qU4Kckun"
)
FETCHAI_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(FetchAICrypto.identifier)
FETCHAI_PRIVATE_KEY_FILE_CONNECTION = PRIVATE_KEY_PATH_SCHEMA.format(
    "fetchai_connection"
)
ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def run():
    """Run demo."""

    # Create a private key
    create_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
    create_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION)

    # Set up the wallet, identity and (empty) resources
    wallet = Wallet(
        private_key_paths={FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE},
        connection_private_key_paths={
            FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        },
    )
    identity = Identity(
        "my_aea",
        address=wallet.addresses.get(FetchAICrypto.identifier),
        public_key=wallet.public_keys.get(FetchAICrypto.identifier),
    )
    resources = Resources()
    data_dir = os.getcwd()

    # specify the default routing for some protocols
    default_routing = {
        LedgerApiMessage.protocol_id: LedgerConnection.connection_id,
        OefSearchMessage.protocol_id: SOEFConnection.connection_id,
    }
    default_connection = P2PLibp2pConnection.connection_id

    state_update_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "state_update")
    )
    resources.add_protocol(state_update_protocol)

    # Add the default protocol (which is part of the AEA distribution)
    default_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "default")
    )
    resources.add_protocol(default_protocol)

    # Add the signing protocol (which is part of the AEA distribution)
    signing_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "signing")
    )
    resources.add_protocol(signing_protocol)

    # Add the ledger_api protocol
    ledger_api_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "ledger_api",)
    )
    resources.add_protocol(ledger_api_protocol)

    # Add the oef_search protocol
    oef_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "oef_search",)
    )
    resources.add_protocol(oef_protocol)

    # Add the fipa protocol
    fipa_protocol = Protocol.from_dir(
        os.path.join(os.getcwd(), "packages", "fetchai", "protocols", "fipa",)
    )
    resources.add_protocol(fipa_protocol)

    # Add the LedgerAPI connection
    configuration = ConnectionConfig(connection_id=LedgerConnection.connection_id)
    ledger_api_connection = LedgerConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )
    resources.add_connection(ledger_api_connection)

    # Add the P2P connection
    cert_path = ".certs/conn_cert.txt"
    cert_request = CertRequest(
        identifier="acn",
        ledger_id=FetchAICrypto.identifier,
        not_after="2022-01-01",
        not_before="2021-01-01",
        public_key="fetchai",
        message_format="{public_key}",
        save_path=cert_path,
    )
    public_key = wallet.connection_cryptos.public_keys.get(FetchAICrypto.identifier)
    message = cert_request.get_message(public_key)
    make_certificate(
        FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE, message, cert_path
    )
    configuration = ConnectionConfig(
        connection_id=P2PLibp2pConnection.connection_id,
        delegate_uri="127.0.0.1:11001",
        entry_peers=[ENTRY_PEER_ADDRESS],
        local_uri="127.0.0.1:9001",
        log_file="libp2p_node.log",
        public_uri="127.0.0.1:9001",
        build_directory=os.getcwd(),
        build_entrypoint="check_dependencies.py",
        cert_requests=[cert_request],
    )
    configuration.directory = os.path.dirname(
        packages.fetchai.connections.p2p_libp2p.connection.__file__
    )

    AEABuilder.run_build_for_component_configuration(configuration)

    p2p_connection = P2PLibp2pConnection(
        configuration=configuration,
        data_dir=data_dir,
        identity=identity,
        crypto_store=wallet.connection_cryptos,
    )
    resources.add_connection(p2p_connection)

    # Add the SOEF connection
    configuration = ConnectionConfig(
        api_key=API_KEY,
        soef_addr=SOEF_ADDR,
        soef_port=SOEF_PORT,
        restricted_to_protocols={OefSearchMessage.protocol_id},
        connection_id=SOEFConnection.connection_id,
    )
    soef_connection = SOEFConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )
    resources.add_connection(soef_connection)

    # create the AEA
    my_aea = AEA(
        identity,
        wallet,
        resources,
        data_dir,
        default_connection=default_connection,
        default_routing=default_routing,
    )
    # Add the error and weather_client skills
    error_skill = Skill.from_dir(
        os.path.join(ROOT_DIR, "packages", "fetchai", "skills", "error"),
        agent_context=my_aea.context,
    )
    weather_skill = Skill.from_dir(
        os.path.join(ROOT_DIR, "packages", "fetchai", "skills", "weather_client"),
        agent_context=my_aea.context,
    )

    strategy = cast(Strategy, weather_skill.models.get("strategy"))
    strategy._is_ledger_tx = False

    for skill in [error_skill, weather_skill]:
        resources.add_skill(skill)

    # Run the AEA
    try:
        logger.info("STARTING AEA NOW!")
        my_aea.start()
    except KeyboardInterrupt:
        logger.info("STOPPING AEA NOW!")
        my_aea.stop()


if __name__ == "__main__":
    run()
