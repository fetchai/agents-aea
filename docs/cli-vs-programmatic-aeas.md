The AEA framework enables us to create agents either from the CLI tool or programmatically.

The following demo demonstrates an interaction between two AEAs.

The provider of weather data (managed with the CLI).
The buyer of weather data (managed programmatically).

## Discussion

The scope of the specific demo is to demonstrate how a CLI based AEA can interact with a programmatically managed AEA. In order 
to achieve this we are going to use the weather station skills. 
This demo does not utilize a smart contract or a ledger interaction. 

## Launch an OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for the entire demo.

## Demo instructions

If you want to create the weather station AEA step by step you can follow this guide <a href='/weather-skills/'>here</a>

### Create the weather station AEA

Fetch the weather station AEA with the following command :

``` bash
aea fetch fetchai/weather_station:0.6.0
cd weather_station
```

### Update the AEA configs

In the terminal change the configuration:
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx False --type bool
```
The `is_ledger_tx` will prevent the AEA to communicate with a ledger.

### Run the weather station AEA
``` bash
aea run
```

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
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE, create_private_key
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.connections.ledger.connection import LedgerConnection
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

    # Set up the wallet, identity and (empty) resources
    wallet = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE})
    identity = Identity(
        "my_aea", address=wallet.addresses.get(FetchAICrypto.identifier)
    )
    resources = Resources()

    # specify the default routing for some protocols
    default_routing = {
        PublicId.from_str("fetchai/ledger_api:0.1.0"): LedgerConnection.connection_id
    }
    default_connection = OEFConnection.connection_id

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

    # Add the OEF connection
    configuration = ConnectionConfig(
        addr=HOST, port=PORT, connection_id=OEFConnection.connection_id
    )
    oef_connection = OEFConnection(configuration=configuration, identity=identity)
    resources.add_connection(oef_connection)

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

For more details on how to create an agent programmatically follow this guide <a href='/build-aea-programmatically/'>here</a>

### Run the weather station AEA

In a new terminal window, navigate to the folder that you created the script and run:
``` bash
python weather_client.py
```

You should see both AEAs interacting now.
