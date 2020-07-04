The AEA weather skills demonstrate an interaction between two AEAs.

* The provider of weather data (the `weather_station`).
* The buyer of weather data (the `weather_client`).

## Discussion

The scope of the specific demo is to demonstrate how to create a simple AEA with the usage of the AEA framework and a database. The weather_station AEA
will read data from the database, that is populated with readings from a weather station, based on the requested dates and will deliver the data to the client upon payment.
This demo does not utilize a smart contract. As a result, we interact with a ledger only to complete a transaction.

You can use this AEA as an example of how to read data from a database and advertise these to possible clients.  

## Communication

This diagram shows the communication between the various entities as data is successfully sold by the weather station AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Weather_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Weather_AEA
        activate Blockchain
        
        Weather_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Weather_AEA: call_for_proposal
        Weather_AEA->>Client_AEA: propose
        Client_AEA->>Weather_AEA: accept
        Weather_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Weather_AEA: send_transaction_hash
        Weather_AEA->>Blockchain: check_transaction_status
        Weather_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Weather_AEA
        deactivate Blockchain
       
</div>

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch an OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions:

A demo to run the same scenario but with a true ledger transaction on Fetch.ai `testnet` or Ethereum `ropsten` network. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

### Create the weather station

First, fetch the AEA that will provide weather measurements:
``` bash
aea fetch fetchai/weather_station:0.6.0 --alias my_weather_station
cd my_weather_station
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the weather station from scratch:
``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/weather_station:0.5.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```

In `weather_station/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
and add 
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```

</p>
</details>


### Create the weather client

In another terminal, fetch the AEA that will query the weather station:
``` bash
aea fetch fetchai/weather_client:0.6.0 --alias my_weather_client
cd my_weather_client
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the weather client from scratch:
``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/oef:0.5.0
aea add connection fetchai/ledger:0.1.0
aea add skill fetchai/weather_client:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.5.0
```

In `my_weather_client/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
and add 
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.1.0
```

</p>
</details>


### Generate wealth for the weather client AEA

The weather client needs to have some wealth to purchase the weather station information.

First, create the private key for the weather client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your weather client based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

<details><summary>Alternatively, create wealth for other test networks.</summary>
<p>

<strong>Ledger Config:</strong>
<br>

In `my_weather_station/aea-config.yaml` and `my_weather_client/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

Alternatively, to connect to Cosmos:
``` yaml
ledger_apis:
  cosmos:
    address: https://rest-agent-land.prod.fetch-ai.com:443
```

<strong>Wealth:</strong>
<br>

To generate and add a private-public key pair for Ethereum use:
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

On the Ethereum `ropsten` network.
``` bash
aea generate-wealth ethereum
```

Alternatively, to generate and add a private-public key pair for Cosmos use:
``` bash
aea generate-key cosmos
aea add-key cosmos cosmos_private_key.txt
```

On the Cosmos `testnet` network.
``` bash
aea generate-wealth cosmos
```

</p>
</details>


### Update the skill configs

The default skill configs assume that the transaction is settled against the fetchai ledger.

<details><summary>Alternatively, configure skills for other test networks.</summary>
<p>

<strong>Weather station:</strong>
<br>
Ensure you are in the weather station project directory.

For ethereum, update the skill config of the weather station via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.weather_station.models.strategy.args.ledger_id cosmos
```

This updates the weather station skill config (`my_weather_station/vendor/fetchai/skills/weather_station/skill.yaml`).


<strong>Weather client:</strong>
<br>
Ensure you are in the weather client project directory.

For ethereum, update the skill config of the weather client via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.weather_client.models.strategy.args.ledger_id cosmos
```

This updates the weather client skill config (`my_weather_client/vendor/fetchai/skills/weather_client/skill.yaml`).

</p>
</details>

### Run the AEAs

Run both AEAs from their respective terminals.
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the selected ledger.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```


