The AEA thermometer skills demonstrate an interaction between two AEAs.

* The provider of thermometer data (the `thermometer`).
* The buyer of thermometer data (the `thermometer_client`).

## Discussion

The scope of the specific demo is to demonstrate how to create a very simple AEA with the usage of the AEA framework, a Raspberry Pi, and a thermometer sensor. The thermometer AEA
will read data from the sensor each time a client requests and will deliver to the client upon payment. To keep the demo simple we avoided the usage of a database since this would increase the complexity. As a result, the AEA can provide only one reading from the sensor.
This demo does not utilise a smart contract. As a result, we interact with a ledger only to complete a transaction.

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 
The AEA must run inside a Raspberry Pi or any other Linux system, and the sensor must be connected to the USB port.

## Communication

This diagram shows the communication between the various entities as data is successfully sold by the thermometer AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Thermometer_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Thermometer_AEA
        activate Blockchain
        
        Thermometer_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Thermometer_AEA: call_for_proposal
        Thermometer_AEA->>Client_AEA: propose
        Client_AEA->>Thermometer_AEA: accept
        Thermometer_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Thermometer_AEA: send_transaction_hash
        Thermometer_AEA->>Blockchain: check_transaction_status
        Thermometer_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Thermometer_AEA
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

## Demo instructions

A demo to run the thermometer scenario with a true ledger transaction This demo assumes the buyer trusts the seller AEA to send the data upon successful payment.

### Create thermometer AEA

First, fetch the thermometer AEA:
``` bash
aea fetch fetchai/thermometer_aea:0.5.0 --alias my_thermometer_aea
cd thermometer_aea
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the thermometer AEA from scratch:
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/thermometer:0.6.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```

In `my_thermometer_aea/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
and add 
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```

</p>
</details>

### Create thermometer client

Then, fetch the thermometer client AEA:
``` bash
aea fetch fetchai/thermometer_client:0.5.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the thermometer client from scratch:
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.6.0
aea add connection fetchai/ledger:0.2.0
aea add skill fetchai/thermometer_client:0.5.0
aea install
aea config set agent.default_connection fetchai/oef:0.6.0
```

In `my_thermometer_aea/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```
and add 
``` yaml
default_routing:
  fetchai/ledger_api:0.1.0: fetchai/ledger:0.2.0
```

</p>
</details>

### Generate wealth for the thermometer client AEA

The thermometer client needs to have some wealth to purchase the thermometer information.

First, create the private key for the thermometer client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your thermometer client based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

<details><summary>Alternatively, create wealth for other test networks.</summary>
<p>

<strong>Ledger Config:</strong>
<br>

In `my_thermometer_aea/aea-config.yaml` and `my_thermometer_client/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

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

<strong>Thermometer:</strong>
<br>
Ensure you are in the thermometer project directory.

For ethereum, update the skill config of the thermometer via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id cosmos
```

This updates the thermometer skill config (`my_thermometer_aea/vendor/fetchai/skills/thermometer/skill.yaml`).


<strong>Thermometer client:</strong>
<br>
Ensure you are in the thermometer client project directory.

For ethereum, update the skill config of the thermometer via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id cosmos
```

This updates the thermometer client skill config (`my_thermometer_client/vendor/fetchai/skills/thermometer_client/skill.yaml`).

</p>
</details>

### Run both AEAs

Finally, run both AEAs from their respective directories:
``` bash
aea run
```

You can see that the AEAs find each other, negotiate and eventually trade.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```

<br />
