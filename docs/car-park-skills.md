The AEA car-park skills demonstrate an interaction between two AEAs.

* The `carpark_detection` AEA provides information on the number of car parking spaces available in a given vicinity.
* The `carpark_client` AEA is interested in purchasing information on available car parking spaces in the same vicinity.

## Discussion

The full Fetch.ai car park AEA demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).
This demo allows you to test the AEA functionality of the car park AEA demo without the detection logic.

It demonstrates how the AEAs trade car park information.

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the car park AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Car_Data_Buyer_AEA
        participant Car_Park_AEA
        participant Blockchain
    
        activate Car_Data_Buyer_AEA
        activate Search
        activate Car_Park_AEA
        activate Blockchain
        
        Car_Park_AEA->>Search: register_service
        Car_Data_Buyer_AEA->>Search: search
        Search-->>Car_Data_Buyer_AEA: list_of_agents
        Car_Data_Buyer_AEA->>Car_Park_AEA: call_for_proposal
        Car_Park_AEA->>Car_Data_Buyer_AEA: propose
        Car_Data_Buyer_AEA->>Car_Park_AEA: accept
        Car_Park_AEA->>Car_Data_Buyer_AEA: match_accept
        Car_Data_Buyer_AEA->>Blockchain: transfer_funds
        Car_Data_Buyer_AEA->>Car_Park_AEA: send_transaction_hash
        Car_Park_AEA->>Blockchain: check_transaction_status
        Car_Park_AEA->>Car_Data_Buyer_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Car_Park_AEA
        deactivate Blockchain
</div>

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch the OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following.

## Demo instructions

### Create car detector AEA

First, fetch the car detector AEA:
``` bash
aea fetch fetchai/car_detector:0.5.0
cd car_detector
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car detector from scratch:
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/oef:0.4.0
aea add skill fetchai/carpark_detection:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.4.0
```

In `car_detector/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect. To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>

### Create car data buyer AEA

Then, fetch the car data client AEA:
``` bash
aea fetch fetchai/car_data_buyer:0.5.0
cd car_data_buyer
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car data client from scratch:
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/oef:0.4.0
aea add skill fetchai/carpark_client:0.4.0
aea install
aea config set agent.default_connection fetchai/oef:0.4.0
```

In `car_data_buyer/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

</p>
</details>

### Generate wealth for the car data buyer AEA

The car data buyer needs to have some wealth to purchase the car park information.

First, create the private key for the car data buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

Then, create some wealth for your car data buyer based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-wealth fetchai
```

<details><summary>Alternatively, create wealth for other test networks.</summary>
<p>

<strong>Ledger Config:</strong>
<br>

In `car_data_buyer/aea-config.yaml` and `car_detector/aea-config.yaml` replace `ledger_apis: {}` with the following based on the network you want to connect.

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
    address: http://aea-testnet.sandbox.fetch-ai.com:1317
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

<strong>Car detector:</strong>
<br>
Ensure you are in the car detector project directory.

For ethereum, update the skill config of the car detector via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.ledger_id cosmos
```

This updates the carpark detection skill config (`car_detector/vendor/fetchai/skills/carpark_detection/skill.yaml`).


<strong>Car data buyer:</strong>
<br>
Ensure you are in the car data buyer project directory.

For ethereum, update the skill config of the car detector via the `aea config get/set` command like so:
``` bash
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.max_buyer_tx_fee 6000 --type int
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.ledger_id ethereum
```

Or for cosmos, like so:
``` bash
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.max_buyer_tx_fee 6000 --type int
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.currency_id ATOM
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.ledger_id cosmos
```

This updates the car data buyer skill config (`car_data_buyer/vendor/fetchai/skills/carpark_client/skill.yaml`).

</p>
</details>

### Run both AEAs

Finally, run both AEAs from their respective directories:
``` bash
aea run --connections fetchai/oef:0.4.0
```

You can see that the AEAs find each other, negotiate and eventually trade.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
```

<br />
