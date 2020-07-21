The AEA framework enables us to create agents either from the CLI tool or programmatically.

The following demo demonstrates an interaction between two AEAs.

The provider of weather data (managed with the CLI).
The buyer of weather data (managed programmatically).

## Discussion

The scope of the specific demo is to demonstrate how a CLI based AEA can interact with a programmatically managed AEA. In order 
to achieve this we are going to use the weather station skills. 
This demo does not utilize a smart contract or a ledger interaction. 

## Get required packages

Copy the packages directory into your local working directory:

``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
```

## Demo instructions

If you want to create the weather station AEA step by step you can follow this guide <a href='/weather-skills/'>here</a>

### Create the weather station AEA

Fetch the weather station AEA with the following command :

``` bash
aea fetch fetchai/weather_station:0.8.0
cd weather_station
```

### Update the AEA configs

In the terminal change the configuration:
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
The `is_ledger_tx` will prevent the AEA to communicate with a ledger.

### Add keys

Add keys for the weather station.
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
aea add-key cosmos cosmos_private_key.txt --connection
```

### Run the weather station AEA
``` bash
aea run
```

Once you see a message of the form `My libp2p addresses: ['SOME_ADDRESS']` take note of the address.

### Create the weather client AEA

Since we want to show the interaction between a programmatically created AEA with a CLI based AEA we are going to write some code for the client.

Create a new python file and name it `weather_client.py` and add the following code

<details><summary>Weather client full code.</summary>

``` python
import logging
import os
import sys
from typing import cast

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import ConnectionConfig, PublicId
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.helpers import COSMOS_PRIVATE_KEY_FILE, create_private_key
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.ledger.connection import LedgerConnection
from packages.fetchai.connections.p2p_libp2p.connection import P2PLibp2pConnection
from packages.fetchai.connections.soef.connection import SOEFConnection
from packages.fetchai.skills.weather_client.strategy import Strategy

API_KEY = "TwiCIriSl0mLahw17pyqoA"
SOEF_ADDR = "soef.fetch.ai"
SOEF_PORT = 9002
ENTRY_PEER_ADDRESS = (
    "/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAmAzvu5uNbcnD2qaqrkSULhJsc6GJUg3iikWerJkoD72pr"
)
ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def run():
    # Create a private key
    create_private_key(CosmosCrypto.identifier)

    # Set up the wallet, identity and (empty) resources
    wallet = Wallet(
        private_key_paths={CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE},
        connection_private_key_paths={CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE},
    )
    identity = Identity("my_aea", address=wallet.addresses.get(CosmosCrypto.identifier))
    resources = Resources()

    # specify the default routing for some protocols
    default_routing = {
        PublicId.from_str("fetchai/ledger_api:0.1.0"): LedgerConnection.connection_id,
        PublicId.from_str("fetchai/oef_search:0.3.0"): SOEFConnection.connection_id,
    }
    default_connection = SOEFConnection.connection_id

    # create the AEA
    my_aea = AEA(
        identity,
        wallet,
        resources,
        default_connection=default_connection,
        default_routing=default_routing,
    )

    # Add the default protocol (which is part of the AEA distribution)
    default_protocol = Protocol.from_dir(os.path.join(AEA_DIR, "protocols", "default"))
    resources.add_protocol(default_protocol)

    # Add the signing protocol (which is part of the AEA distribution)
    signing_protocol = Protocol.from_dir(os.path.join(AEA_DIR, "protocols", "signing"))
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
        configuration=configuration, identity=identity
    )
    resources.add_connection(ledger_api_connection)

    # Add the P2P connection
    configuration = ConnectionConfig(
        connection_id=P2PLibp2pConnection.connection_id,
        delegate_uri="127.0.0.1:11001",
        entry_peers=[ENTRY_PEER_ADDRESS],
        local_uri="127.0.0.1:9001",
        log_file="libp2p_node.log",
        public_uri="127.0.0.1:9001",
    )
    p2p_connection = P2PLibp2pConnection(
        configuration=configuration,
        identity=identity,
        crypto_store=wallet.connection_cryptos,
    )
    resources.add_connection(p2p_connection)

    # Add the SOEF connection
    configuration = ConnectionConfig(
        api_key=API_KEY,
        soef_addr=SOEF_ADDR,
        soef_port=SOEF_PORT,
        restricted_to_protocols={PublicId.from_str("fetchai/oef_search:0.3.0")},
        connection_id=SOEFConnection.connection_id,
        delegate_uri="127.0.0.1:11001",
        entry_peers=[ENTRY_PEER_ADDRESS],
        local_uri="127.0.0.1:9001",
        log_file="libp2p_node.log",
        public_uri="127.0.0.1:9001",
    )
    soef_connection = SOEFConnection(configuration=configuration, identity=identity)
    resources.add_connection(soef_connection)

    # Add the error and weather_client skills
    error_skill = Skill.from_dir(
        os.path.join(AEA_DIR, "skills", "error"), agent_context=my_aea.context
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
```
</details>

Now replace `ENTRY_PEER_ADDRESS` with the peer address (`SOME_ADDRESS`) noted above.

For more details on how to create an agent programmatically follow this guide <a href='/build-aea-programmatically/'>here</a>.

### Run the weather station AEA

In a new terminal window, navigate to the folder that you created the script and run:
``` bash
python weather_client.py
```

You should see both AEAs interacting now.
